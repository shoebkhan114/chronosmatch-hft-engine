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


WHALE_QTY = 90


def spread_ticks(engine: MatchingEngine):
    """Best ask minus best bid in ticks, or None if either side is empty."""
    if not engine.buy_orders or not engine.sell_orders:
        return None
    return engine.sell_orders[0].price_ticks - engine.buy_orders[0].price_ticks


def format_side_by_side(
    engine: MatchingEngine, depth: int = 8, whale_qty: int = WHALE_QTY
) -> List[str]:
    """BUY (left) and SELL (right) columns; rows with qty >= whale_qty end in ' <WHALE>'."""
    spread = spread_ticks(engine)
    spread_text = "n/a" if spread is None else f"{spread} ticks"
    lines = [
        f"SPREAD: {spread_text}  |  WHALE: qty >= {whale_qty}",
        f"{'BUY (best first)':<34}{'SELL (best first)':<34}",
        f"{'ID':<9}{'Price':<9}{'Qty':<9}  {'ID':<9}{'Price':<9}{'Qty':<9}",
    ]

    def cell(order):
        if order is None:
            return " " * 28
        mark = "*" if order.quantity >= whale_qty else " "
        return f"{order.order_id:<9}{order.price_ticks:<9}{order.quantity:<9}{mark}"

    buys = engine.buy_orders[:depth]
    sells = engine.sell_orders[:depth]
    for i in range(max(len(buys), len(sells), 1)):
        left = cell(buys[i] if i < len(buys) else None)
        right = cell(sells[i] if i < len(sells) else None)
        lines.append(f"{left}  {right}".rstrip())
    return lines
