"""Build a dashboard snapshot (plain data, no curses) from engine state."""
from src.book_view import format_book_lines, format_side_by_side
from src.latency_stats import LatencyWindow
from src.matching_engine import MatchingEngine


def _trade_lines(engine: MatchingEngine, depth: int) -> list:
    lines = ["RECENT TRADES",
             f"{'Buy ID':<10}{'Sell ID':<10}{'Price':<12}{'Quantity':<10}"]
    for t in engine.trades[-depth:][::-1]:
        lines.append(f"{t.buy_order_id:<10}{t.sell_order_id:<10}"
                     f"{t.price_ticks:<12}{t.quantity:<10}")
    if not engine.trades:
        lines.append("(no trades)")
    lines.append("")
    lines.append(
        f"Trades: {len(engine.trades)} | Buys in book: {len(engine.buy_orders)}"
        f" | Sells in book: {len(engine.sell_orders)}"
    )
    return lines


def make_snapshot(engine: MatchingEngine, window: LatencyWindow,
                  received: int, rate: float, depth: int = 8,
                  side_by_side: bool = False) -> dict:
    if side_by_side:
        lines = (format_side_by_side(engine, depth=depth) + [""]
                 + _trade_lines(engine, depth))
    else:
        lines = format_book_lines(engine, depth=depth, trade_depth=depth)
    return {
        "lines": lines,
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
