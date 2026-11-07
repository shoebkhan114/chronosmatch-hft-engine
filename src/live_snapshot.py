"""Build a dashboard snapshot (plain data, no curses) from engine state."""
from src.book_view import format_book_lines
from src.latency_stats import LatencyWindow
from src.matching_engine import MatchingEngine


def make_snapshot(engine: MatchingEngine, window: LatencyWindow,
                  received: int, rate: float, depth: int = 8) -> dict:
    return {
        "lines": format_book_lines(engine, depth=depth, trade_depth=depth),
        "latency": window.summary(),
        "received": received,
        "rate": rate,
    }


def format_status_lines(snapshot: dict) -> list:
    lat = snapshot["latency"]
    if lat["count"] == 0:
        lat_text = "end-to-end latency: waiting for data"
    else:
        lat_text = (
            f"end-to-end latency (last {lat['count']}): "
            f"median {lat['median_us']:.1f} us | p99 {lat['p99_us']:.1f} us"
            f" | max {lat['max_us']:.1f} us"
        )
    return [
        "CHRONOSMATCH LIVE (simulated)  -  press q to quit",
        f"orders received: {snapshot['received']} | rate: {snapshot['rate']:.0f}/s",
        lat_text,
        "",
    ]
