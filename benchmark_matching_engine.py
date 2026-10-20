
from statistics import median
from time import perf_counter

from src.matching_engine import MatchingEngine
from src.models import Order, Side


def run_once(number_of_orders=10_000):
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

    assert len(engine.buy_orders) == number_of_orders
    assert len(engine.sell_orders) == 0
    assert len(engine.trades) == 0

    return elapsed


def run_benchmark(number_of_orders=10_000, trials=5):
    # Warm-up run, excluded from measurements.
    run_once(100)

    times = [
        run_once(number_of_orders)
        for _ in range(trials)
    ]

    median_time = median(times)
    throughput = number_of_orders / median_time

    print(f"Orders per run: {number_of_orders}")
    print(f"Trials: {trials}")
    print("Elapsed times:", [round(t, 6) for t in times])
    print(f"Median elapsed time: {median_time:.6f} seconds")
    print(f"Median throughput: {throughput:,.0f} orders/second")


if __name__ == "__main__":
    run_benchmark()

