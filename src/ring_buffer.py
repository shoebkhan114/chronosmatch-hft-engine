
import mmap
import os
import struct
import threading

from src.models import Order, OrderType, Side


# Header: write position, read position, capacity
HEADER = struct.Struct("<QQQ")

# Order: ID, timestamp, side, price, quantity, order type
ORDER_RECORD = struct.Struct("<QqBQIB")
HEADER_SIZE = HEADER.size
RECORD_SIZE = ORDER_RECORD.size


class RingBuffer:
    """Fixed-capacity mmap ring buffer for binary order records."""

    def __init__(self, path: str, capacity: int, create: bool = False, lock=None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self.path = path
        self.capacity = capacity
        self.lock = lock if lock is not None else threading.Lock()
        self.size = HEADER_SIZE + capacity * RECORD_SIZE

        if create:
            with open(path, "wb") as file:
                file.truncate(self.size)

        if not os.path.exists(path):
            raise FileNotFoundError(path)

        if os.path.getsize(path) != self.size:
            raise ValueError("File size does not match capacity")

        self.file = open(path, "r+b")
        self.memory = mmap.mmap(self.file.fileno(), self.size)

        if create:
            HEADER.pack_into(
                self.memory, 0, 0, 0, capacity
            )
            self.memory.flush()
        else:
            write_pos, read_pos, stored_capacity = HEADER.unpack_from(
                self.memory, 0
            )
            if stored_capacity != capacity:
                self.close()
                raise ValueError("Stored capacity does not match")

    def put(self, order: Order) -> bool:
        order.validate()

        with self.lock:
            write_pos, read_pos, capacity = HEADER.unpack_from(
                self.memory, 0
            )

            if write_pos - read_pos >= capacity:
                return False

            offset = HEADER_SIZE + (
                write_pos % capacity
            ) * RECORD_SIZE

            ORDER_RECORD.pack_into(
                self.memory,
                offset,
                order.order_id,
                order.timestamp_ns,
                int(order.side),
                order.price_ticks,
                order.quantity,
                int(order.order_type),
            )

            HEADER.pack_into(
                self.memory, 0,
                write_pos + 1, read_pos, capacity
            )
            return True

    def get(self):
        with self.lock:
            write_pos, read_pos, capacity = HEADER.unpack_from(
                self.memory, 0
            )

            if read_pos >= write_pos:
                return None

            offset = HEADER_SIZE + (
                read_pos % capacity
            ) * RECORD_SIZE

            values = ORDER_RECORD.unpack_from(
                self.memory, offset
            )

            HEADER.pack_into(
                self.memory, 0,
                write_pos, read_pos + 1, capacity
            )

        order_id, timestamp_ns, side, price, quantity, order_type = values

        return Order(
            order_id=order_id,
            timestamp_ns=timestamp_ns,
            side=Side(side),
            price_ticks=price,
            quantity=quantity,
            order_type=OrderType(order_type),
        )

    def close(self):
        if getattr(self, "memory", None) is not None:
            self.memory.close()
            self.memory = None

        if getattr(self, "file", None) is not None:
            self.file.close()
            self.file = None
