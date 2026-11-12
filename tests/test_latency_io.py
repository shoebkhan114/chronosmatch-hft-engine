import threading
import time

from src.latency_io import load_latencies, write_latency_csv
from src.live_dashboard import dashboard_consumer, toggle_plot
from src.models import Order, OrderType, Side
from src.ring_buffer import RingBuffer


class FakeProc:
    def __init__(self, running=True):
        self.running = running
        self.terminated = False

    def poll(self):
        return None if self.running else 0

    def terminate(self):
        self.terminated = True
        self.running = False

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.running = False


def test_write_and_load_roundtrip(tmp_path):
    p = str(tmp_path / "l.csv")
    write_latency_csv(p, [1000, 2500, 40000])
    assert load_latencies(p) == [1.0, 2.5, 40.0]


def test_load_missing_file_is_empty(tmp_path):
    assert load_latencies(str(tmp_path / "none.csv")) == []


def test_load_skips_bad_rows(tmp_path):
    p = tmp_path / "l.csv"
    p.write_text("latency_us\n1.5\nabc\n\n2.5\n")
    assert load_latencies(str(p)) == [1.5, 2.5]


def test_toggle_starts_when_no_process():
    proc = FakeProc()
    assert toggle_plot(None, lambda: proc) is proc


def test_toggle_stops_running_process():
    proc = FakeProc(running=True)
    assert toggle_plot(proc, lambda: FakeProc()) is None
    assert proc.terminated


def test_toggle_restarts_after_window_closed():
    closed = FakeProc(running=False)
    fresh = FakeProc()
    assert toggle_plot(closed, lambda: fresh) is fresh


def test_consumer_writes_latency_csv(tmp_path):
    import queue
    path = str(tmp_path / "rb.bin")
    csv_path = str(tmp_path / "lat.csv")
    lock = threading.Lock()
    creator = RingBuffer(path, 16, create=True, lock=lock)
    for i in range(1, 11):
        side = Side.BUY if i % 2 else Side.SELL
        assert creator.put(Order(i, time.perf_counter_ns(), side, 10000, 5,
                                 OrderType.LIMIT))
    dashboard_consumer(path, 16, lock, 10, queue.Queue(), latency_csv=csv_path)
    creator.close()
    assert len(load_latencies(csv_path)) == 10


def test_latency_stats_us_known_values():
    from src.latency_io import latency_stats_us
    s = latency_stats_us([float(i) for i in range(1, 101)])
    assert s["median"] == 50.5 and s["p99"] == 99.0 and s["max"] == 100.0


def test_latency_stats_us_empty_is_none():
    from src.latency_io import latency_stats_us
    assert latency_stats_us([]) is None
