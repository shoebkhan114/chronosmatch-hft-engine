"""Latency CSV read/write helpers (no matplotlib, no curses)."""
import os


def write_latency_csv(path, samples_ns):
    """Write samples (ns) as microseconds; temp file + rename so readers never see a half file."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write("latency_us\n")
        for v in samples_ns:
            f.write(f"{v / 1000.0:.3f}\n")
    os.replace(tmp, path)


def load_latencies(path):
    """Return latencies in microseconds; [] if the file is missing; bad rows are skipped."""
    try:
        with open(path) as f:
            lines = f.read().splitlines()[1:]
    except FileNotFoundError:
        return []
    values = []
    for line in lines:
        try:
            values.append(float(line))
        except ValueError:
            continue
    return values


def latency_stats_us(values):
    """Median, p99 (nearest rank) and max of microsecond values; None if empty."""
    if not values:
        return None
    import math
    from statistics import median
    ordered = sorted(values)
    return {
        "median": median(ordered),
        "p99": ordered[math.ceil(0.99 * len(ordered)) - 1],
        "max": ordered[-1],
    }
