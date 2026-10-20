# ChronosMatch Architecture

## 1. Project Objective

ChronosMatch is a high-performance limit order book engine designed to simulate buy and sell orders, transfer order messages between processes, execute matching logic, and measure throughput and latency.

## 2. Main Components

1. Market Simulator - generates valid order events using Python asyncio.
2. Shared-Memory Ring Buffer - transfers binary messages using mmap and struct.
3. Matching Engine - matches compatible orders using price-time priority.
4. Terminal Dashboard - displays order activity, trades, throughput, and latency.
5. Benchmarking and Tests - validates correctness and measures performance.

## 3. Data Flow

Market Simulator -> Shared-Memory Ring Buffer -> Matching Engine -> Metrics and Terminal Dashboard

## 4. Development Principles

- Each member works on their assigned Git branch.
- Modules use an agreed common order schema.
- Correctness tests come before optimization.
- Performance claims must be supported by repeatable benchmarks.
- Branches are not merged into main until review requirements are confirmed.

## 5. Current Status

- Common Order model implemented with validation.
- Fixed-capacity mmap-based ring buffer implemented using struct-based binary order records.
- Single-process ring buffer tests cover empty, full, FIFO, put/get, and wrap-around behavior.
- Producer-consumer process communication covered by an integration test.
- Cross-process producer-consumer benchmark completed with 100,000 orders.
- Latest automated test run: 32 tests passed.
- Measured benchmark throughput: approximately 172,489 orders/second on the current machine and workload.

## 6. Ring Buffer Limitations

- External synchronization: independent processes must share the same multiprocessing-compatible lock. The default threading lock is not sufficient for process synchronization.
- No crash recovery: unexpected process termination during an operation may leave the buffer in an inconsistent state; automatic recovery is not implemented.
- Fixed capacity: new orders are rejected when the buffer is full until space becomes available.
- Shared file requirements: processes must use the same backing file, capacity, and binary record format.
- Performance scope: benchmark results depend on the machine and workload and do not guarantee production trading performance.

## 7. Future Work

- Investigate crash recovery and consistency after unexpected process termination.
- Expand concurrency and failure-handling tests.
- Repeat benchmarks with different capacities and workloads.
- Optimize further after correctness and repeatability are established.
