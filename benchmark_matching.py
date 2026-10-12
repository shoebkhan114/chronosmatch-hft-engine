
from time import perf_counter

from src.matching_engine import MatchingEngine
from src.models import Order, Side


def run_benchmark(number_of_trades=10_000):
    engine = MatchingEngine()
    start = perf_counter()

    for i in range(number_of_trades):
        engine.add_order(
            Order(
                order_id=2 * i + 1,
                timestamp_ns=2 * i,
                side=Side.SELL,
                price_ticks=100,
                quantity=1,
            )
        )

        engine.add_order(
            Order(
                order_id=2 * i + 2,
                timestamp_ns=2 * i + 1,
                side=Side.BUY,
                price_ticks=100,
                quantity=1,
            )
        )

    elapsed = perf_counter() - start

    print(f"Completed trades: {len(engine.trades)}")
    print(f"Elapsed time: {elapsed:.6f} seconds")
    print(f"Order submissions: {2 * number_of_trades}")
    print(f"Throughput: {2 * number_of_trades / elapsed:,.0f} orders/second")


if __name__ == "__main__":
    run_benchmark()
