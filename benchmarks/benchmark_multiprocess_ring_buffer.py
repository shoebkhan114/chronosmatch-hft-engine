
import multiprocessing
import os
import tempfile
import time

from src.models import Order, Side, OrderType
from src.ring_buffer import RingBuffer


ORDER_COUNT = 100_000
CAPACITY = 1024
PROCESS_TIMEOUT = 120


def producer_process(path, capacity, lock, order_count):
    buffer = RingBuffer(path, capacity, lock=lock)

    try:
        for i in range(order_count):
            order = Order(
                order_id=i + 1,
                timestamp_ns=time.perf_counter_ns(),
                side=Side.BUY,
                price_ticks=25000,
                quantity=10,
                order_type=OrderType.LIMIT,
            )

            while not buffer.put(order):
                time.sleep(0)
    finally:
        buffer.close()


def consumer_process(path, capacity, lock, order_count, result_queue):
    buffer = RingBuffer(path, capacity, lock=lock)
    received = 0
    last_order_id = 0

    try:
        while received < order_count:
            order = buffer.get()

            if order is None:
                time.sleep(0)
                continue

            if order.order_id != last_order_id + 1:
                raise RuntimeError(
                    f"Unexpected order ID: {order.order_id}"
                )

            last_order_id = order.order_id
            received += 1

        result_queue.put({"received": received})
    except Exception as exc:
        result_queue.put({"error": repr(exc)})
        raise
    finally:
        buffer.close()


def main():
    context = multiprocessing.get_context("spawn")
    lock = context.Lock()
    result_queue = context.Queue()

    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "benchmark.bin")
        creator = RingBuffer(path, CAPACITY, create=True, lock=lock)

        producer = context.Process(
            target=producer_process,
            args=(path, CAPACITY, lock, ORDER_COUNT),
        )
        consumer = context.Process(
            target=consumer_process,
            args=(path, CAPACITY, lock, ORDER_COUNT, result_queue),
        )

        start = None

        try:
            consumer.start()
            producer.start()
            start = time.perf_counter()

            producer.join(PROCESS_TIMEOUT)
            consumer.join(PROCESS_TIMEOUT)

            for process in (producer, consumer):
                if process.is_alive():
                    process.terminate()
                    process.join()
                    raise TimeoutError("Benchmark process timed out")

            elapsed = time.perf_counter() - start

            if producer.exitcode != 0:
                raise RuntimeError(
                    f"Producer failed with exit code {producer.exitcode}"
                )

            if consumer.exitcode != 0:
                raise RuntimeError(
                    f"Consumer failed with exit code {consumer.exitcode}"
                )

            result = result_queue.get(timeout=5)

            if "error" in result:
                raise RuntimeError(result["error"])

            received = result["received"]
            if received != ORDER_COUNT:
                raise RuntimeError(
                    f"Expected {ORDER_COUNT} orders, received {received}"
                )

            throughput = received / elapsed if elapsed > 0 else 0

            print(f"Orders sent: {ORDER_COUNT}")
            print(f"Orders received: {received}")
            print(f"Elapsed time: {elapsed:.6f} seconds")
            print(f"Throughput: {throughput:.2f} orders/second")
            print("Benchmark type: Cross-process producer/consumer")

        finally:
            for process in (producer, consumer):
                if process.is_alive():
                    process.terminate()
                    process.join()

            creator.close()
            result_queue.close()
            result_queue.join_thread()


if __name__ == "__main__":
    main()
