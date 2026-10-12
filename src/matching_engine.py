
from dataclasses import dataclass
from typing import List

from src.models import Order, Side, OrderType


@dataclass(slots=True)
class Trade:
    buy_order_id: int
    sell_order_id: int
    price_ticks: int
    quantity: int


class MatchingEngine:
    def __init__(self):
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []
        self.trades: List[Trade] = []

    def add_order(self, order: Order) -> List[Trade]:
        order.validate()

        if order.order_type == OrderType.MARKET:
            raise NotImplementedError(
                "Market orders will be implemented after limit orders."
            )

        new_trades = []

        if order.side == Side.BUY:
            opposite_orders = self.sell_orders
        else:
            opposite_orders = self.buy_orders

        while order.quantity > 0 and opposite_orders:
            best = opposite_orders[0]

            if order.side == Side.BUY:
                if order.price_ticks < best.price_ticks:
                    break
            else:
                if order.price_ticks > best.price_ticks:
                    break

            traded_quantity = min(order.quantity, best.quantity)

            trade = Trade(
                buy_order_id=(
                    order.order_id
                    if order.side == Side.BUY
                    else best.order_id
                ),
                sell_order_id=(
                    order.order_id
                    if order.side == Side.SELL
                    else best.order_id
                ),
                price_ticks=best.price_ticks,
                quantity=traded_quantity,
            )

            new_trades.append(trade)
            self.trades.append(trade)

            order.quantity -= traded_quantity
            best.quantity -= traded_quantity

            if best.quantity == 0:
                opposite_orders.pop(0)

        if order.quantity > 0:
            if order.side == Side.BUY:
                self.buy_orders.append(order)
                self.buy_orders.sort(
                    key=lambda o: (-o.price_ticks, o.timestamp_ns)
                )
            else:
                self.sell_orders.append(order)
                self.sell_orders.sort(
                    key=lambda o: (o.price_ticks, o.timestamp_ns)
                )

        return new_trades
