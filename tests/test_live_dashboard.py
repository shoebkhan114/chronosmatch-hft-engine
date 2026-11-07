import queue
import threading
import time

from src.live_dashboard import dashboard_consumer, screen_lines
from src.live_snapshot import make_snapshot
from src.latency_stats import LatencyWindow
from src.matching_engine import MatchingEngine
from src.models import Order, OrderType, Side
from src.ring_buffer import RingBuffer


def test_consumer_processes_all_orders_and_sends_final_snapshot(tmp_path):
    path = str(tmp_path / "rb.bin")
    lock = threading.Lock()
    creator = RingBuffer(path, 16, create=True, lock=lock)
    for i in range(1, 11):
        side = Side.BUY if i % 2 else Side.SELL
        order = Order(i, time.perf_counter_ns(), side, 10000, 5,
                      OrderType.LIMIT)
        assert creator.put(order)
    q = queue.Queue()
    dashboard_consumer(path, 16, lock, 10, q)
    snaps = []
    while not q.empty():
        snaps.append(q.get())
    creator.close()
    last = snaps[-1]
    assert last["done"] is True
    assert last["received"] == 10
    assert last["latency"]["count"] == 10
    assert "Trades: 5" in "\n".join(last["lines"])


def test_screen_lines_show_finished_message_only_when_done():
    snap = make_snapshot(MatchingEngine(), LatencyWindow(5), 0, 0.0)
    snap["done"] = False
    assert not any("FINISHED" in l for l in screen_lines(snap))
    snap["done"] = True
    assert any("FINISHED" in l for l in screen_lines(snap))


def test_screen_lines_start_with_status_header():
    snap = make_snapshot(MatchingEngine(), LatencyWindow(5), 0, 0.0)
    assert screen_lines(snap)[0].startswith("CHRONOSMATCH LIVE")


from src.live_dashboard import line_color


def test_line_color_titles_and_sides():
    assert line_color("CHRONOSMATCH LIVE (simulated)") == "title"
    assert line_color("FINISHED - all orders processed.") == "title"
    assert line_color("BUY ORDERS (highest price first)") == "buy"
    assert line_color("SELL ORDERS (lowest price first)") == "sell"


def test_line_color_stats_and_plain():
    assert line_color("end-to-end latency (last 5): median 1.0 us") == "stat"
    assert line_color("orders received: 5 | rate: 10/s") == "stat"
    assert line_color("99816     25166     23") == "plain"


def test_line_color_recent_trades_is_title():
    assert line_color("RECENT TRADES") == "title"


def test_line_color_empty_line_is_plain():
    assert line_color("") == "plain"
