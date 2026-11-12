from src.latency_stats import LatencyWindow
from src.live_snapshot import format_status_lines, make_snapshot
from src.matching_engine import MatchingEngine
from src.models import Order, OrderType, Side


def test_empty_snapshot_waits_for_data():
    snap = make_snapshot(MatchingEngine(), LatencyWindow(10), 0, 0.0)
    assert snap["latency"]["count"] == 0
    assert any("waiting for data" in l for l in format_status_lines(snap))


def test_snapshot_contains_book_and_latency():
    e = MatchingEngine()
    e.add_order(Order(1, 1, Side.SELL, 10000, 5, OrderType.LIMIT))
    w = LatencyWindow(10)
    w.add(5000)
    snap = make_snapshot(e, w, 1, 100.0)
    assert snap["received"] == 1
    assert snap["latency"]["median_us"] == 5.0
    assert any(l.startswith("1 ") for l in snap["lines"])


def test_status_lines_show_median_p99_max():
    w = LatencyWindow(10)
    for v in (1000, 2000, 3000):
        w.add(v)
    snap = make_snapshot(MatchingEngine(), w, 3, 50.0)
    text = "\n".join(format_status_lines(snap))
    assert "median 2.0 us" in text and "max 3.0 us" in text


def test_depth_is_applied():
    e = MatchingEngine()
    for i in range(1, 6):
        e.add_order(Order(i, i, Side.BUY, 9000 + i, 1, OrderType.LIMIT))
    snap = make_snapshot(e, LatencyWindow(5), 5, 0.0, depth=2)
    rows = [l for l in snap["lines"] if l and l[0].isdigit()]
    assert len(rows) == 2


def test_side_by_side_snapshot_has_spread_and_totals():
    e = MatchingEngine()
    e.add_order(Order(1, 1, Side.BUY, 100, 5, OrderType.LIMIT))
    e.add_order(Order(2, 2, Side.SELL, 103, 5, OrderType.LIMIT))
    snap = make_snapshot(e, LatencyWindow(5), 2, 0.0, side_by_side=True)
    text = "\n".join(snap["lines"])
    assert "SPREAD: 3 ticks" in text
    assert "Trades: 0 | Buys in book: 1 | Sells in book: 1" in text


def test_side_by_side_snapshot_lists_trades():
    e = MatchingEngine()
    e.add_order(Order(1, 1, Side.SELL, 100, 5, OrderType.LIMIT))
    e.add_order(Order(2, 2, Side.BUY, 100, 5, OrderType.LIMIT))
    snap = make_snapshot(e, LatencyWindow(5), 2, 0.0, side_by_side=True)
    assert any(l.split()[:4] == ["2", "1", "100", "5"] for l in snap["lines"])


def test_default_snapshot_is_not_side_by_side():
    snap = make_snapshot(MatchingEngine(), LatencyWindow(5), 0, 0.0)
    assert not any(l.startswith("SPREAD") for l in snap["lines"])


def test_line_color_spread_and_whale():
    from src.live_dashboard import line_color
    assert line_color("SPREAD: 3 ticks  |  WHALE: qty >= 90") == "stat"
    assert line_color("99816    25166    95       *") == "whale"


def test_line_color_side_by_side_headers():
    from src.live_dashboard import line_color
    assert line_color("BUY (best first)      SELL (best first)") == "title"
    assert line_color("ID       Price    Qty") == "title"
