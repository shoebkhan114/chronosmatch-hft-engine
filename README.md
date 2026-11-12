# ChronosMatch

**A simulated high-frequency trading engine in Python and Cython: shared-memory IPC, a price-time-priority matching engine, and a live terminal dashboard.**

![Python](https://img.shields.io/badge/python-3.12-blue)
![Tests](https://img.shields.io/badge/tests-95%20passed%20%7C%20111%20with%20Cython-brightgreen)
![Status](https://img.shields.io/badge/status-final%20prototype-informational)

ChronosMatch was built as Project 2 of the Infotact Solutions Python Development Internship (Batch-22). It is a **learning prototype, not a real exchange**. The project name comes from the original brief ("Zero-Copy"); the implementation uses **shared-memory IPC without pickling** and is **not** true zero-copy (see [Design notes](#design-notes)).

## Project Materials

| Material | Link |
|---|---|
| Demo video | [VIDEO](https://drive.google.com/file/d/1wyo30s4JrjM8qChjB9qNEvFCYA816kwd/view?usp=drive_link) |
| Project report | [REPORT](https://drive.google.com/file/d/1Ax7gEBfa54XP3xYcdapDwPq3bUUQ9kBJ/view?usp=drive_link) |
| Presentation (PPT) | [PPT](https://docs.google.com/presentation/d/1mE8VyLcKL0Xwq-w75vavGM9FiqUfYg6X/edit?usp=drive_link&ouid=102686431428325278595&rtpof=true&sd=true) |
| Architecture notes | [docs/architecture.md](docs/architecture.md) |
| Benchmark results | [docs/benchmark_results.md](docs/benchmark_results.md) |
| Ring buffer failure modes | [docs/ring_buffer_failure_modes.md](docs/ring_buffer_failure_modes.md) |

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Live Dashboard](#live-dashboard)
5. [Testing](#testing)
6. [Benchmarks and Results](#benchmarks-and-results)
7. [Targets vs Results](#targets-vs-results)
8. [Design Notes](#design-notes)
9. [Known Limitations](#known-limitations)
10. [Running on Windows](#running-on-windows)
11. [Project Structure](#project-structure)
12. [Roadmap](#roadmap)
13. [Team](#team)

## Features

- **Shared-memory ring buffer:** file-backed `mmap` with fixed 30-byte binary records (`struct`), so two processes exchange orders without pickling.
- **Matching engine:** limit orders, price-time priority, partial fills, duplicate-ID rejection. A Cython version is included (optional build).
- **Market simulator:** `asyncio` order generator with a NIFTY-50 dataset mode and a seeded random-walk mode (reproducible runs).
- **Live curses dashboard:** side-by-side BUY/SELL book, spread line, whale marker (quantity >= 90), and rolling end-to-end latency (median, p99, max).
- **Latency graph:** press `g` to open a live matplotlib window in a separate process.
- **Trade ledger:** matched trades flushed to SQLite by a background thread.
- **Measurement tools:** `perf_counter_ns` timing, end-to-end and engine-only benchmarks, a GC on/off experiment runner.

## Architecture

```
Producer process -> Ring buffer (mmap file) -> Consumer process -> Snapshot queue -> Curses dashboard
                                                (matching engine            (main process)
                                                 + latency window)
                                                       |
                                                       +--> SQLite trade store (background thread)
```

1. The producer creates limit orders, stamps each with `perf_counter_ns`, and writes a 30-byte record to the ring buffer under a shared lock. If the buffer is full, `put()` returns `False` and the producer retries.
2. The consumer reads records with `get()`, runs `MatchingEngine.add_order()`, and measures latency as the time after matching minus the order timestamp.
3. About every 100 ms the consumer builds a snapshot (book, spread, trades, latency) and puts it on a small queue. If the queue is full the snapshot is dropped, so the engine never waits for the screen.
4. The main process draws the latest snapshot with `curses`. Key `g` starts a separate matplotlib process that reads a latency CSV.

**Order model:** `order_id`, `timestamp_ns`, `side` (BUY=1, SELL=2), `price_ticks`, `quantity`, `order_type` (LIMIT=1, MARKET=2). One tick equals Rs 0.01 and prices are stored as integers to avoid floating-point error.

## Quick Start

Requirements: Python 3.12, Linux (tested on Ubuntu).

```bash
git clone https://github.com/shoebkhan114/chronosmatch-hft-engine.git
cd chronosmatch-hft-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q                      # expect 95 passed, 1 skipped
PYTHONPATH=. python -m src.live_dashboard 100000
```

Optional Cython build (needs a C compiler). `setuptools` and `cython` are not in `requirements.txt`:

```bash
pip install setuptools cython
python setup.py build_ext --inplace
python -m pytest -q                      # 16 more tests run; 111 passed
```

Dataset mode needs a local NIFTY-50 CSV in `data/` (gitignored and not included in this repository). The dashboard uses synthetic random-walk orders and needs no dataset.

## Live Dashboard

```bash
PYTHONPATH=. python -m src.live_dashboard 100000            # live dashboard
PYTHONPATH=. python -m src.live_dashboard 100000 trades.db  # also flush trades to SQLite
```

| Key | Action |
|---|---|
| `g` | Open or close the live latency graph (separate process) |
| `q` | Quit (also closes the graph) |

Use `q` to quit; do not suspend with Ctrl+Z. The latency shown is **end-to-end** (producer timestamp to after matching) and includes queueing delay in the ring buffer, so it is measured in milliseconds, not microseconds.

## Testing

```bash
python -m pytest -q          # default run (slow test excluded)
python -m pytest -m slow     # 1,000,000-order cross-process stress test
```

| Environment | Result |
|---|---|
| Fresh clone, no Cython build | 95 passed, 1 skipped, 1 deselected |
| Developer machine with Cython build | 111 passed, 1 deselected |

Coverage includes the order model, ring buffer (including corrupted fields), matching engine (Python and Cython), simulator, snapshot and book views, latency statistics, trade store, and multi-process integration tests. The curses screen and the matplotlib window are verified manually, not by automated tests.

## Benchmarks and Results

All figures are **single runs on one noisy laptop**. Run-to-run variation was large (up to about 2.6x), so no single number is representative. Full details and caveats are in [docs/benchmark_results.md](docs/benchmark_results.md).

| Measurement | Result |
|---|---|
| Ring buffer, 1M orders cross-process (3 runs, FIFO verified) | about 115k to 300k orders/sec |
| Matching engine alone, small book | about 380k orders/sec, `add_order` median about 1.5 us |
| End-to-end: producer, ring buffer, engine (5 runs) | 38.7k to 92k orders/sec |
| End-to-end median latency | 9.6 to 25.7 ms (saturated pipeline, mostly queueing) |
| Engine-only median latency | 4.5 to 9 us |
| Cython vs Python, engine-only (3 sessions) | about 35 to 43% faster (not isolated, not measured end to end) |
| GC on vs off, 10 alternating rounds | no clear effect (78.8k vs 80.8k orders/sec) |
| Live dashboard run, 100,000 orders | about 94.7k orders/sec, 92,796 trades; SQLite stored 92,796 |

Run the benchmarks:

```bash
PYTHONPATH=. python benchmarks/benchmark_end_to_end.py
PYTHONPATH=. python benchmarks/benchmark_matching_engine.py
python benchmarks/run_gc_experiment.py
```

## Targets vs Results

| Target from the brief | Result |
|---|---|
| 100,000 orders/sec | **Not achieved** end to end (best single runs about 92k to 96k) |
| Under 50 us matching | **Not achieved** end to end; engine-only median is a few microseconds, but end-to-end latency is in milliseconds |
| Cython C-level optimization, no GC pauses in the loop | **Not done**; Cython gain is engine-only, and the GC experiment showed no clear effect |
| Background process for the SQLite flush | Implemented as a **thread**, not a process; its cost was not measured |

## Design Notes

- **Not true zero-copy.** Records are read from shared memory without pickling, but unpacking creates a Python `Order` object, so data is copied.
- **Locking.** Both processes must share the same `multiprocessing` lock; a default threading lock does not protect across processes. The buffer is not lock-free.
- **Full buffer.** `put()` returns `False` without overwriting unread records; there is no automatic backpressure.
- **Trade price.** A trade executes at the resting order's price.
- **Book structure.** Sorted lists via `bisect.insort`; the best order is at index 0.
- **Snapshots.** The dashboard queue drops snapshots when full so the engine never blocks.

## Known Limitations

- No crash recovery in the ring buffer; `get()` advances the read position before building the order, and does not validate quantity or price (call `Order.validate()`).
- Matching engine uses O(n) list operations (`pop(0)`, mid-list insert), mutates `Order.quantity` in place, and supports LIMIT orders only (MARKET raises `NotImplementedError`). Single symbol per run.
- SQLite flush and CSV export costs were not measured.
- Tested on Ubuntu. Native Windows is untested.

See [docs/ring_buffer_failure_modes.md](docs/ring_buffer_failure_modes.md) for details.

## Running on Windows

Windows steps have **not been tested**. WSL2 is recommended.

**Option A (recommended): WSL2 + VS Code.** Run `wsl --install -d Ubuntu` in an administrator PowerShell, install the VS Code "WSL" extension, then follow the Linux commands in [Quick Start](#quick-start) inside Ubuntu. The graph window needs Windows 11 (WSLg).

**Option B: native Windows (PowerShell).** Needs Python 3.12 and Git.

```powershell
git clone https://github.com/shoebkhan114/chronosmatch-hft-engine.git
cd chronosmatch-hft-engine
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install windows-curses
python -m pytest -q
$env:PYTHONPATH="."; python -m src.live_dashboard 100000
```

- If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope Process Bypass` and activate again.
- `windows-curses` is not in `requirements.txt`; it provides `curses` on Windows.
- The ring buffer uses a file-backed mmap, which Windows handles differently; some tests may fail there.
- Cython tests are skipped without a C compiler (Visual Studio Build Tools).

## Project Structure

```
src/
  models.py               Order model, Side, OrderType
  ring_buffer.py          mmap ring buffer (30-byte records, shared lock)
  matching_engine.py      Python matching engine
  matching_engine_cy.pyx  Cython matching engine (optional build)
  simulator.py            asyncio simulator (dataset and random-walk modes)
  trade_store.py          SQLite trade store with background writer thread
  live_dashboard.py       Curses dashboard and consumer process
  live_snapshot.py        Snapshot builder
  book_view.py            Side-by-side book, spread, whale marker
  latency_stats.py        Rolling median / p99 / max
  latency_io.py           Latency CSV helpers
  latency_plot.py         Live matplotlib graph
  dashboard.py            Simple print()/input() CLI demo
benchmarks/               Ring buffer, matching engine, end-to-end, GC experiment
tests/                    Unit and integration tests
docs/                     Architecture, benchmark results, dataset report, failure modes
setup.py                  Cython build
pytest.ini                Test configuration (slow marker)
requirements.txt          Pinned dependencies
```

## Roadmap

- Replace list operations with price levels or deques and re-measure.
- Rewrite the matching loop with `cdef` types and measure end to end.
- Measure low-load latency (current end-to-end numbers come from a saturated pipeline).
- Move the SQLite flush to a separate process and measure its cost.
- Add automated tests for the curses layer and crash recovery for the ring buffer.

## Team

| Member | Contribution |
|---|---|
| Shoeb Khan (team leader) | Architecture, order model, ring buffer, matching engine, Cython, integration, live dashboard, benchmarks, documentation |
| Ajay | Ring buffer and IPC tests, 1M-order stress test, failure-modes document |
| Vighnesh | Dataset preparation and asyncio simulator (seeded generation) |
| Likiteshwar | Matching engine tests and the initial CLI dashboard |

Built during the Infotact Solutions Python Development Internship, Batch-22.
