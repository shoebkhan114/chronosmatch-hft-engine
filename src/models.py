from dataclasses import dataclass
from enum import IntEnum


class Side(IntEnum):
    BUY = 1
    SELL = 2


class OrderType(IntEnum):
    LIMIT = 1
    MARKET = 2


@dataclass(slots=True)
class Order:
    order_id: int
    timestamp_ns: int
    side: Side
    price_ticks: int
    quantity: int
    order_type: OrderType = OrderType.LIMIT

    def validate(self) -> None:
        if self.order_id <= 0:
            raise ValueError("order_id must be positive")

        if self.timestamp_ns < 0:
            raise ValueError("timestamp_ns cannot be negative")

        if self.price_ticks <= 0:
            raise ValueError("price_ticks must be positive")

        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

        if not isinstance(self.side, Side):
            raise ValueError("side must be Side.BUY or Side.SELL")

        if not isinstance(self.order_type, OrderType):
            raise ValueError("Invalid order type")