
from bisect import insort
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
    """Limit-order matching engine.

    Matching mutates Order.quantity in place to represent remaining quantity.
    MARKET orders are currently unsupported.

    Orders are prioritized by price, timestamp_ns, then engine arrival
    sequence. Duplicate accepted order IDs are rejected for the engine's
    lifetime, including IDs of fully filled orders.
    """

    def __init__(self):
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []
        self.trades: List[Trade] = []

        self._seen_order_ids = set()
        self._arrival_sequence_by_order_id = {}
        self._next_arrival_sequence = 0

    def add_order(self, order: Order) -> List[Trade]:
        order.validate()

        if order.order_type == OrderType.MARKET:
            raise NotImplementedError(
                "Market orders will be implemented after limit orders."
            )

        if order.order_id in self._seen_order_ids:
            raise ValueError(f"Duplicate order_id: {order.order_id}")

        # Record every accepted order, even if it fills immediately.
        self._seen_order_ids.add(order.order_id)
        self._arrival_sequence_by_order_id[order.order_id] = (
            self._next_arrival_sequence
        )
        self._next_arrival_sequence += 1

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

            # Mutate original Order objects to track remaining quantities.
            order.quantity -= traded_quantity
            best.quantity -= traded_quantity

            if best.quantity == 0:
                opposite_orders.pop(0)

        if order.quantity > 0:
            if order.side == Side.BUY:
                insort(
                    self.buy_orders,
                    order,
                    key=lambda o: (
                        -o.price_ticks,
                        o.timestamp_ns,
                        self._arrival_sequence_by_order_id[o.order_id],
                    ),
                )
            else:
                insort(
                    self.sell_orders,
                    order,
                    key=lambda o: (
                        o.price_ticks,
                        o.timestamp_ns,
                        self._arrival_sequence_by_order_id[o.order_id],
                    ),
                )

        return new_trades
