# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Python-based investment simulator that calculates returns for dollar-cost averaging strategies. It uses yfinance to fetch historical stock data and simulates regular investments with automatic dividend reinvestment and stock split handling.

## Commands

### Setup and Dependencies
```bash
# Install dependencies using Poetry
poetry install

# Update dependencies
poetry update
```

### Running the Simulator
```bash
# Basic usage with one or more tickers
poetry run python main.py AAPL MSFT

# With custom parameters
poetry run python main.py AAPL --start 2020-01-01 --end 2023-12-31 --principal 5000

# One-time purchase instead of dollar-cost averaging
poetry run python main.py AAPL --one-buy --principal 10000
```

### Command-line Arguments
- `TICKER(s)`: Stock symbols (required, can specify multiple)
- `--start`: Start date for simulation (format: YYYY-MM-DD)
- `--end`: End date for simulation (format: YYYY-MM-DD)
- `--principal`: Investment amount per period (default: $1000)
- `--one-buy`: Make single initial purchase instead of periodic investments
- `--frequency`: Investment frequency (not fully implemented)

## Architecture

The entire application is contained in `main.py` with these key components:

- **get_data()**: Fetches historical data using yfinance, handles both single and multiple tickers
- **extract_buy_days()**: Determines investment dates (monthly by default)
- **extract_field()**: Extracts dividend and split events from data
- **main()**: Core simulation logic that:
  1. Processes buy transactions on investment dates
  2. Reinvests dividends automatically
  3. Adjusts share counts for stock splits
  4. Calculates final portfolio metrics (ROI, CAGR)

The simulator tracks shares and dividends per symbol, then displays results in a formatted table showing value, shares, ROI, CAGR, and dividend yield for each holding.