import math
from collections import defaultdict
from itertools import cycle

import pandas as pd
import yfinance as yf
from rich import box
from rich.console import Console
from rich.table import Table

console = Console()

def _default_grouper(ts):
    return (ts.year, ts.month)

def extract_buy_days(data, grouper=_default_grouper):
    dd = defaultdict(list)
    for ts in data.index:
        dd[grouper(ts)].append(ts)

    days = sorted(min(tss) for tss in dd.values())
    return data['Close'].loc[days]

def extract_field(data, field):
    fs = data[field]
    return fs[(fs.T != 0.0).any()]

def get_data(symbols, start=None, end=None):
    data = yf.download(symbols, start=start, end=end, actions=True, progress=False, auto_adjust=True)
    data.dropna(inplace=True)
    return data

def main(buy_amount=1000, start=None, end=None, symbols=(), one_buy=False, frequency=None):
    data = get_data(symbols, start=start, end=end)

    grouper = _default_grouper
    if frequency == "D":
        grouper = lambda ts: (ts.year, ts.month, ts.day)

    buys = extract_buy_days(data, grouper=grouper)
    divs = extract_field(data, "Dividends")
    splits = extract_field(data, "Stock Splits")
    div_prices = data['Close'].loc[divs.index]
    all_days = sorted(set(buys.index) | set(divs.index) | set(splits.index))

    shares = dict.fromkeys(symbols, 0)
    dividends = dict.fromkeys(symbols, 0)
    bought = False

    for day in all_days:
        if day in buys.index and not bought:
            for symbol, price in data['Close'].loc[day].items():
                amt = float(buy_amount / price)
                shares[symbol] = shares.get(symbol, 0) + amt

        if one_buy:
            bought = True

        if day in divs.index:
            for symbol, amt in divs.loc[day].items():
                v = shares[symbol] * amt
                price = div_prices[symbol][day]
                samt = v / price
                dividends[symbol] = dividends.get(symbol, 0) + v
                shares[symbol] = shares.get(symbol, 0) + samt

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
    table.add_column("Shares", justify="right")
    table.add_column("ROI", justify="right")
    table.add_column("CAGR", justify="right")
    table.add_column("Div Yield", justify="right")

    results = []
    for symbol, price in data['Close'].loc[final_day].items():
        value = shares[symbol] * price
        roi = int(100 * ((value - total_invested)/ total_invested))
        ann_ret = 100 * (math.pow(value / total_invested, 1 / years) - 1)
        fvalue = f"${value:,.2f}"
        dvalue = f"${dividends[symbol]:.2f}"
        results.append((
            symbol,
            fvalue,
            shares[symbol],
            roi,
            ann_ret,
            dvalue
        ))

    for r in sorted(results, key=lambda x: x[4]):
        table.add_row(r[0], r[1], f"{r[2]:.2f}", f"{r[3]:.2f}%", f"{r[4]:.2f}%", r[5])
    console.print(table)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("tickers", metavar="TICKER", nargs="+")
    p.add_argument("--start", metavar="S", default=None)
    p.add_argument("--end", metavar="E", default=None)
    p.add_argument("--principal", metavar="P", type=int, default=1000)
    p.add_argument("--one-buy", action="store_true", default=False)
    p.add_argument("--frequency", metavar="F", default=None)
    args = p.parse_args()
    main(symbols=args.tickers, start=args.start, end=args.end, buy_amount=args.principal, one_buy=args.one_buy, frequency=None)
