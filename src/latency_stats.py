"""Rolling latency statistics for the live dashboard (no curses dependency)."""
import math
from collections import deque
from statistics import median


class LatencyWindow:
    """Keeps the most recent `size` latency samples (nanoseconds)."""

    def __init__(self, size: int = 1000):
        if size < 1:
            raise ValueError("size must be at least 1")
        self._values = deque(maxlen=size)

    def add(self, latency_ns: int) -> None:
        self._values.append(latency_ns)

    def summary(self) -> dict:
        """Return count, median_us, p99_us, max_us (None values if empty)."""
        n = len(self._values)
        if n == 0:
            return {"count": 0, "median_us": None, "p99_us": None, "max_us": None}
        ordered = sorted(self._values)
        p99_index = math.ceil(0.99 * n) - 1  # nearest-rank
        return {
            "count": n,
            "median_us": median(ordered) / 1000.0,
            "p99_us": ordered[p99_index] / 1000.0,
            "max_us": ordered[-1] / 1000.0,
        }
