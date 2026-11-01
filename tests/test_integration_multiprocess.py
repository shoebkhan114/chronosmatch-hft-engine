import multiprocessing
import os
import tempfile
import time

from src.matching_engine import MatchingEngine
from src.models import Order, Side, OrderType
from src.ring_buffer import RingBuffer

PAIRS = 10
PRICE = 25000
QTY = 5


def producer_process(path, capacity, lock):
    buffer = RingBuffer(path, capacity, lock=lock)
    try:
        orders = []
        for i in range(PAIRS):
            orders.append(Order(i + 1, 1000 + i, Side.SELL, PRICE, QTY, OrderType.LIMIT))
        for i in range(PAIRS):
            orders.append(Order(PAIRS + i + 1, 2000 + i, Side.BUY, PRICE, QTY, OrderType.LIMIT))

        for order in orders:
            deadline = time.monotonic() + 5
            while not buffer.put(order):
                if time.monotonic() >= deadline:
                    raise TimeoutError("Producer timed out")
                time.sleep(0.001)
    finally:
        buffer.close()


def consumer_process(path, capacity, lock, result_queue):
    buffer = RingBuffer(path, capacity, lock=lock)
    engine = MatchingEngine()
    trades = []
    received = 0
    try:
        deadline = time.monotonic() + 10
        while received < 2 * PAIRS:
            order = buffer.get()
            if order is not None:
                received += 1
                for t in engine.add_order(order):
                    trades.append(
                        (t.buy_order_id, t.sell_order_id, t.price_ticks, t.quantity)
                    )
            elif time.monotonic() >= deadline:
                raise TimeoutError("Consumer timed out")
            else:
                time.sleep(0.001)

        result_queue.put(
            {
                "trades": trades,
                "buy_left": len(engine.buy_orders),
                "sell_left": len(engine.sell_orders),
            }
        )
    except Exception as exc:
        result_queue.put({"error": str(exc)})
        raise
    finally:
        buffer.close()


def stress_producer(path, capacity, lock, order_count, result_queue):
    buffer = RingBuffer(path, capacity, lock=lock)
    full_retries = 0

    try:
        for i in range(order_count):
            order = Order(
                i + 1,
                time.perf_counter_ns(),
                Side.BUY,
                PRICE,
                QTY,
                OrderType.LIMIT,
            )

            while not buffer.put(order):
                full_retries += 1
                time.sleep(0)

        result_queue.put({"full_retries": full_retries})

    finally:
        buffer.close()


def stress_consumer(path, capacity, lock, order_count, result_queue):
    buffer = RingBuffer(path, capacity, lock=lock)
    received = 0
    last_order_id = 0

    try:
        deadline = time.monotonic() + 300

        while received < order_count:
            order = buffer.get()

            if order is None:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Consumer timed out")
                time.sleep(0)
                continue

            if order.order_id != last_order_id + 1:
                raise AssertionError(
                    f"Expected order {last_order_id + 1}, "
                    f"received {order.order_id}"
                )

            last_order_id = order.order_id
            received += 1

        result_queue.put({"received": received})

    except Exception as exc:
        result_queue.put({"error": repr(exc)})
        raise

    finally:
        buffer.close()



def test_multiprocess_producer_consumer_to_engine():
    context = multiprocessing.get_context("spawn")
    lock = context.Lock()
    result_queue = context.Queue()
    capacity = 8  # smaller than 20 orders, so wrap-around is exercised

    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "ring.bin")
        creator = RingBuffer(path, capacity, create=True, lock=lock)

        producer = context.Process(
            target=producer_process, args=(path, capacity, lock)
        )
        consumer = context.Process(
            target=consumer_process, args=(path, capacity, lock, result_queue)
        )

        try:
            consumer.start()
            producer.start()
            producer.join(15)
            consumer.join(15)

            for p in (producer, consumer):
                if p.is_alive():
                    p.terminate()
                    p.join()
                    raise AssertionError("Process timed out")

            assert producer.exitcode == 0
            assert consumer.exitcode == 0

            result = result_queue.get(timeout=2)
            assert "error" not in result, result
            assert len(result["trades"]) == PAIRS
            for buy_id, sell_id, price, qty in result["trades"]:
                assert price == PRICE
                assert qty == QTY
                assert 1 <= sell_id <= PAIRS
                assert PAIRS + 1 <= buy_id <= 2 * PAIRS
            assert result["buy_left"] == 0
            assert result["sell_left"] == 0
        finally:
            creator.close()



def test_multiprocess_one_million_orders_full_buffer_wraparound():
    context = multiprocessing.get_context("spawn")
    lock = context.Lock()

    producer_queue = context.Queue()
    consumer_queue = context.Queue()

    order_count = 1_000_000
    capacity = 1024

    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "stress_ring.bin")
        creator = RingBuffer(path, capacity, create=True, lock=lock)

        producer = context.Process(
            target=stress_producer,
            args=(path, capacity, lock, order_count, producer_queue),
        )
        consumer = context.Process(
            target=stress_consumer,
            args=(path, capacity, lock, order_count, consumer_queue),
        )

        try:
            consumer.start()
            producer.start()

            producer.join(300)
            consumer.join(300)

            for process in (producer, consumer):
                if process.is_alive():
                    process.terminate()
                    process.join()
                    raise AssertionError("Stress test process timed out")

            assert producer.exitcode == 0
            assert consumer.exitcode == 0

            producer_result = producer_queue.get(timeout=5)
            consumer_result = consumer_queue.get(timeout=5)

            assert "error" not in consumer_result, consumer_result
            assert consumer_result["received"] == order_count
            assert producer_result["full_retries"] > 0
            assert order_count // capacity >= 900

        finally:
            for process in (producer, consumer):
                if process.is_alive():
                    process.terminate()
                    process.join()

            creator.close()
            producer_queue.close()
            consumer_queue.close()
            producer_queue.join_thread()
            consumer_queue.join_thread()
