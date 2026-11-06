import pytest

from src.latency_stats import LatencyWindow


def test_empty_window_has_no_values():
    s = LatencyWindow(10).summary()
    assert s == {"count": 0, "median_us": None, "p99_us": None, "max_us": None}


def test_known_values_one_to_hundred_us():
    w = LatencyWindow(1000)
    for i in range(1, 101):
        w.add(i * 1000)
    s = w.summary()
    assert s["count"] == 100
    assert s["median_us"] == 50.5
    assert s["p99_us"] == 99.0
    assert s["max_us"] == 100.0


def test_window_drops_oldest_samples():
    w = LatencyWindow(3)
    for i in range(1, 6):
        w.add(i * 1000)
    s = w.summary()
    assert s["count"] == 3
    assert s["median_us"] == 4.0
    assert s["max_us"] == 5.0


def test_single_sample():
    w = LatencyWindow(5)
    w.add(7000)
    s = w.summary()
    assert s["median_us"] == s["p99_us"] == s["max_us"] == 7.0


def test_invalid_size_rejected():
    with pytest.raises(ValueError):
        LatencyWindow(0)
