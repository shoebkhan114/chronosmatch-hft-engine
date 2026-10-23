
import os
import tempfile
import unittest
import multiprocessing
import time

from src.models import Order, Side
from src.ring_buffer import RingBuffer


def producer_process(path, capacity, lock, count):
    buffer = RingBuffer(path, capacity, lock=lock)
    try:
        for order_id in range(1, count + 1):
            order = Order(
                order_id=order_id,
                timestamp_ns=1000 + order_id,
                side=Side.BUY,
                price_ticks=25000,
                quantity=10,
            )

            deadline = time.monotonic() + 5
            while not buffer.put(order):
                if time.monotonic() >= deadline:
                    raise TimeoutError("Producer timed out")
                time.sleep(0.001)
    finally:
        buffer.close()


def consumer_process(path, capacity, lock, count, result_queue):
    buffer = RingBuffer(path, capacity, lock=lock)
    received = []

    try:
        deadline = time.monotonic() + 10

        while len(received) < count:
            order = buffer.get()

            if order is not None:
                received.append(order.order_id)
            elif time.monotonic() >= deadline:
                raise TimeoutError("Consumer timed out")
            else:
                time.sleep(0.001)

        result_queue.put(received)
    except Exception as exc:
        result_queue.put({"error": str(exc)})
        raise
    finally:
        buffer.close()

class TestRingBuffer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp_dir.name, "ring.bin")
        self.buffer = RingBuffer(self.path, capacity=2, create=True)

    def tearDown(self):
        self.buffer.close()
        self.temp_dir.cleanup()

    def make_order(self, order_id):
        return Order(
            order_id=order_id,
            timestamp_ns=1000 + order_id,
            side=Side.BUY,
            price_ticks=25000,
            quantity=10,
        )

    def test_empty_buffer(self):
        self.assertIsNone(self.buffer.get())

    def test_put_and_get(self):
        order = self.make_order(1)

        self.assertTrue(self.buffer.put(order))

        result = self.buffer.get()
        self.assertEqual(result.order_id, 1)
        self.assertEqual(result.price_ticks, 25000)
        self.assertEqual(result.quantity, 10)

    def test_full_buffer(self):
        self.assertTrue(self.buffer.put(self.make_order(1)))
        self.assertTrue(self.buffer.put(self.make_order(2)))
        self.assertFalse(self.buffer.put(self.make_order(3)))

    def test_fifo_order(self):
        self.buffer.put(self.make_order(1))
        self.buffer.put(self.make_order(2))

        self.assertEqual(self.buffer.get().order_id, 1)
        self.assertEqual(self.buffer.get().order_id, 2)

    def test_wraparound(self):
        self.buffer.put(self.make_order(1))
        self.buffer.put(self.make_order(2))
        self.buffer.get()

        self.assertTrue(self.buffer.put(self.make_order(3)))

        self.assertEqual(self.buffer.get().order_id, 2)
        self.assertEqual(self.buffer.get().order_id, 3)
        self.assertIsNone(self.buffer.get())

    def test_separate_process_communication(self):
        count = 100
        context = multiprocessing.get_context("spawn")
        lock = context.Lock()
        result_queue = context.Queue()

        producer = context.Process(
            target=producer_process,
            args=(self.path, self.buffer.capacity, lock, count),
        )
        consumer = context.Process(
            target=consumer_process,
            args=(
                self.path,
                self.buffer.capacity,
                lock,
                count,
                result_queue,
            ),
        )

        consumer.start()
        producer.start()

        producer.join(15)
        consumer.join(15)

        if producer.is_alive():
            producer.terminate()
            producer.join()
            self.fail("Producer process timed out")

        if consumer.is_alive():
            consumer.terminate()
            consumer.join()
            self.fail("Consumer process timed out")

        self.assertEqual(producer.exitcode, 0)
        self.assertEqual(consumer.exitcode, 0)

        received = result_queue.get(timeout=2)
        self.assertEqual(received, list(range(1, count + 1)))

        result_queue.close()


if __name__ == "__main__":
    unittest.main()
