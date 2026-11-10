# Market Simulator Usage Guide

## 1. Overview

ChronosMatch provides two modes of market order generation:

- **Historical mode:** Generates BUY and SELL orders using stock market dataset records.
- **Synthetic mode:** Generates simulated orders using a random-walk price model without requiring a dataset.

Both modes generate orders asynchronously using Python `asyncio`.

## 2. Historical Data Mode

Historical mode uses the NIFTY 50 dataset.

```python
import asyncio
from src.simulator import MarketSimulator

async def main():
    simulator = MarketSimulator(
        dataset_path="data/NIFTY50_all.csv",
        symbol="RELIANCE"
    )

    async for order in simulator.generate_orders(delay=0):
        print(order)

asyncio.run(main())
```

The simulator filters the selected stock and generates orders from valid dataset rows.

### Historical Dataset Validation

Before generating orders, the simulator validates and prepares the historical dataset:

1. Converts the `Date` column into datetime format.
2. Filters records using the configured stock symbol.
3. Removes rows containing missing values in `Date`, `Open`, `High`, `Low`, `Close`, or `Volume`.
4. Raises a `ValueError` if no valid market data remains for the selected symbol.

Invalid date values that cannot be converted are rejected during datetime conversion.

This ensures that historical orders are generated only from valid dataset records.


## 3. Synthetic Random-Walk Mode

Synthetic mode generates orders without loading a CSV dataset.

```python
import asyncio
from src.simulator import MarketSimulator

async def main():
    simulator = MarketSimulator()

    async for order in simulator.generate_random_orders(
        count=1000,
        initial_price=1000.0,
        delay=0,
        seed=42
    ):
        print(order)

asyncio.run(main())
```

### Parameters

| Parameter | Description |
|---|---|
| count | Number of orders to generate |
| initial_price | Starting reference price |
| delay | Optional delay between orders |
| seed | Controls reproducible random generation |

Using the same seed and inputs produces the same random order data, excluding timestamps.

## 4. Input Validation

The simulator checks important input values:

- Order count must be at least 1.
- Initial price must be positive.
- Delay cannot be negative.

Invalid inputs raise a `ValueError`.

## 5. Asynchronous Execution

The simulator uses asynchronous generators to produce orders.

When delay is zero, synthetic generation periodically yields control to the event loop every 1,000 orders. This allows other asynchronous tasks to execute.

## 6. Important Limitation

Synthetic orders are generated for simulation and testing. They are not actual exchange orders or real-time market transactions.