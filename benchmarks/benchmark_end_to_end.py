import multiprocessing
import os
import platform
import random
import sys
import tempfile
import time

from src.matching_engine import MatchingEngine
from src.models import Order, Side, OrderType
from src.ring_buffer import RingBuffer


ORDER_COUNT = 100_000
CAPACITY = 1024
PROCESS_TIMEOUT = 180
SEED = 42


def pct(sorted_values, p):
    return sorted_values[
        min(len(sorted_values) - 1, int(len(sorted_values) * p / 100))
    ]


def build_specs(count):
    rng = random.Random(SEED)
    mid = 25000
    specs = []
    for _ in range(count):
        mid += rng.choice((-1, 0, 1))
        side = Side.BUY if rng.random() < 0.5 else Side.SELL
        price = max(1, mid + rng.randint(-3, 3))
        specs.append((side, price, rng.randint(1, 100)))
    return specs


def summarize(values_ns):
    values = sorted(values_ns)
    return {
        "median_us": pct(values, 50) / 1000,
        "p99_us": pct(values, 99) / 1000,
        "p999_us": pct(values, 99.9) / 1000,
        "max_us": values[-1] / 1000,
        "min_us": values[0] / 1000,
    }


def producer_process(path, capacity, lock, order_count):
    specs = build_specs(order_count)
    buffer = RingBuffer(path, capacity, lock=lock)
    try:
        for i, (side, price, qty) in enumerate(specs, start=1):
            order = Order(
                i, time.perf_counter_ns(), side, price, qty, OrderType.LIMIT
            )
            while not buffer.put(order):
                time.sleep(0)
    finally:
        buffer.close()


def consumer_process(path, capacity, lock, order_count, result_queue):
    buffer = RingBuffer(path, capacity, lock=lock)
    import gc
    if os.environ.get("BENCH_GC", "on") == "off":
        gc.disable()
    engine = MatchingEngine()
    end_to_end = []
    engine_only = []
    get_only = []
    received = 0
    last_id = 0
    t_first = None
    t1 = None
    try:
        while received < order_count:
            tg0 = time.perf_counter_ns()
            order = buffer.get()
            if order is None:
                time.sleep(0)
                continue
            if order.order_id != last_id + 1:
                raise RuntimeError(f"Unexpected order ID: {order.order_id}")
            last_id = order.order_id

            t0 = time.perf_counter_ns()
            get_only.append(t0 - tg0)
            if t_first is None:
                t_first = t0
            engine.add_order(order)
            t1 = time.perf_counter_ns()

            end_to_end.append(t1 - order.timestamp_ns)
            engine_only.append(t1 - t0)
            received += 1

        result_queue.put(
            {
                "received": received,
                "trades": len(engine.trades),
                "window_s": (t1 - t_first) / 1e9,
                "end_to_end": summarize(end_to_end),
                "engine_only": summarize(engine_only),
                "get_only": summarize(get_only),
            }
        )
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
        path = os.path.join(directory, "e2e.bin")
        creator = RingBuffer(path, CAPACITY, create=True, lock=lock)
        producer = context.Process(
            target=producer_process,
            args=(path, CAPACITY, lock, ORDER_COUNT),
        )
        consumer = context.Process(
            target=consumer_process,
            args=(path, CAPACITY, lock, ORDER_COUNT, result_queue),
        )
        try:
            consumer.start()
            producer.start()
            result = result_queue.get(timeout=PROCESS_TIMEOUT)
            producer.join(PROCESS_TIMEOUT)
            consumer.join(PROCESS_TIMEOUT)

            if "error" in result:
                raise RuntimeError(result["error"])
            if producer.exitcode != 0 or consumer.exitcode != 0:
                raise RuntimeError("A benchmark process failed")
            if result["received"] != ORDER_COUNT:
                raise RuntimeError(f"Received {result['received']}")

            thr = result["received"] / result["window_s"]
            print(f"Python {sys.version.split()[0]} | {platform.machine()} | {platform.platform()}")
            print(f"Orders: {ORDER_COUNT} | Trades: {result['trades']} | Capacity: {CAPACITY} | Seed: {SEED}")
            print(f"Consumer-window throughput: {thr:.2f} orders/second")
            for name in ("end_to_end", "engine_only", "get_only"):
                s = result[name]
                print(
                    f"{name}: min {s['min_us']:.2f} us | median {s['median_us']:.2f} us | "
                    f"p99 {s['p99_us']:.2f} us | p99.9 {s['p999_us']:.2f} us | max {s['max_us']:.2f} us"
                )
            print("Benchmark type: end-to-end producer -> ring buffer -> engine (2 processes, single run)")
            print(f"GC in consumer: {os.environ.get('BENCH_GC', 'on')}")
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
