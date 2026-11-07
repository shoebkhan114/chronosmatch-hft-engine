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
