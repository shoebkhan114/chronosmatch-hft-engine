
import asyncio

import pandas as pd
import pytest

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
    """Check zero delay and selected-stock filtering."""

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


def test_generate_random_orders_without_dataset():
    """Check random order generation without reading a CSV."""

    async def run_test():
        simulator = MarketSimulator(
            dataset_path="file_does_not_need_to_exist.csv"
        )

        orders = [
            order
            async for order in simulator.generate_random_orders(
                count=100
            )
        ]

        assert len(orders) == 100
        assert all(isinstance(order, Order) for order in orders)
        assert [order.order_id for order in orders] == list(
            range(1, 101)
        )
        assert all(order.price_ticks > 0 for order in orders)

        # The random mode must not load the dataset.
        assert simulator.market_data is None

    asyncio.run(run_test())


def test_generate_random_orders_rejects_invalid_count():
    """Check that an invalid order count raises ValueError."""

    async def run_test():
        simulator = MarketSimulator()

        with pytest.raises(
            ValueError, match="count must be at least 1"
        ):
            async for _ in simulator.generate_random_orders(count=0):
                pass

    asyncio.run(run_test())


def test_generate_random_orders_same_seed():
    """Same seed should produce identical random order data."""

    async def run_test():
        simulator = MarketSimulator()

        orders1 = [
            order
            async for order in simulator.generate_random_orders(
                count=100, seed=42
            )
        ]

        orders2 = [
            order
            async for order in simulator.generate_random_orders(
                count=100, seed=42
            )
        ]

        data1 = [(o.side, o.price_ticks, o.quantity) for o in orders1]
        data2 = [(o.side, o.price_ticks, o.quantity) for o in orders2]

        assert data1 == data2

    asyncio.run(run_test())


def test_generate_random_orders_different_seeds():
    """Different seeds should produce different random order data."""

    async def run_test():
        simulator = MarketSimulator()

        orders1 = [
            order
            async for order in simulator.generate_random_orders(
                count=100, seed=42
            )
        ]

        orders2 = [
            order
            async for order in simulator.generate_random_orders(
                count=100, seed=99
            )
        ]

        data1 = [(o.side, o.price_ticks, o.quantity) for o in orders1]
        data2 = [(o.side, o.price_ticks, o.quantity) for o in orders2]

        assert data1 != data2

    asyncio.run(run_test())


def test_generate_random_orders_yields_to_event_loop():
    """Other asynchronous tasks should run during order generation."""

    async def run_test():
        simulator = MarketSimulator()
        background_task_ran = False

        async def background_task():
            nonlocal background_task_ran
            background_task_ran = True

        task = asyncio.create_task(background_task())

        index = 0

        async for _ in simulator.generate_random_orders(count=2000):
            index += 1

            if index == 1001:
                assert background_task_ran

        await task
        assert background_task_ran

    asyncio.run(run_test())


@pytest.mark.parametrize("initial_price", [0, -100])
def test_generate_random_orders_rejects_invalid_initial_price(
    initial_price,
):
    async def run_test():
        simulator = MarketSimulator()

        with pytest.raises(
            ValueError, match="initial_price must be positive"
        ):
            async for _ in simulator.generate_random_orders(
                count=10,
                initial_price=initial_price,
            ):
                pass

    asyncio.run(run_test())


@pytest.mark.parametrize("delay", [-1, -0.01])
def test_generate_random_orders_rejects_negative_delay(delay):
    async def run_test():
        simulator = MarketSimulator()

        with pytest.raises(
            ValueError, match="delay cannot be negative"
        ):
            async for _ in simulator.generate_random_orders(
                count=10,
                delay=delay,
            ):
                pass

    asyncio.run(run_test())


def test_generate_orders_rejects_negative_delay():
    async def run_test():
        simulator = MarketSimulator()

        with pytest.raises(
            ValueError, match="delay cannot be negative"
        ):
            async for _ in simulator.generate_orders(delay=-1):
                pass

    asyncio.run(run_test())


@pytest.mark.parametrize(
    "column",
    ["Open", "High", "Low", "Close", "Volume"],
)
def test_load_data_removes_rows_with_missing_values(
    monkeypatch, column
):
    """Verify that rows with missing essential values are removed."""
    simulator = MarketSimulator(symbol="RELIANCE")
    sample_data = create_test_data()

    sample_data.loc[0, column] = float("nan")

    monkeypatch.setattr(
        pd, "read_csv", lambda _path: sample_data.copy()
    )

    data = simulator.load_data()

    assert len(data) == 1
    assert data[column].notna().all()
    assert set(data["Symbol"]) == {"RELIANCE"}


def test_load_data_rejects_unknown_symbol(monkeypatch):
    """Verify that an unknown stock symbol raises ValueError."""
    simulator = MarketSimulator(symbol="UNKNOWN")
    sample_data = create_test_data()

    monkeypatch.setattr(
        pd, "read_csv", lambda _path: sample_data.copy()
    )

    with pytest.raises(
        ValueError,
        match="No valid market data found for symbol: UNKNOWN",
    ):
        simulator.load_data()
