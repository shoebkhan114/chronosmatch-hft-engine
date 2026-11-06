from src.book_view import format_book_lines
from src.matching_engine import MatchingEngine
from src.models import Order, OrderType, Side


def mk(i, side, price, qty):
    return Order(order_id=i, timestamp_ns=i, side=side, price_ticks=price,
                 quantity=qty, order_type=OrderType.LIMIT)


def test_empty_book():
    text = "\n".join(format_book_lines(MatchingEngine()))
    assert "(empty)" in text
    assert "(no trades)" in text
    assert "Trades: 0 | Buys in book: 0 | Sells in book: 0" in text


def test_best_bid_and_ask_listed_first():
    e = MatchingEngine()
    e.add_order(mk(1, Side.BUY, 9900, 5))
    e.add_order(mk(2, Side.BUY, 9950, 5))
    e.add_order(mk(3, Side.SELL, 10100, 5))
    e.add_order(mk(4, Side.SELL, 10050, 5))
    lines = format_book_lines(e)
    buy_rows = lines[2:4]
    assert buy_rows[0].startswith("2 ")
    assert buy_rows[1].startswith("1 ")
    sell_start = lines.index("SELL ORDERS (lowest price first)")
    assert lines[sell_start + 2].startswith("4 ")
    assert lines[sell_start + 3].startswith("3 ")


def test_depth_limits_rows():
    e = MatchingEngine()
    for i in range(1, 8):
        e.add_order(mk(i, Side.BUY, 9000 + i, 1))
    lines = format_book_lines(e, depth=3)
    rows = [l for l in lines[2:] if l and l[0].isdigit()]
    assert len(rows) == 3


def test_trades_shown_newest_first():
    e = MatchingEngine()
    e.add_order(mk(1, Side.SELL, 10000, 5))
    e.add_order(mk(2, Side.BUY, 10000, 2))
    e.add_order(mk(3, Side.BUY, 10000, 1))
    lines = format_book_lines(e)
    i = lines.index(f"{'Buy ID':<10}{'Sell ID':<10}{'Price':<12}{'Quantity':<10}")
    assert lines[i + 1].startswith("3 ")
    assert lines[i + 2].startswith("2 ")


def test_partial_fill_shows_remaining_quantity():
    e = MatchingEngine()
    e.add_order(mk(1, Side.SELL, 10000, 5))
    e.add_order(mk(2, Side.BUY, 10000, 2))
    lines = format_book_lines(e)
    sell_start = lines.index("SELL ORDERS (lowest price first)")
    assert lines[sell_start + 2].split() == ["1", "10000", "3"]
