import os
import tempfile

from src.matching_engine import MatchingEngine
from src.models import Order, Side, OrderType
from src.ring_buffer import RingBuffer


def make_buffer(capacity=8):
    fd, path = tempfile.mkstemp(suffix=".rb")
    os.close(fd)
    return RingBuffer(path, capacity, create=True), path


def test_ring_buffer_to_engine_full_fill():
    rb, path = make_buffer()
    try:
        rb.put(Order(1, 100, Side.SELL, 10000, 50, OrderType.LIMIT))
        rb.put(Order(2, 200, Side.BUY, 10000, 50, OrderType.LIMIT))

        engine = MatchingEngine()
        trades = []
        while (order := rb.get()) is not None:
            trades.extend(engine.add_order(order))

        assert len(trades) == 1
        assert trades[0].buy_order_id == 2
        assert trades[0].sell_order_id == 1
        assert trades[0].price_ticks == 10000
        assert trades[0].quantity == 50
        assert engine.buy_orders == []
        assert engine.sell_orders == []
    finally:
        rb.close()
        os.remove(path)


def test_ring_buffer_to_engine_partial_fill():
    rb, path = make_buffer()
    try:
        rb.put(Order(1, 100, Side.SELL, 10000, 30, OrderType.LIMIT))
        rb.put(Order(2, 200, Side.BUY, 10000, 50, OrderType.LIMIT))

        engine = MatchingEngine()
        trades = []
        while (order := rb.get()) is not None:
            trades.extend(engine.add_order(order))

        assert len(trades) == 1
        assert trades[0].quantity == 30
        assert engine.sell_orders == []
        assert len(engine.buy_orders) == 1
        assert engine.buy_orders[0].order_id == 2
        assert engine.buy_orders[0].quantity == 20
    finally:
        rb.close()
        os.remove(path)
