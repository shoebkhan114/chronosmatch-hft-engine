
from bisect import bisect_right
from dataclasses import dataclass
from typing import List

from src.models import Order, Side, OrderType


cdef class Trade:
    cdef public unsigned long long buy_order_id
    cdef public unsigned long long sell_order_id
    cdef public unsigned long long price_ticks
    cdef public unsigned long long quantity

    def __init__(self, buy_order_id, sell_order_id, price_ticks, quantity):
        self.buy_order_id = buy_order_id
        self.sell_order_id = sell_order_id
        self.price_ticks = price_ticks
        self.quantity = quantity

    def __repr__(self):
        return (
            f"Trade(buy_order_id={self.buy_order_id}, "
            f"sell_order_id={self.sell_order_id}, "
            f"price_ticks={self.price_ticks}, quantity={self.quantity})"
        )

    def __eq__(self, other):
        if not isinstance(other, Trade):
            return NotImplemented
        return (
            self.buy_order_id == other.buy_order_id
            and self.sell_order_id == other.sell_order_id
            and self.price_ticks == other.price_ticks
            and self.quantity == other.quantity
        )


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
        self._buy_keys = []
        self._sell_keys = []

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
            opposite_keys = self._sell_keys
        else:
            opposite_orders = self.buy_orders
            opposite_keys = self._buy_keys

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
                opposite_keys.pop(0)

        if order.quantity > 0:
            seq = self._arrival_sequence_by_order_id[order.order_id]
            if order.side == Side.BUY:
                key = (-order.price_ticks, order.timestamp_ns, seq)
                pos = bisect_right(self._buy_keys, key)
                self._buy_keys.insert(pos, key)
                self.buy_orders.insert(pos, order)
            else:
                key = (order.price_ticks, order.timestamp_ns, seq)
                pos = bisect_right(self._sell_keys, key)
                self._sell_keys.insert(pos, key)
                self.sell_orders.insert(pos, order)

        return new_trades
