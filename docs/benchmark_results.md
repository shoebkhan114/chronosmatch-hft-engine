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
- Growing book (BUY only): ~10,199 orders/sec at 1,000 orders, ~1,032 orders/sec at 10,000 orders
- add_order latency, immediate-trade workload: median 1.46 us, p99 2.80 us, p99.9 40.44 us, max 1,178.99 us
- Command: `PYTHONPATH=. python benchmarks/benchmark_matching_engine.py`
- Cause of growing-book slowdown: the book list is re-sorted on every insert.

## Not measured yet
- End-to-end order-to-trade latency (ring buffer + engine together).
- The 100,000 orders/sec and under-50 us targets are NOT proven end-to-end.
