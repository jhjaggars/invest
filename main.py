import math
from collections import defaultdict
from itertools import cycle

import pandas as pd
import yfinance as yf
from rich import box
from rich.console import Console
from rich.table import Table

console = Console()


def extract_buy_days(data):
    dd = defaultdict(list)
    for ts in data.index:
        dd[(ts.year, ts.month)].append(ts)

    days = sorted(min(tss) for tss in dd.values())
    return data.T[days].T.Close

def extract_field(data, field):
    fs = data[field]
    return fs[(fs.T != 0.0).any()]

def get_data(symbols, start=None, end=None):
    data = yf.download(symbols, start=start, end=end, actions=True, progress=False)
    data.dropna(inplace=True)
    # yf returns a regular index if there is only one ticker
    if len(symbols) == 1:
        data.columns = pd.MultiIndex.from_tuples(zip(data.columns, cycle(symbols)))
    return data

def main(buy_amount=1000, start=None, end=None, symbols=(), one_buy=False):
    data = get_data(symbols, start=start, end=end)
    buys = extract_buy_days(data)
    divs = extract_field(data, "Dividends")
    splits = extract_field(data, "Stock Splits")
    div_prices = data.T[divs.index].T.Close
    all_days = sorted(set(buys.index) | set(divs.index) | set(splits.index))

    shares = dict.fromkeys(symbols, 0)
    bought = False

    for day in all_days:
        if day in buys.index and not bought:
            for symbol, price in data.loc[day].Close.items():
                shares[symbol] = shares.get(symbol, 0) + (float(buy_amount / price))

        if one_buy:
            bought = True

        if day in divs.index:
            for symbol, amt in divs.loc[day].items():
                v = shares[symbol] * amt
                price = div_prices[symbol][day]
                shares[symbol] = shares.get(symbol, 0) + (float(v / price))

        if day in splits.index:
            for symbol, amt in splits.loc[day].items():
                if amt != 0.0:
                    shares[symbol] = shares.get(symbol, 0) * amt

    final_day = max(data.index)
    years = len(buys) / 12
    total_invested = buy_amount if one_buy else buy_amount * len(buys)

    console.print(f"Start date: {min(data.index)}")
    console.print(f"Total Invested: ${total_invested:,}")

    table = Table(show_header=True, header_style="bold magenta", box=box.MINIMAL_HEAVY_HEAD)
    table.add_column("Symbol")
    table.add_column("Value", justify="right")
    table.add_column("ROI", justify="right")
    table.add_column("CAGR", justify="right")

    for symbol, price in data.loc[final_day].Close.items():
        value = shares[symbol] * price
        roi = int(100 * ((value - total_invested)/ total_invested))
        ann_ret = 100 * (math.pow(value / total_invested, 1 / years) - 1)
        fvalue = f"${value:,.2f}"
        table.add_row(
            symbol,
            fvalue,
            f"{roi:.2f}%",
            f"{ann_ret:.2f}%"
        )

    console.print(table)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("tickers", metavar="TICKER", nargs="+")
    p.add_argument("--start", metavar="S", default=None)
    p.add_argument("--end", metavar="E", default=None)
    p.add_argument("--principal", metavar="P", type=int, default=1000)
    p.add_argument("--one-buy", action="store_true", default=False)
    args = p.parse_args()
    main(symbols=args.tickers, start=args.start, end=args.end, buy_amount=args.principal, one_buy=args.one_buy)
