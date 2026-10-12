
from src.models import Order, Side
from src.matching_engine import MatchingEngine


def make_order(order_id, side, price, quantity, timestamp):
    return Order(
        order_id=order_id,
        timestamp_ns=timestamp,
        side=side,
        price_ticks=price,
        quantity=quantity,
    )


def test_matching_buy_and_sell_orders():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.SELL, 100, 5, 1))
    trades = engine.add_order(make_order(2, Side.BUY, 100, 5, 2))

    assert len(trades) == 1
    assert trades[0].buy_order_id == 2
    assert trades[0].sell_order_id == 1
    assert trades[0].price_ticks == 100
    assert trades[0].quantity == 5
    assert engine.sell_orders == []


def test_non_matching_orders_remain_in_book():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.SELL, 110, 5, 1))
    trades = engine.add_order(make_order(2, Side.BUY, 100, 5, 2))

    assert trades == []
    assert len(engine.buy_orders) == 1
    assert len(engine.sell_orders) == 1


def test_partial_fill():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.SELL, 100, 10, 1))
    trades = engine.add_order(make_order(2, Side.BUY, 100, 4, 2))

    assert len(trades) == 1
    assert trades[0].quantity == 4
    assert engine.sell_orders[0].quantity == 6
    assert engine.buy_orders == []


def test_best_sell_price_first():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.SELL, 105, 3, 1))
    engine.add_order(make_order(2, Side.SELL, 100, 3, 2))

    trades = engine.add_order(make_order(3, Side.BUY, 110, 4, 3))

    assert [trade.sell_order_id for trade in trades] == [2, 1]
    assert [trade.quantity for trade in trades] == [3, 1]


def test_time_priority_at_same_price():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.SELL, 100, 3, 10))
    engine.add_order(make_order(2, Side.SELL, 100, 3, 20))

    trades = engine.add_order(make_order(3, Side.BUY, 100, 4, 30))

    assert [trade.sell_order_id for trade in trades] == [1, 2]
    assert [trade.quantity for trade in trades] == [3, 1]
