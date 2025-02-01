import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import requests
import Tools
from dotenv import load_dotenv
import os
import numpy as np
import math

load_dotenv() 
api_key = os.getenv('ALPHA_KEY')

p = {
    "starting_capital": 1000000000,
    "capital_invested_per_year": 0.2,
    "max_portfolio": 20,
    "stock_purchases_per_quarter": 20, # 20 works well
    "stock_shorts_per_quarter": 0,
    "starting_quarter": "2014-03-31",
    "roic_lower_threshold": 0.25
}

capital = p["starting_capital"]
holdings = [] # list of dicts: name, date purchased, amount of stock, shorting T/F
results = pd.DataFrame(columns=["portfolio value"])

roic_ey_df = pd.read_csv("roic_ey.csv", index_col="fiscalDateEnding")
prices_df = pd.read_csv("prices_edited.csv", index_col="fiscalDateEnding")

# print(prices_df["CTBB_price"])
# print(roic_ey_df["CTBB_ey"])

for quarter in range(roic_ey_df.index.get_loc(p["starting_quarter"]), -1, -1):

    quarter_string = roic_ey_df.index[quarter]
    quarterly_capital = 0

    roic_cols = [col for col in roic_ey_df.columns if "roic" in col]

    roic = roic_ey_df.iloc[quarter][roic_cols].dropna().sort_values(ascending=False)
    prospects_names = [name.replace("_roic", "") for name in roic[roic > p["roic_lower_threshold"]].index]

    # for prospect in prospects_names:
    #     print(prospect)
    #     print(prices_df.loc[quarter_string][f"{prospect}_price"])

    ey_cols = [col for col in roic_ey_df.columns if "ey" in col and col.replace("_ey", "") in prospects_names]
    ey = roic_ey_df.iloc[quarter][ey_cols].dropna().sort_values(ascending=False)

    picks = ey.head(p["stock_purchases_per_quarter"])

    if capital > 0:
        quarterly_capital = p["starting_capital"] * p["capital_invested_per_year"] / 4
        capital -= quarterly_capital

    # for h in holdings:
    #     if dt.datetime.strptime(quarter_string, "%Y-%m-%d") - dt.datetime.strptime(h["date"], "%Y-%m-%d") > dt.timedelta(days=360):
    #         quarterly_capital += h["amount"] * prices_df.loc[quarter_string][f"{h['ticker']}_price"]
    #         # quarterly_capital += h["amount"] * Tools.get_price_request(quarter_string, h['ticker'])
    #         holdings.remove(h)

    # Calculate value of sellings 
    for h in list(holdings):
        purchase_date = dt.datetime.strptime(h["date"], "%Y-%m-%d")
        current_date = dt.datetime.strptime(quarter_string, "%Y-%m-%d")
        if (current_date - purchase_date) > dt.timedelta(days=360):
            stock = h["ticker"]
            # Check if price exists and is not NaN
            if f"{stock}_price" not in prices_df.columns or pd.isna(prices_df.loc[quarter_string, f"{stock}_price"]):
                try:
                    cost = Tools.get_price_request(quarter_string, stock)
                    quarterly_capital += h["amount"] * cost
                    prices_df.loc[quarter_string, f"{stock}_price"] = cost
                    holdings.remove(h)
                except:
                    print(f"Warning: Missing price for {stock} in {quarter_string}. Holding not sold.")
                    continue
                continue
            quarterly_capital += h["amount"] * prices_df.loc[quarter_string, f"{stock}_price"]
            holdings.remove(h)

    # print(picks)

    for stock in [p.replace("_ey", "") for p in picks.index]:
        holdings.append({
            "ticker": stock,
            "date": quarter_string,
            "amount": (quarterly_capital / p["stock_purchases_per_quarter"]) / prices_df.loc[quarter_string][f"{stock}_price"]
            # "amount": (quarterly_capital / p["stock_purchases_per_quarter"]) / Tools.get_price_request(quarter_string, stock)
        })

    # print([[h["ticker"], h["amount"] * prices_df.loc[quarter_string][f"{h['ticker']}_price"] / 10000000.0, prices_df.loc[quarter_string][f"{h['ticker']}_price"]] for h in holdings], end="\n\n")

    # Calculate new total value
    # value = sum([h["amount"] * prices_df.loc[quarter_string][f"{h['ticker']}_price"] for h in holdings]) + capital
    current_value = 0
    for h in holdings:
        stock = h["ticker"]
        if f"{stock}_price" not in prices_df.columns:
            continue  # Skip if price column missing
        price = prices_df.loc[quarter_string, f"{stock}_price"]
        if pd.isna(price):
            try:
                price = Tools.get_price_request(quarter_string, stock)
                prices_df.loc[quarter_string, f"{stock}_price"] = price
            except:
                print(f"Warning: NaN price for {stock} in {quarter_string}. Valuing at 0.")
                price = 0      
        current_value += h["amount"] * price
    value = current_value + capital
    results.loc[dt.datetime.strptime(quarter_string, "%Y-%m-%d")] = value
    print(value)

spy_daily_stock_prices = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=spy&outputsize=full&apikey={api_key}").json()["Time Series (Daily)"]
spy_prices = pd.DataFrame().from_records([{"date": d, "price": Tools.get_price(dt.datetime.strftime(d, "%Y-%m-%d"), spy_daily_stock_prices)} for d in results.index], index="date") / Tools.get_price(dt.datetime.strftime(results.index[0], "%Y-%m-%d"), spy_daily_stock_prices)
results = results / results.iloc[0]

print(results)

figure = plt.figure()
p = figure.add_subplot()

prices_df.to_csv("prices_edited.csv")

p.plot(results, label="Test")
p.plot(spy_prices, label="Spy")
p.legend()
plt.show()