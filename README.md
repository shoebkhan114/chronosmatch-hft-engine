# ChronosMatch: Zero-Copy High-Frequency Trading Engine (simulated prototype)

Internship project (Infotact Solutions, Python Development, Batch-22). This is a **simulated prototype for learning, not a real exchange**.

"Zero-Copy" is the project's original name from the brief. The implementation uses **shared-memory IPC without pickling** (a memory-mapped ring buffer). It is not true zero-copy.

## What is built

- `src/models.py`: common `Order` model (`Side`, `OrderType`), integer price ticks (1 tick = Rs 0.01).
- `src/ring_buffer.py`: file-backed mmap ring buffer, fixed 30-byte records (`<QqBQIB`), 24-byte header, shared `multiprocessing` lock. `put()` returns `False` when full; `get()` returns `None` when empty.
- `src/matching_engine.py`: Python matching engine with price-time priority (LIMIT orders; MARKET orders are rejected).
- `src/matching_engine_cy.pyx`: Cython version of the engine (optional build).
- `src/simulator.py`: asyncio order simulator (NIFTY-50 dataset mode and seeded random-walk mode).
- `src/dashboard.py`: manual command-line demo (not a curses dashboard).
- `src/trade_store.py`: SQLite trade store with a background writer thread (not yet integrated into the pipeline).
- `benchmarks/`: ring buffer, multiprocess ring buffer, matching engine, end-to-end.
- `docs/`: architecture, benchmark results, dataset report, ring buffer failure modes.

## Setup

~~~bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
~~~

Optional Cython build (Cython tests are skipped if it is not built):

~~~bash
python setup.py build_ext --inplace
~~~

## Tests

~~~bash
python -m pytest -q            # default run, slow test excluded
python -m pytest -m slow       # 1,000,000-order cross-process stress test
~~~

Last verified: 69 passed, 1 deselected (slow test).

## Benchmarks (single runs on one noisy laptop)

1M-order cross-process ring buffer benchmark (ring buffer only):

~~~bash
PYTHONPATH=. python -c "import benchmarks.benchmark_multiprocess_ring_buffer as b; b.ORDER_COUNT = 1_000_000; b.PROCESS_TIMEOUT = 300; b.main()"
~~~

Other benchmark scripts are in `benchmarks/`.

Measured so far (single runs; run-to-run variance is large, so no single number is representative):

- Ring buffer, 1M orders cross-process, FIFO verified: about 115k to 300k orders/sec across three runs.
- End-to-end (producer, ring buffer, engine, 2 processes, 100k synthetic orders): about 39k to 92k orders/sec in 5 runs.
- Matching engine only: median add_order a few microseconds.
- Cython vs Python, engine-only: about 35 to 43% faster in 3 sessions (not isolated, not end-to-end).

Details and caveats: `docs/benchmark_results.md`.

## Targets are NOT achieved

100,000 orders/sec and under 50 microseconds matching are **targets, not results**. End-to-end runs have not reached them.

## Known limitations

- Ring buffer has no crash recovery and is not lock-free (see `docs/ring_buffer_failure_modes.md`).
- `get()` does not validate quantity or price; call `Order.validate()`.
- Matching engine uses O(n) list operations and mutates `Order.quantity` in place.
- No live curses dashboard. `TradeStore` (SQLite) is implemented and unit-tested but not connected to the live pipeline, and its cost to the engine is not measured. perf_counter_ns timing exists only inside the end-to-end benchmark, not in a live monitor.

## Planned

Curses live dashboard with latency panel, connecting `TradeStore` to the pipeline and measuring its cost, live latency metrics.

## Team

Shoeb Khan (lead), Ajay, Vighnesh, Likiteshwar.
