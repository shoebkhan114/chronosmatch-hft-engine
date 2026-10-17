
import pytest
from src.models import Order, Side, OrderType
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
    
def test_one_buy_matches_multiple_sellers():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.SELL, 100, 3, 1))
    engine.add_order(make_order(2, Side.SELL, 101, 4, 2))

    trades = engine.add_order(make_order(3, Side.BUY, 105, 5, 3))

    assert len(trades) == 2
    assert trades[0].sell_order_id == 1
    assert trades[0].quantity == 3
    assert trades[1].sell_order_id == 2
    assert trades[1].quantity == 2
    assert engine.sell_orders[0].quantity == 2
    assert engine.buy_orders == []


def test_highest_priced_buy_has_priority():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.BUY, 100, 3, 1))
    engine.add_order(make_order(2, Side.BUY, 105, 3, 2))

    trades = engine.add_order(make_order(3, Side.SELL, 100, 4, 3))

    assert len(trades) == 2
    assert trades[0].buy_order_id == 2
    assert trades[0].quantity == 3
    assert trades[1].buy_order_id == 1
    assert trades[1].quantity == 1


def test_fully_filled_incoming_order_is_not_added_to_book():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.SELL, 100, 5, 1))
    incoming = make_order(2, Side.BUY, 100, 5, 2)

    trades = engine.add_order(incoming)

    assert sum(trade.quantity for trade in trades) == 5
    assert incoming.quantity == 0
    assert engine.buy_orders == []
    assert engine.sell_orders == []

import pytest


def test_invalid_order_is_rejected():
    engine = MatchingEngine()

    invalid_order = make_order(1, Side.BUY, 100, 0, 1)

    with pytest.raises(ValueError, match="quantity must be positive"):
        engine.add_order(invalid_order)

    assert engine.buy_orders == []
    assert engine.sell_orders == []


def test_no_trade_when_prices_do_not_cross():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.BUY, 100, 5, 1))
    trades = engine.add_order(make_order(2, Side.SELL, 105, 3, 2))

    assert trades == []
    assert len(engine.buy_orders) == 1
    assert len(engine.sell_orders) == 1
    assert engine.buy_orders[0].quantity == 5
    assert engine.sell_orders[0].quantity == 3

def test_buy_orders_follow_time_priority_at_same_price():
    engine = MatchingEngine()

    # Both buy orders have the same price.
    engine.add_order(make_order(1, Side.BUY, 100, 3, 10))
    engine.add_order(make_order(2, Side.BUY, 100, 3, 20))

    # This sell order can match both buy orders.
    trades = engine.add_order(make_order(3, Side.SELL, 100, 4, 30))

    # The earlier buy order must be filled first.
    assert len(trades) == 2
    assert trades[0].buy_order_id == 1
    assert trades[0].quantity == 3
    assert trades[1].buy_order_id == 2
    assert trades[1].quantity == 1

    # The second buy order has two units remaining.
    assert len(engine.buy_orders) == 1
    assert engine.buy_orders[0].order_id == 2
    assert engine.buy_orders[0].quantity == 2
def test_market_orders_are_not_supported():
    engine = MatchingEngine()

    market_order = Order(
        order_id=1,
        timestamp_ns=1,
        side=Side.BUY,
        price_ticks=100,
        quantity=5,
        order_type=OrderType.MARKET,
    )

    with pytest.raises(
        NotImplementedError,
        match="Market orders will be implemented after limit orders",
    ):
        engine.add_order(market_order)

    assert engine.buy_orders == []
    assert engine.sell_orders == []

def test_duplicate_order_id_is_rejected():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.SELL, 100, 5, 1))

    with pytest.raises(ValueError, match="Duplicate order_id"):
        engine.add_order(make_order(1, Side.BUY, 100, 5, 2))

    assert len(engine.sell_orders) == 1
    assert engine.sell_orders[0].quantity == 5
    assert engine.buy_orders == []


def test_duplicate_id_rejected_after_original_order_is_filled():
    engine = MatchingEngine()

    original = make_order(1, Side.SELL, 100, 2, 1)
    engine.add_order(original)
    engine.add_order(make_order(2, Side.BUY, 100, 2, 2))

    assert original.quantity == 0

    with pytest.raises(ValueError, match="Duplicate order_id"):
        engine.add_order(make_order(1, Side.SELL, 100, 3, 3))


def test_equal_timestamps_preserve_arrival_order():
    engine = MatchingEngine()

    engine.add_order(make_order(1, Side.SELL, 100, 3, 10))
    engine.add_order(make_order(2, Side.SELL, 100, 3, 10))

    trades = engine.add_order(make_order(3, Side.BUY, 100, 4, 20))

    assert [trade.sell_order_id for trade in trades] == [1, 2]
    assert [trade.quantity for trade in trades] == [3, 1]
    assert engine.sell_orders[0].order_id == 2
    assert engine.sell_orders[0].quantity == 2


def test_matching_mutates_original_order_quantities():
    engine = MatchingEngine()

    resting_sell = make_order(1, Side.SELL, 100, 10, 1)
    incoming_buy = make_order(2, Side.BUY, 100, 4, 2)

    engine.add_order(resting_sell)
    engine.add_order(incoming_buy)

    assert resting_sell.quantity == 6
    assert incoming_buy.quantity == 0


def test_market_orders_are_not_supported():
    engine = MatchingEngine()

    market_order = Order(
        order_id=1,
        timestamp_ns=1,
        side=Side.BUY,
        price_ticks=100,
        quantity=5,
        order_type=OrderType.MARKET,
    )

    with pytest.raises(
        NotImplementedError,
        match="Market orders will be implemented after limit orders",
    ):
        engine.add_order(market_order)

    assert engine.buy_orders == []
    assert engine.sell_orders == []
    assert engine.trades == []

