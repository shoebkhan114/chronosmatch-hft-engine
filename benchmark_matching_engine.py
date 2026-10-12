
from time import perf_counter

from src.matching_engine import MatchingEngine
from src.models import Order, Side


def run_benchmark(number_of_orders=10_000):
    engine = MatchingEngine()

    start = perf_counter()

    for i in range(number_of_orders):
        engine.add_order(
            Order(
                order_id=i + 1,
                timestamp_ns=i,
                side=Side.BUY,
                price_ticks=100,
                quantity=1,
            )
        )

    elapsed = perf_counter() - start

    print(f"Orders submitted: {number_of_orders}")
    print(f"Elapsed time: {elapsed:.6f} seconds")
    print(f"Throughput: {number_of_orders / elapsed:,.0f} orders/second")


if __name__ == "__main__":
    run_benchmark()
