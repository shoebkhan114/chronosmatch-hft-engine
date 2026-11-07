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
- `src/live_dashboard.py`, `src/live_snapshot.py`, `src/book_view.py`, `src/latency_stats.py`: live curses dashboard (separate consumer process sends snapshots through a queue; rolling median/p99/max latency; order book and recent trades). Run: `PYTHONPATH=. python -m src.live_dashboard 100000` (press q to quit).
- `benchmarks/`: ring buffer, multiprocess ring buffer, matching engine, end-to-end.
- `docs/`: architecture, benchmark results, dataset report, ring buffer failure modes.

## Quick start for reviewers

~~~bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q                                  # expect 70 passed, 1 skipped (no Cython build)
PYTHONPATH=. python -m src.live_dashboard 100000     # live curses dashboard, press q to quit
~~~

The dashboard uses synthetic random-walk orders and needs no dataset. Dataset mode needs a local `data/` folder (gitignored, not in the repo). Dashboard latency is end-to-end and includes queueing delay, so it is in milliseconds; the 50 us target is not achieved.

## Setup

~~~bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
~~~

Optional Cython build (needs a C compiler; Cython tests are skipped if it is not built). `setuptools` and `cython` are not in `requirements.txt`, so install them first:

~~~bash
pip install setuptools cython
python setup.py build_ext --inplace
~~~

## Tests

~~~bash
python -m pytest -q            # default run, slow test excluded
python -m pytest -m slow       # 1,000,000-order cross-process stress test
~~~

Last verified (fresh clone of `shoeb-lead`): 70 passed, 1 skipped, 1 deselected without the Cython build; 86 passed, 1 deselected with it (the 16 matching-engine tests are re-run on the Cython engine).

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
- Live dashboard, one manual run, 100,000 orders: about 94.7k orders/sec, end-to-end latency median about 4.6 ms (queueing included), 92,796 trades. Single run, not a target result.

Details and caveats: `docs/benchmark_results.md`.

## Targets are NOT achieved

100,000 orders/sec and under 50 microseconds matching are **targets, not results**. End-to-end runs have not reached them.

## Known limitations

- Ring buffer has no crash recovery and is not lock-free (see `docs/ring_buffer_failure_modes.md`).
- `get()` does not validate quantity or price; call `Order.validate()`.
- Matching engine uses O(n) list operations and mutates `Order.quantity` in place.
- The curses screen layer is not unit-tested (the data/formatting parts are) and was run manually only a few times. Dashboard latency is end-to-end and includes queueing delay in the ring buffer, so it is in milliseconds, not 50 us. `TradeStore` (SQLite) is implemented and unit-tested but not connected to the live pipeline, and its cost to the engine is not measured.

## Planned

Connecting `TradeStore` to the pipeline and measuring its cost; automated tests for the curses layer.

## Team

Shoeb Khan (lead), Ajay, Vighnesh, Likiteshwar.
