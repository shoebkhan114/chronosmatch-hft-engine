# ChronosMatch Architecture

## 1. Project Objective

ChronosMatch is a high-performance limit order book engine designed to simulate buy and sell orders, transfer order messages between processes, execute matching logic, and measure throughput and latency.

## 2. Main Components

1. Market Simulator - generates valid order events using Python asyncio.
2. Shared-Memory Ring Buffer - transfers binary messages using mmap and struct.
3. Matching Engine - matches compatible orders using price-time priority.
4. Live Terminal Dashboard - curses screen showing the order book, recent trades, order rate and rolling end-to-end latency (median/p99/max). A manual print()/input() demo (`src/dashboard.py`) also exists.
5. Trade Store - SQLite store with a background writer thread (`src/trade_store.py`). Implemented and unit-tested, not yet connected to the pipeline.
6. Benchmarking and Tests - validates correctness and measures performance.

## 3. Data Flow

Market Simulator -> Shared-Memory Ring Buffer -> Matching Engine -> Metrics and Terminal Dashboard

Live dashboard flow (`python -m src.live_dashboard`): producer process -> ring buffer -> consumer process (matching engine + latency window) -> snapshot queue (about every 100 ms, dropped if full) -> curses screen in the main process. Latency shown is end-to-end (producer timestamp to after add_order), so it includes queueing delay in the ring buffer and is in milliseconds, not microseconds.

## 4. Development Principles

- Each member works on their assigned Git branch.
- Modules use an agreed common order schema.
- Correctness tests come before optimization.
- Performance claims must be supported by repeatable benchmarks.
- Branches are not merged into main until review requirements are confirmed.

## 5. Current Status

- Common Order model, mmap ring buffer (30-byte struct records, shared lock), Python and Cython matching engines, asyncio simulator (dataset and seeded random-walk modes).
- Latest automated test run: 86 passed, 1 deselected (slow 1M-order test, run with `pytest -m slow`).
- Cython vs Python engine-only: about 35 to 43 percent faster in 3 sessions (not isolated, not measured end to end).
- GC experiment (10 alternating rounds, one session): no clear effect on median or p99; see `docs/benchmark_results.md`.
- TradeStore (SQLite, background thread): unit-tested, not connected to the pipeline, cost to the engine not measured.
- Live curses dashboard: run manually; the curses screen layer itself is not unit-tested.
- Throughput numbers are single runs on a noisy laptop and vary a lot between runs; all figures and caveats are in `docs/benchmark_results.md`.
- Targets of 100,000 orders/sec and under 50 microseconds end to end are NOT achieved.

## 6. Ring Buffer Limitations

- External synchronization: independent processes must share the same multiprocessing-compatible lock. The default threading lock is not sufficient for process synchronization.
- No crash recovery: unexpected process termination during an operation may leave the buffer in an inconsistent state; automatic recovery is not implemented.
- Full-buffer behaviour: `put()` returns `False` when the buffer is full. Existing unread orders are preserved, and new orders can be accepted after space becomes available.
- Benchmark results: see `docs/benchmark_results.md`; they are single runs and vary widely between runs and machines.
- Shared file requirements: processes must use the same backing file, capacity, and binary record format.
- Performance scope: benchmark results depend on the machine and workload and do not guarantee production trading performance.

## 7. Future Work

- Connect TradeStore to the pipeline and measure its cost to the engine.
- Add automated tests for the curses layer.
- Measure low-load latency (current end-to-end numbers are a saturated pipeline).
- Investigate crash recovery and consistency after unexpected process termination.
- Remove O(n) list operations in the matching engine and re-measure.
