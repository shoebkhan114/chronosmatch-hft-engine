"""SQLite trade store with a background writer thread.

submit() only puts trades on a queue, so the caller (engine hot path) does not
wait for disk I/O. A background thread writes them in batches. This is a thread,
not a process, so it still shares the GIL; the cost to the engine is not measured.
"""
import queue
import sqlite3
import threading
from typing import Iterable

from src.matching_engine import Trade

_STOP = object()
BATCH_SIZE = 500

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS trades ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "buy_order_id INTEGER NOT NULL, "
    "sell_order_id INTEGER NOT NULL, "
    "price_ticks INTEGER NOT NULL, "
    "quantity INTEGER NOT NULL)"
)


class TradeStore:
    def __init__(self, path: str):
        self.path = path
        self._queue: queue.Queue = queue.Queue()
        self._error = None
        self._closed = False
        # Create the table up front so errors surface in the caller's thread.
        conn = sqlite3.connect(path)
        conn.execute(SCHEMA)
        conn.commit()
        conn.close()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def submit(self, trades: Iterable[Trade]) -> None:
        if self._closed:
            raise RuntimeError("TradeStore is closed")
        rows = [
            (t.buy_order_id, t.sell_order_id, t.price_ticks, t.quantity)
            for t in trades
        ]
        if rows:
            self._queue.put(rows)

    def _run(self) -> None:
        conn = sqlite3.connect(self.path)
        try:
            stop = False
            while not stop:
                item = self._queue.get()
                batch = []
                if item is _STOP:
                    stop = True
                else:
                    batch.extend(item)
                while not stop and len(batch) < BATCH_SIZE:
                    try:
                        item = self._queue.get_nowait()
                    except queue.Empty:
                        break
                    if item is _STOP:
                        stop = True
                    else:
                        batch.extend(item)
                if batch:
                    conn.executemany(
                        "INSERT INTO trades (buy_order_id, sell_order_id, "
                        "price_ticks, quantity) VALUES (?, ?, ?, ?)",
                        batch,
                    )
                    conn.commit()
        except Exception as exc:
            self._error = exc
        finally:
            conn.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put(_STOP)
        self._thread.join()
        if self._error is not None:
            raise RuntimeError(f"TradeStore writer failed: {self._error!r}")

    def fetch_all(self):
        """Read stored trades (call after close() for a complete result)."""
        conn = sqlite3.connect(self.path)
        try:
            return conn.execute(
                "SELECT buy_order_id, sell_order_id, price_ticks, quantity "
                "FROM trades ORDER BY id"
            ).fetchall()
        finally:
            conn.close()
