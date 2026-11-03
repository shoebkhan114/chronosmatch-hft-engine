import platform
import sys
import time
import random

from src.matching_engine import MatchingEngine
from src.models import Order, Side, OrderType


def pct(sorted_values, p):
    return sorted_values[min(len(sorted_values) - 1, int(len(sorted_values) * p / 100))]


def build_pairs(pairs):
    orders = []
    oid = 1
    for _ in range(pairs):
        for side in (Side.SELL, Side.BUY):
            orders.append(Order(oid, oid, side, 25000, 10, OrderType.LIMIT))
            oid += 1
    return orders


def bench_immediate(pairs=10_000):
    orders = build_pairs(pairs)
    engine = MatchingEngine()
    start = time.perf_counter()
    for order in orders:
        engine.add_order(order)
    elapsed = time.perf_counter() - start
    assert len(engine.trades) == pairs
    assert not engine.buy_orders and not engine.sell_orders
    print(f"[1] Immediate trades: {len(orders)} orders, {len(engine.trades)} trades, "
          f"{len(orders) / elapsed:,.0f} orders/sec")


def bench_growing(sizes=(1_000, 2_000, 5_000, 10_000)):
    for n in sizes:
        rng = random.Random(42)
        orders = [
            Order(i + 1, i + 1, Side.BUY, rng.randint(24000, 25000), 10, OrderType.LIMIT)
            for i in range(n)
        ]
        engine = MatchingEngine()
        start = time.perf_counter()
        for order in orders:
            engine.add_order(order)
        elapsed = time.perf_counter() - start
        print(f"[2] Growing book (BUY only): {n:>6} orders, "
              f"{n / elapsed:,.0f} orders/sec, final book {len(engine.buy_orders)}")


def bench_latency(pairs=10_000):
    orders = build_pairs(pairs)
    engine = MatchingEngine()
    lat = []
    for order in orders:
        t0 = time.perf_counter_ns()
        engine.add_order(order)
        lat.append(time.perf_counter_ns() - t0)
    lat.sort()
    print("[3] add_order latency, immediate-trade workload (ns -> us):")
    for label, p in (("median", 50), ("p90", 90), ("p99", 99), ("p99.9", 99.9)):
        print(f"    {label:>6}: {pct(lat, p) / 1000:.2f} us")
    print(f"       max: {lat[-1] / 1000:.2f} us")


def main():
    print(f"Python {sys.version.split()[0]} | {platform.platform()} | {platform.processor()}")
    print("Single-process, in-memory MatchingEngine only (no ring buffer).\n")
    bench_immediate()
    bench_growing()
    bench_latency()


if __name__ == "__main__":
    main()
