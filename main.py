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
    "percent_sold_per_quarter": 1,
    "stock_purchases_per_quarter": 20, # 20 works well
    "starting_quarters": ["2014-03-31", "2018-03-31", "2020-03-31", "2023-03-31"], # 2014-03-31, 2018-03-31 good. 2019-03-31 bad but 2019-06-30 good?
    # "starting_quarters": ["2020-03-31"], # 202[0, 1, 2, 3]-03-31 only 2 did well
    "roic_lower_threshold": 0.25,
    "ey_lower_threshold": 0,
    "market_cap_lower_threshold": 500000000
}

results_list = []

for starting_quarter in p["starting_quarters"]:

    capital = p["starting_capital"]
    holdings = [] # list of dicts: name, date purchased, amount of stock, shorting T/F
    results = pd.DataFrame(columns=["portfolio value"])

    roic_ey_df = pd.read_csv("roic_ey.csv", index_col="fiscalDateEnding")
    prices_df = pd.read_csv("prices_edited.csv", index_col="fiscalDateEnding")
    market_caps = pd.read_csv("market_caps.csv", index_col="fiscalDateEnding")

    for quarter in range(roic_ey_df.index.get_loc(starting_quarter), -1, -1):
        quarter_string = roic_ey_df.index[quarter]

        # Find stats for this quarter's contenders in new df
        roic_cols = [col for col in roic_ey_df.loc[quarter_string].index if "roic" in col]
        ey_cols = [col for col in roic_ey_df.loc[quarter_string].index if "ey" in col]
        quarter_df = pd.DataFrame(columns=["roic", "ey", "market_cap", "score"])
        for ticker in [r.replace("_roic", "") for r in roic_cols]:
            quarter_df.loc[ticker] = {"roic": roic_ey_df.loc[quarter_string][f"{ticker}_roic"], "ey": roic_ey_df.loc[quarter_string][f"{ticker}_ey"], "market_cap": market_caps.loc[quarter_string][f"{ticker}_market_cap"]}
        
        # Apply thresholds
        quarter_df = quarter_df[quarter_df["ey"] > p["ey_lower_threshold"]]
        quarter_df = quarter_df[quarter_df["roic"] > p["roic_lower_threshold"]]
        quarter_df = quarter_df[quarter_df["market_cap"] > p["market_cap_lower_threshold"]]

        # Calculate and sort by score to find picks
        quarter_df["score"] = 0.5 * quarter_df.roic.rank(pct = True) + 0.5 * quarter_df.ey.rank(pct = True)
        quarter_df.sort_values(by="score", ascending=False, inplace=True)
        picks = quarter_df.head(p["stock_purchases_per_quarter"])

        # Calculate value of sellings 
        for h in list(holdings):
            purchase_date = dt.datetime.strptime(h["date"], "%Y-%m-%d")
            current_date = dt.datetime.strptime(quarter_string, "%Y-%m-%d")
            stock = h["ticker"]
            price = prices_df.loc[quarter_string, f"{stock}_price"]
            # Check if price exists and is not NaN
            if f"{stock}_price" not in prices_df.columns or pd.isna(prices_df.loc[quarter_string, f"{stock}_price"]):
                try:
                    price = Tools.get_price_request(quarter_string, stock)
                    prices_df.loc[quarter_string, f"{stock}_price"] = price
                except:
                    print(f"Warning: Missing price for {stock} in {quarter_string}. Holding not closed.")
                    continue
            capital += h["amount"] * price
            holdings.remove(h)

        # Make purchases
        for stock in picks.index:
            price = prices_df.loc[quarter_string][f"{stock}_price"]
            amount = (capital / p["stock_purchases_per_quarter"]) / price
            holdings.append({
                "ticker": stock,
                "date": quarter_string,
                "type": "long",
                "amount": amount
            })
            capital -= (capital / p["stock_purchases_per_quarter"])
        
        # Calculate new total value
        current_value = 0
        for h in holdings:
            stock = h["ticker"]
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
        # print(f"{quarter_string}: \n{[h['ticker'] for h in holdings]}\n\n")

    results = results / results.iloc[0]
    results_list.append(results)

figure = plt.figure()
plot = figure.add_subplot()

prices_df.to_csv("prices_edited.csv")

for i, results in enumerate(results_list):
    plot.plot(results, label=f"{p['starting_quarters'][i]}")
    spy_daily_stock_prices = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=spy&outputsize=full&apikey={api_key}").json()["Time Series (Daily)"]
    spy_prices = pd.DataFrame().from_records([{"date": d, "price": Tools.get_price(dt.datetime.strftime(d, "%Y-%m-%d"), spy_daily_stock_prices)} for d in results.index], index="date") / Tools.get_price(dt.datetime.strftime(results.index[0], "%Y-%m-%d"), spy_daily_stock_prices)
    plot.plot(spy_prices, label=f"Spy For {p['starting_quarters'][i]}", color="black")
plot.legend()
plt.show()