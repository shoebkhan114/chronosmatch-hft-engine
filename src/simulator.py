import asyncio
import pandas as pd
import random
import time

class MarketSimulator:
    def __init__(self, dataset_path="data/NIFTY50_all.csv"):
        self.dataset_path = dataset_path
        self.market_data = None

    def load_data(self):
        self.market_data = pd.read_csv(self.dataset_path)

        self.market_data["Date"] = pd.to_datetime(
            self.market_data["Date"]
        )

        self.market_data = self.market_data.dropna(
            subset=["Open", "High", "Low", "Close", "Volume"]
        )

        return self.market_data
    
    def generate_order(self, row, order_id):
        side = random.choice(["BUY", "SELL"])

        if side == "BUY":
            price = row["Close"] * 1.001
        else:
            price = row["Close"] * 0.999

        return {
            "order_id": order_id,
            "timestamp_ns": time.time_ns(),
            "side": side,
            "price": round(price, 2),
            "quantity": random.randint(1, 100),
            "symbol": row["Symbol"],
        }

    async def generate_orders(self, delay=0.01):
        if self.market_data is None:
            self.load_data()

        order_id = 1

        for _, row in self.market_data.iterrows():
            order = self.generate_order(row, order_id)
            yield order

            order_id += 1
            await asyncio.sleep(delay)   