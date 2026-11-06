"""Plain-text order book view for the live dashboard (no curses dependency)."""
from typing import List

from src.matching_engine import MatchingEngine


def _side_lines(title: str, orders, depth: int) -> List[str]:
    lines = [title, f"{'Order ID':<12}{'Price':<10}{'Remaining Qty':<15}"]
    for order in orders[:depth]:
        lines.append(
            f"{order.order_id:<12}{order.price_ticks:<10}{order.quantity:<15}"
        )
    if not orders:
        lines.append("(empty)")
    return lines


def format_book_lines(
    engine: MatchingEngine, depth: int = 10, trade_depth: int = 10
) -> List[str]:
    lines = _side_lines("BUY ORDERS (highest price first)", engine.buy_orders, depth)
    lines.append("")
    lines += _side_lines("SELL ORDERS (lowest price first)", engine.sell_orders, depth)
    lines.append("")
    lines.append("RECENT TRADES")
    lines.append(f"{'Buy ID':<10}{'Sell ID':<10}{'Price':<12}{'Quantity':<10}")
    for trade in engine.trades[-trade_depth:][::-1]:
        lines.append(
            f"{trade.buy_order_id:<10}{trade.sell_order_id:<10}"
            f"{trade.price_ticks:<12}{trade.quantity:<10}"
        )
    if not engine.trades:
        lines.append("(no trades)")
    lines.append("")
    lines.append(
        f"Trades: {len(engine.trades)} | Buys in book: {len(engine.buy_orders)}"
        f" | Sells in book: {len(engine.sell_orders)}"
    )
    return lines
