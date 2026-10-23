
import os
import tempfile
import time

from src.models import Order, Side
from src.ring_buffer import RingBuffer


def main():
    order_count = 100_000
    capacity = 1024

    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "benchmark.bin")
        buffer = RingBuffer(path, capacity=capacity, create=True)

        processed = 0
        start = time.perf_counter()

        try:
            while processed < order_count:
                order = Order(
                    order_id=processed + 1,
                    timestamp_ns=time.perf_counter_ns(),
                    side=Side.BUY,
                    price_ticks=25000,
                    quantity=10,
                )

                if buffer.put(order):
                    received = buffer.get()
                    if received is not None:
                        processed += 1
        finally:
            elapsed = time.perf_counter() - start
            buffer.close()

        throughput = processed / elapsed if elapsed > 0 else 0

        print(f"Orders processed: {processed}")
        print(f"Elapsed time: {elapsed:.6f} seconds")
        print(f"Throughput: {throughput:.2f} orders/second")
        print("Benchmark type: Single-process ring buffer put/get")


if __name__ == "__main__":
    main()
