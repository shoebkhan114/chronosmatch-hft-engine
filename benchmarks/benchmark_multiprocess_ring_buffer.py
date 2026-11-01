import multiprocessing
import os
import tempfile
import time

from src.models import Order, Side, OrderType
from src.ring_buffer import RingBuffer


ORDER_COUNT = 1_000_000
CAPACITY = 1024
PROCESS_TIMEOUT = 300


def producer_process(path, capacity, lock, order_count, result_queue):
    buffer = RingBuffer(path, capacity, lock=lock)
    full_retries = 0

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
                full_retries += 1
                time.sleep(0)

        result_queue.put({"full_retries": full_retries})

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
        result_queue.put({"consumer_error": repr(exc)})
        raise

    finally:
        buffer.close()


def main():
    context = multiprocessing.get_context("spawn")
    lock = context.Lock()
    producer_queue = context.Queue()
    consumer_queue = context.Queue()

    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "benchmark.bin")
        creator = RingBuffer(path, CAPACITY, create=True, lock=lock)

        producer = context.Process(
            target=producer_process,
            args=(path, CAPACITY, lock, ORDER_COUNT, producer_queue),
        )

        consumer = context.Process(
            target=consumer_process,
            args=(path, CAPACITY, lock, ORDER_COUNT, consumer_queue),
        )

        try:
            start = time.perf_counter()

            consumer.start()
            producer.start()

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

            producer_result = producer_queue.get(timeout=5)
            consumer_result = consumer_queue.get(timeout=5)

            if "consumer_error" in consumer_result:
                raise RuntimeError(consumer_result["consumer_error"])

            received = consumer_result["received"]
            full_retries = producer_result["full_retries"]

            if received != ORDER_COUNT:
                raise RuntimeError(
                    f"Expected {ORDER_COUNT} orders, received {received}"
                )

            if full_retries == 0:
                raise RuntimeError("Buffer-full condition was not observed")

            wraparounds = ORDER_COUNT // CAPACITY

            throughput = received / elapsed if elapsed > 0 else 0

            print(f"Orders sent: {ORDER_COUNT}")
            print(f"Orders received: {received}")
            print(f"Full-buffer retries: {full_retries}")
            print(f"Capacity: {CAPACITY}")
            print(f"Write-position wraparounds: at least {wraparounds}")
            print(f"Elapsed time: {elapsed:.6f} seconds")
            print(f"Throughput: {throughput:.2f} orders/second")
            print("Benchmark type: 1M cross-process producer/consumer")

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


if __name__ == "__main__":
    main()
