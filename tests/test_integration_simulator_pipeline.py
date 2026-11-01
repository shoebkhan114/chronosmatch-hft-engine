import asyncio
import os
import random
import tempfile

import pandas as pd

from src.matching_engine import MatchingEngine
from src.ring_buffer import RingBuffer
from src.simulator import MarketSimulator


def make_sample_data(rows=40):
    return pd.DataFrame(
        {
            "Date": pd.date_range("2024-01-01", periods=rows),
            "Symbol": ["RELIANCE"] * rows,
            "Open": [100.0] * rows,
            "High": [105.0] * rows,
            "Low": [99.0] * rows,
            "Close": [100.0] * rows,
            "Volume": [1000] * rows,
        }
    )


def generate_orders(seed=12345):
    random.seed(seed)
    sim = MarketSimulator(symbol="RELIANCE")
    sim.market_data = make_sample_data()

    async def collect():
        return [o async for o in sim.generate_orders(delay=0)]

    return asyncio.run(collect())


def trade_tuples(trades):
    return [
        (t.buy_order_id, t.sell_order_id, t.price_ticks, t.quantity)
        for t in trades
    ]


def test_simulator_to_ring_buffer_to_engine_matches_direct_engine():
    # Reference: same orders straight into a fresh engine (no ring buffer).
    reference_orders = generate_orders()
    ref_engine = MatchingEngine()
    ref_trades = []
    for order in reference_orders:
        ref_trades.extend(ref_engine.add_order(order))

    # Pipeline: regenerate identical orders (same seed), go through ring buffer.
    pipeline_orders = generate_orders()
    fd, path = tempfile.mkstemp(suffix=".rb")
    os.close(fd)
    rb = RingBuffer(path, 64, create=True)
    try:
        for order in pipeline_orders:
            assert rb.put(order) is True

        engine = MatchingEngine()
        trades = []
        received = 0
        while (order := rb.get()) is not None:
            received += 1
            trades.extend(engine.add_order(order))
    finally:
        rb.close()
        os.remove(path)

    assert received == len(pipeline_orders) == 40
    assert len(trades) > 0  # BUY and SELL both occur, prices cross
    assert trade_tuples(trades) == trade_tuples(ref_trades)
