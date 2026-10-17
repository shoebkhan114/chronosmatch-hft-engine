# ChronosMatch Architecture

## 1. Project Objective

ChronosMatch is a high-performance limit order book engine designed to simulate buy and sell orders, transfer order messages between processes, execute matching logic, and measure throughput and latency.

## 2. Main Components

1. Market Simulator — generates valid order events using Python asyncio.
2. Shared-Memory Ring Buffer — transfers binary messages using mmap and struct.
3. Matching Engine — matches compatible orders using price-time priority.
4. Terminal Dashboard — displays order activity, trades, throughput, and latency.
5. Benchmarking and Tests — validates correctness and measures actual performance.

## 3. Data Flow

Market Simulator → Shared-Memory Ring Buffer → Matching Engine → Metrics and Terminal Dashboard

## 4. Development Principles

- Each member works on their assigned Git branch.
- Modules use an agreed common order schema.
- Correctness tests come before optimization.
- Performance claims must be supported by repeatable benchmarks.
- Branches are not merged into main until the review requirements are confirmed.

## 5. Current Status

- Initial repository and branch setup completed.
- Common Order model implemented with validation.
- Fixed-capacity mmap-based ring buffer prototype implemented using struct-based binary order records.
- Single-process ring buffer tests cover empty, full, FIFO, put/get, and wrap-around behavior.
- Separate producer-consumer process communication tested with 100 orders.
- All 13 current automated tests pass.
- High-throughput benchmarking, crash recovery, and broader concurrency testing remain pending.