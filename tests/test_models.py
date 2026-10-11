import unittest

from src.models import Order, OrderType, Side


class TestOrder(unittest.TestCase):
    def test_valid_order(self):
        order = Order(
            order_id=1,
            timestamp_ns=1000,
            side=Side.BUY,
            price_ticks=25000,
            quantity=10,
        )
        order.validate()

    def test_invalid_quantity(self):
        order = Order(
            order_id=1,
            timestamp_ns=1000,
            side=Side.BUY,
            price_ticks=25000,
            quantity=0,
        )
        with self.assertRaises(ValueError):
            order.validate()

    def test_invalid_price(self):
        order = Order(
            order_id=1,
            timestamp_ns=1000,
            side=Side.SELL,
            price_ticks=0,
            quantity=10,
        )
        with self.assertRaises(ValueError):
            order.validate()


if __name__ == "__main__":
    unittest.main()