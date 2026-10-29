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

## End-to-end pipeline (producer -> ring buffer -> engine, 2 processes)
- Scope: synthetic seeded random-walk LIMIT orders (not the NIFTY dataset), 100,000 orders, 92,796 trades, ring buffer capacity 1,024, spawn context with shared lock, FIFO order verified in the consumer. Python 3.12.3, x86_64 Linux, one laptop (Inspiron 15 3520). Five single runs, same machine, not controlled for CPU frequency or background load.
- Consumer-window throughput across runs: 38,740 / 42,813 / 50,357 / 64,182 / 92,030 orders/sec. The spread is about 2.4x, so no single number is representative.
- Engine-only add_order median: 9.12 / 9.14 / 6.65 / 6.34 / 4.54 us.
- Ring buffer get() median (includes lock wait; runs 2-5 only): 9.34 / 6.11 / 6.36 / 3.81 us.
- End-to-end latency (producer timestamp to after add_order) median: 25,668 / 22,573 / 18,616 / 15,430 / 9,649 us (about 10 to 26 ms), p99 about 32 to 76 ms. The producer is faster than the consumer, so the buffer stays nearly full and this number is mostly queueing delay in a saturated pipeline, not processing time at low load.
- Targets: 100,000 orders/sec was NOT achieved (best single run 92,030). Under 50 us end-to-end was NOT achieved (medians are in the milliseconds).
- Reading: get() and add_order take similar time per order, so speeding up only one of them would not reach the throughput target by itself. This is inferred from medians, not from a profiler.
- Command: `PYTHONPATH=. python benchmarks/benchmark_end_to_end.py`

## Not measured yet
- Low-load end-to-end latency (the end-to-end run above is a saturated pipeline).
- The 100,000 orders/sec and under-50 us targets were NOT achieved end-to-end in the runs above.
