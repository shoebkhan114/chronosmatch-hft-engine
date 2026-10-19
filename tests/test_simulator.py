
import asyncio

import pandas as pd

from src.models import Order, OrderType, Side
from src.simulator import MarketSimulator, TICK_SIZE_INR


def create_test_data():
    """Create sample stock data without requiring the original CSV."""
    return pd.DataFrame(
        [
            {
                "Date": "2024-01-01",
                "Symbol": "RELIANCE",
                "Open": 100.0,
                "High": 105.0,
                "Low": 99.0,
                "Close": 102.0,
                "Volume": 1000,
            },
            {
                "Date": "2024-01-02",
                "Symbol": "RELIANCE",
                "Open": 102.0,
                "High": 108.0,
                "Low": 101.0,
                "Close": 106.0,
                "Volume": 1200,
            },
            {
                "Date": "2024-01-03",
                "Symbol": "TCS",
                "Open": 200.0,
                "High": 205.0,
                "Low": 198.0,
                "Close": 203.0,
                "Volume": 800,
            },
        ]
    )


def test_load_data(monkeypatch):
    """Check that only the selected stock is loaded."""
    simulator = MarketSimulator(symbol="RELIANCE")
    sample_data = create_test_data()

    def fake_read_csv(_path):
        return sample_data.copy()

    monkeypatch.setattr(pd, "read_csv", fake_read_csv)

    data = simulator.load_data()

    assert not data.empty
    assert set(data["Symbol"]) == {"RELIANCE"}
    assert len(data) == 2
    assert "Close" in data.columns


def test_generate_order():
    """Check that the simulator generates a valid Order object."""
    simulator = MarketSimulator()
    row = create_test_data().iloc[0]

    order = simulator.generate_order(row, 1)

    assert isinstance(order, Order)
    assert order.order_id == 1
    assert order.side in (Side.BUY, Side.SELL)
    assert order.price_ticks > 0
    assert isinstance(order.price_ticks, int)
    assert 1 <= order.quantity <= 100
    assert order.order_type == OrderType.LIMIT
    assert order.timestamp_ns > 0

    order.validate()


def test_price_tick_conversion():
    """Check price conversion using the specified tick size."""
    simulator = MarketSimulator()
    row = create_test_data().iloc[0]

    order = simulator.generate_order(row, 1)

    expected_buy_ticks = round(
        (102.0 * 1.001) / TICK_SIZE_INR
    )
    expected_sell_ticks = round(
        (102.0 * 0.999) / TICK_SIZE_INR
    )

    assert order.price_ticks in (
        expected_buy_ticks,
        expected_sell_ticks,
    )


def test_generate_orders_without_delay():
    """Check that zero delay works and only the selected stock is used."""

    async def run_test():
        simulator = MarketSimulator(symbol="RELIANCE")

        sample_data = create_test_data()
        simulator.market_data = sample_data[
            sample_data["Symbol"] == simulator.symbol
        ].copy()

        orders = [
            order
            async for order in simulator.generate_orders(delay=0)
        ]

        assert len(orders) == 2
        assert all(isinstance(order, Order) for order in orders)
        assert [order.order_id for order in orders] == [1, 2]

    asyncio.run(run_test())
