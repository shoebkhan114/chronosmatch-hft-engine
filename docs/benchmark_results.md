

# ChronosMatch Python Benchmark Baseline

## Environment
- Python: 3.13.5
- Implementation: Python
- Benchmark date: 2026-10-12

## Workload A: Buy-only order insertion
- Order submissions: 10,000
- Elapsed time: 7.290808 seconds
- Throughput: 1,372 orders/second

## Workload B: Immediate matching
- Order submissions: 20,000
- Completed trades: 10,000
- Elapsed time: 0.041468 seconds
- Throughput: 482,303 order submissions/second

## Notes
- These are preliminary single-run measurements.
- The workloads exercise different code paths and are not directly comparable.
- Repeat runs and profiling are required before optimization.

# Benchmark Results (shoeb-lead)

Machine: Inspiron 15 3520, Linux x86_64, Python 3.12.3.
All numbers are single runs. Do not compare different workloads.

## Ring buffer, single process (put/get)
- 100,000 orders, ~256,602 orders/sec (earlier recorded run)
- Command: `PYTHONPATH=. python benchmarks/benchmark_ring_buffer.py`

## Ring buffer, cross-process producer/consumer
- 100,000 sent, 100,000 received, ~166,498 orders/sec
- Shared multiprocessing lock, capacity 1024
- Command: `PYTHONPATH=. python benchmarks/benchmark_multiprocess_ring_buffer.py`

## Matching engine, in-memory (no ring buffer)
- Immediate trades (small book): ~376,981 orders/sec
- Growing book (BUY only), before optimization (list.sort per insert): ~10,199 orders/sec at 1,000 orders, ~1,032 orders/sec at 10,000 orders
- Growing book (BUY only), after bisect.insort (commit 7d2e785): ~300,982 orders/sec at 1,000 orders, ~134,001 orders/sec at 10,000 orders (single run)
- add_order latency, immediate-trade workload: median 1.46 us, p99 2.80 us, p99.9 40.44 us, max 1,178.99 us
- Command: `PYTHONPATH=. python benchmarks/benchmark_matching_engine.py`
- Cause of the original slowdown: the book list was re-sorted on every insert. insort removes that; mid-list insert is still O(n), so throughput still falls as the book grows.

## Not measured yet
- End-to-end order-to-trade latency (ring buffer + engine together).
- The 100,000 orders/sec and under-50 us targets are NOT proven end-to-end.

