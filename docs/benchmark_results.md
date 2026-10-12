
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
