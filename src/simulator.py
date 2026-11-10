
import asyncio
import pandas as pd
import random
import time

from src.models import Order, Side, OrderType

TICK_SIZE_INR = 0.01


class MarketSimulator:
    def __init__(self, dataset_path="data/NIFTY50_all.csv", symbol="RELIANCE"):
        self.dataset_path = dataset_path
        self.symbol = symbol
        self.market_data = None

    def load_data(self):
        self.market_data = pd.read_csv(self.dataset_path)

        self.market_data["Date"] = pd.to_datetime(
            self.market_data["Date"]
        )

        self.market_data = self.market_data[
            self.market_data["Symbol"] == self.symbol
        ]

        self.market_data = self.market_data.dropna(
            subset=["Date", "Open", "High", "Low", "Close", "Volume"]
        )

        if self.market_data.empty:
            raise ValueError(
                f"No valid market data found for symbol: {self.symbol}"
            )

        return self.market_data

    def generate_order(self, row, order_id):
        """Generate an order using a historical dataset row."""
        side = random.choice([Side.BUY, Side.SELL])

        if side == Side.BUY:
            price = float(row["Close"]) * 1.001
        else:
            price = float(row["Close"]) * 0.999

        price_ticks = round(price / TICK_SIZE_INR)

        order = Order(
            order_id=order_id,
            timestamp_ns=time.time_ns(),
            side=side,
            price_ticks=price_ticks,
            quantity=random.randint(1, 100),
            order_type=OrderType.LIMIT,
        )

        order.validate()
        return order

    async def generate_orders(self, delay=0.01):
        """Generate orders from historical dataset rows."""
        if delay < 0:
            raise ValueError("delay cannot be negative")

        if self.market_data is None:
            self.load_data()

        for order_id, (_, row) in enumerate(
            self.market_data.iterrows(), start=1
        ):
            yield self.generate_order(row, order_id)

            if delay > 0:
                await asyncio.sleep(delay)

    async def generate_random_orders(
        self,
        count=100_000,
        initial_price=1000.0,
        delay=0,
        seed=None,
    ):
        """Generate reproducible synthetic orders without dataset rows."""
        if count < 1:
            raise ValueError("count must be at least 1")

        if initial_price <= 0:
            raise ValueError("initial_price must be positive")

        if delay < 0:
            raise ValueError("delay cannot be negative")

        rng = random.Random(seed)
        price = float(initial_price)

        for order_id in range(1, count + 1):
            price += rng.choice([-1, 1]) * TICK_SIZE_INR
            price = max(price, TICK_SIZE_INR)

            side = rng.choice([Side.BUY, Side.SELL])

            order = Order(
                order_id=order_id,
                timestamp_ns=time.time_ns(),
                side=side,
                price_ticks=round(price / TICK_SIZE_INR),
                quantity=rng.randint(1, 100),
                order_type=OrderType.LIMIT,
            )

            order.validate()
            yield order

            if delay > 0:
                await asyncio.sleep(delay)
            elif order_id % 1000 == 0:
                await asyncio.sleep(0)
