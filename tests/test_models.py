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
    
    def test_invalid_order_id(self):
        order = Order(
            order_id=0,
            timestamp_ns=1000,
            side=Side.BUY,
            price_ticks=25000,
            quantity=10,
        )
        with self.assertRaises(ValueError):
            order.validate()

    def test_negative_timestamp(self):
        order = Order(
            order_id=1,
            timestamp_ns=-1,
            side=Side.BUY,
            price_ticks=25000,
            quantity=10,
        )
        with self.assertRaises(ValueError):
            order.validate()

    def test_invalid_side(self):
        order = Order(
            order_id=1,
            timestamp_ns=1000,
            side=99,
            price_ticks=25000,
            quantity=10,
        )
        with self.assertRaises(ValueError):
            order.validate()

    def test_invalid_order_type(self):
        order = Order(
            order_id=1,
            timestamp_ns=1000,
            side=Side.BUY,
            price_ticks=25000,
            quantity=10,
            order_type=99,
        )
        with self.assertRaises(ValueError):
            order.validate()
        


if __name__ == "__main__":
    unittest.main()