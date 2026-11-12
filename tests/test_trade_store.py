import pytest

from src.matching_engine import MatchingEngine, Trade
from src.models import Order, OrderType, Side
from src.trade_store import TradeStore


def make_order(order_id, side, price, qty, ts):
    return Order(
        order_id=order_id,
        timestamp_ns=ts,
        side=side,
        price_ticks=price,
        quantity=qty,
        order_type=OrderType.LIMIT,
    )


def test_submit_and_close_stores_rows(tmp_path):
    store = TradeStore(str(tmp_path / "t.db"))
    store.submit([Trade(2, 1, 10000, 3), Trade(3, 1, 10000, 2)])
    store.close()
    assert store.fetch_all() == [(2, 1, 10000, 3), (3, 1, 10000, 2)]


def test_order_preserved_across_batches(tmp_path):
    store = TradeStore(str(tmp_path / "t.db"))
    expected = []
    for i in range(1, 1301):
        store.submit([Trade(i, i + 5000, 10000 + i, 1)])
        expected.append((i, i + 5000, 10000 + i, 1))
    store.close()
    assert store.fetch_all() == expected


def test_empty_submit_stores_nothing(tmp_path):
    store = TradeStore(str(tmp_path / "t.db"))
    store.submit([])
    store.close()
    assert store.fetch_all() == []


def test_submit_after_close_raises_and_close_is_idempotent(tmp_path):
    store = TradeStore(str(tmp_path / "t.db"))
    store.close()
    store.close()
    with pytest.raises(RuntimeError):
        store.submit([Trade(1, 2, 10000, 1)])


def test_real_engine_trades_are_flushed(tmp_path):
    engine = MatchingEngine()
    store = TradeStore(str(tmp_path / "t.db"))
    engine.add_order(make_order(1, Side.SELL, 10000, 5, 1))
    store.submit(engine.add_order(make_order(2, Side.BUY, 10000, 3, 2)))
    store.submit(engine.add_order(make_order(3, Side.BUY, 10000, 2, 3)))
    store.close()
    assert store.fetch_all() == [(2, 1, 10000, 3), (3, 1, 10000, 2)]
    assert len(engine.trades) == 2
