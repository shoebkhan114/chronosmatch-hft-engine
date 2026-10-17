# Dataset Report — ChronosMatch

## 1. Dataset Information

- **Dataset name:** NIFTY-50 Stock Market Data
- **File:** `NIFTY50_all.csv`
- **Format:** CSV
- **Total records:** 235,192
- **Unique stocks:** 65
- **Date range:** 2000-01-03 to 2021-04-30

## 2. Relevant Attributes

The selected attributes are Date, Symbol, Open, High, Low, Close, VWAP, Volume, and Trades.

- **Date:** Trading date.
- **Symbol:** Stock identifier.
- **Open:** Opening price for the day.
- **High:** Highest price for the day.
- **Low:** Lowest price for the day.
- **Close:** Closing price for the day.
- **VWAP:** Volume-weighted average price.
- **Volume:** Total shares traded during the day.
- **Trades:** Number of trades recorded, where available.

## 3. Data Quality Checks

- No invalid dates were detected.
- No missing values were found in Open, High, Low, Close, VWAP, or Volume.
- No violations were found in the checks comparing High, Low, Open, and Close.
- The Trades column contains 114,848 missing values.
- Deliverable Volume and %Deliverble each contain 16,077 missing values.

## 4. Limitations

This dataset contains daily stock summaries, not individual high-frequency order events. The simulator will generate synthetic BUY and SELL orders for testing, subject to the project's agreed design. These generated orders must not be described as actual historical orders.
