from src.book_view import format_side_by_side, spread_ticks
from src.matching_engine import MatchingEngine
from src.models import Order, OrderType, Side


def mk(i, side, price, qty):
    return Order(i, i, side, price, qty, OrderType.LIMIT)


def test_spread_none_when_a_side_is_empty():
    e = MatchingEngine()
    assert spread_ticks(e) is None
    e.add_order(mk(1, Side.BUY, 100, 5))
    assert spread_ticks(e) is None


def test_spread_is_best_ask_minus_best_bid():
    e = MatchingEngine()
    e.add_order(mk(1, Side.BUY, 100, 5))
    e.add_order(mk(2, Side.BUY, 99, 5))
    e.add_order(mk(3, Side.SELL, 103, 5))
    e.add_order(mk(4, Side.SELL, 105, 5))
    assert spread_ticks(e) == 3
    assert format_side_by_side(e)[0].startswith("SPREAD: 3 ticks")


def test_empty_book_has_header_and_one_blank_row():
    lines = format_side_by_side(MatchingEngine())
    assert lines[0].startswith("SPREAD: n/a")
    assert len(lines) == 4


def test_buy_left_sell_right_same_row():
    e = MatchingEngine()
    e.add_order(mk(1, Side.BUY, 100, 5))
    e.add_order(mk(2, Side.SELL, 103, 7))
    row = format_side_by_side(e)[3]
    assert row.split() == ["1", "100", "5", "2", "103", "7"]


def test_whale_marked_only_at_threshold():
    e = MatchingEngine()
    e.add_order(mk(1, Side.BUY, 100, 89))
    e.add_order(mk(2, Side.BUY, 99, 90))
    rows = format_side_by_side(e, whale_qty=90)[3:]
    assert "*" not in rows[0]
    assert "*" in rows[1]


def test_depth_limits_rows():
    e = MatchingEngine()
    for i in range(1, 8):
        e.add_order(mk(i, Side.BUY, 100 - i, 1))
    assert len(format_side_by_side(e, depth=3)) == 3 + 3
