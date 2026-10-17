# ChronosMatch — Zero-Copy High-Frequency Trading Engine

## ROLE : Dataset Research and Market Simulator

My contribution to the project focuses on researching and inspecting the stock market dataset, checking its data quality, and developing a Python-based asynchronous market simulator that generates synthetic BUY and SELL orders.

### 1. Dataset Used

- **Dataset name:** NIFTY-50 Stock Market Data
- **Source:** [Kaggle — NIFTY-50 Stock Market Data](https://www.kaggle.com/datasets/rohanrao/nifty50-stock-market-data)
- **File name:** `NIFTY50_all.csv`
- **Format:** CSV
- **Total records:** 235,192
- **Unique stocks:** 65
- **Date range:** January 3, 2000 – April 30, 2021

### 2. Dataset Inspection and Cleaning

I inspected the dataset using Python and pandas to understand its structure and check data quality.

The relevant columns for the simulator are `Date`, `Symbol`, `Open`, `High`, `Low`, `Close`, `VWAP`, `Volume`, and `Trades`.

The checks confirmed that the main price and volume columns have no missing values, no invalid dates were detected, and no violations were found in the basic price consistency checks. The `Trades` column contains 114,848 missing values.

### 3. Market Simulator

I developed `src/simulator.py` using Python. The simulator loads the dataset, converts dates into datetime format, removes rows missing essential market values, and generates synthetic BUY and SELL orders.

Each generated order includes an order ID, timestamp, side, price, quantity, and stock symbol. The simulator uses `asyncio` to generate orders asynchronously.

### 4. Testing

I created `tests/test_simulator.py` to test dataset loading and order generation.

**Test result:** Both tests passed successfully using `pytest`.

### 5. Dataset Setup

The dataset is not included in the GitHub repository because the CSV file is excluded through `.gitignore`.

To run the simulator:

1. Download the dataset from the [Kaggle dataset page](https://www.kaggle.com/datasets/rohanrao/nifty50-stock-market-data?select=NIFTY50_all.csv).
2. Extract `NIFTY50_all.csv`.
3. Place it in the project's `data/` directory.

Expected file path: `data/NIFTY50_all.csv`

### 6. Dataset Limitation

The dataset contains daily stock summaries rather than actual high-frequency order events. Therefore, the simulator generates synthetic orders for testing; these orders are not historical exchange orders.