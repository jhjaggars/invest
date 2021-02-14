from collections import defaultdict
import pandas as pd
import yfinance as yf
from itertools import cycle

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

def main(buy_amount=1000, start=None, end=None, symbols=()):
    data = get_data(symbols, start=start, end=end)
    buys = extract_buy_days(data)
    divs = extract_field(data, "Dividends")
    splits = extract_field(data, "Stock Splits")
    div_prices = data.T[divs.index].T.Close
    all_days = sorted(set(buys.index) | set(divs.index) | set(splits.index))

    shares = dict.fromkeys(symbols, 0)

    for day in all_days:
        if day in buys.index:
            for symbol, price in data.loc[day].Close.items():
                shares[symbol] = shares.get(symbol, 0) + (float(buy_amount / price))

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
    total_invested = buy_amount * len(buys)
    print(f"Start date: {min(data.index)}")
    print(f"Total Invested: ${total_invested:,}")
    for symbol, price in data.loc[final_day].Close.items():
        value = shares[symbol] * price
        roi = int(100 * (value / total_invested))
        fvalue = f"${value:,.2f}"
        print(f"{symbol:>5} {fvalue:>20} {roi:>6,}%")

if __name__ == "__main__":
    import sys
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("tickers", metavar="TICKER", nargs="+")
    p.add_argument("--start", metavar="S", default=None)
    p.add_argument("--end", metavar="E", default=None)
    args = p.parse_args() 
    main(symbols=args.tickers, start=args.start, end=args.end)