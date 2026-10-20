
from bisect import bisect_left
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

    Features:
    - Price-time priority
    - Full and partial order matching
    - Remaining quantity tracking
    - Trade recording
    - Duplicate order ID validation
    - Sorted order insertion using bisect

    MARKET orders are currently unsupported.
    """

    def __init__(self):
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []
        self.trades: List[Trade] = []

        self._seen_order_ids = set()
        self._arrival_sequence_by_order_id = {}
        self._next_arrival_sequence = 0

    def _insert_order_sorted(
        self, orders: List[Order], order: Order
    ) -> None:
        """Insert an order while preserving price-time priority."""

        if orders is self.buy_orders:
            new_key = (
                -order.price_ticks,
                order.timestamp_ns,
                self._arrival_sequence_by_order_id[order.order_id],
            )

            keys = [
                (
                    -existing.price_ticks,
                    existing.timestamp_ns,
                    self._arrival_sequence_by_order_id[existing.order_id],
                )
                for existing in orders
            ]

        else:
            new_key = (
                order.price_ticks,
                order.timestamp_ns,
                self._arrival_sequence_by_order_id[order.order_id],
            )

            keys = [
                (
                    existing.price_ticks,
                    existing.timestamp_ns,
                    self._arrival_sequence_by_order_id[existing.order_id],
                )
                for existing in orders
            ]

        position = bisect_left(keys, new_key)
        orders.insert(position, order)

    def add_order(self, order: Order) -> List[Trade]:
        """Add an order, match it against the book, and return new trades."""

        # Validate the incoming order.
        order.validate()

        # Market orders are not implemented yet.
        if order.order_type == OrderType.MARKET:
            raise NotImplementedError(
                "Market orders will be implemented after limit orders."
            )

        # Reject duplicate order IDs.
        if order.order_id in self._seen_order_ids:
            raise ValueError(f"Duplicate order_id: {order.order_id}")

        # Record the order's arrival sequence.
        self._seen_order_ids.add(order.order_id)

        self._arrival_sequence_by_order_id[order.order_id] = (
            self._next_arrival_sequence
        )
        self._next_arrival_sequence += 1

        new_trades = []

        # Select the opposite side of the order book.
        if order.side == Side.BUY:
            opposite_orders = self.sell_orders
        else:
            opposite_orders = self.buy_orders

        # Match while the incoming order has quantity remaining.
        while order.quantity > 0 and opposite_orders:
            best = opposite_orders[0]

            # Check whether the best opposite order can be matched.
            if order.side == Side.BUY:
                if order.price_ticks < best.price_ticks:
                    break
            else:
                if order.price_ticks > best.price_ticks:
                    break

            # Determine the quantity traded.
            traded_quantity = min(order.quantity, best.quantity)

            # The trade executes at the resting order's price.
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

            # Record the trade.
            new_trades.append(trade)
            self.trades.append(trade)

            # Update remaining quantities.
            order.quantity -= traded_quantity
            best.quantity -= traded_quantity

            # Remove fully filled resting orders.
            if best.quantity == 0:
                opposite_orders.pop(0)

        # Insert any unfilled quantity into the appropriate order book.
        if order.quantity > 0:
            if order.side == Side.BUY:
                self._insert_order_sorted(self.buy_orders, order)
            else:
                self._insert_order_sorted(self.sell_orders, order)

        return new_trades
