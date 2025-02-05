import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import requests
import Tools
from dotenv import load_dotenv
import os
import numpy as np
import math
import json

load_dotenv() 
api_key = os.getenv('ALPHA_KEY')

quarters = ['2014-03-31', '2014-06-30', '2014-09-30', '2014-12-31', '2015-03-31', '2015-06-30', '2015-09-30', '2015-12-31', '2016-03-31', '2016-06-30', '2016-09-30', '2016-12-31', '2017-03-31', '2017-06-30', '2017-09-30', '2017-12-31', '2018-03-31', '2018-06-30', '2018-09-30', '2018-12-31', '2019-03-31', '2019-06-30', '2019-09-30', '2019-12-31', '2020-03-31', '2020-06-30', '2020-09-30', '2020-12-31', '2021-03-31', '2021-06-30', '2021-09-30', '2021-12-31', '2022-03-31', '2022-06-30', '2022-09-30', '2022-12-31', '2023-03-31', '2023-06-30', '2023-09-30', '2023-12-31', '2024-03-31', '2024-06-30', '2024-09-30']

p = {
    "starting_capital": 1000000000,
    "percent_sold_per_quarter": 1,
    "stock_purchases_per_quarter": 20, # 20 works well
    # "starting_quarters": ["2014-03-31", "2018-03-31", "2020-03-31", "2023-03-31"], # 2014-03-31, 2018-03-31 good. 2019-03-31 bad but 2019-06-30 good?
    "starting_quarters": ["2023-03-31"], # 202[0, 1, 2, 3]-03-31 only 2 did well
    "roic_lower_threshold": -100, # 0.25 before, 0 works well
    "ey_lower_threshold": -100, # 0 before
    "market_cap_lower_threshold": 0
}

results_list = []

for starting_quarter in p["starting_quarters"]:

    capital = p["starting_capital"]
    holdings = [] # list of dicts: name, date purchased, amount of stock, shorting T/F
    results = pd.DataFrame(columns=["portfolio value"])

    roic_df = pd.read_csv("data/roic.csv", index_col="fiscalDateEnding")
    ey_df = pd.read_csv("data/ey.csv", index_col="fiscalDateEnding")
    prices_df = pd.read_csv("data/prices.csv", index_col="fiscalDateEnding")
    market_caps_df = pd.read_csv("data/market_caps.csv", index_col="fiscalDateEnding")

    for quarter_string in quarters[quarters.index(starting_quarter):]:

        # Find stats for this quarter's contenders in new df
        quarter_df = pd.DataFrame(columns=["roic", "ey", "market_cap", "price", "score"])
        for ticker in roic_df.columns:
            roic = Tools.get_latest_stat(ticker, quarter_string, roic_df)
            ey = Tools.get_latest_stat(ticker, quarter_string, ey_df)
            price = Tools.get_latest_stat(ticker, quarter_string, prices_df)
            market_cap = Tools.get_latest_stat(ticker, quarter_string, market_caps_df)
            if not pd.isna(roic) and not pd.isna(ey) and not pd.isna(price) and not pd.isna(market_cap):
                quarter_df.loc[ticker] = {"roic": roic, "ey": ey, "market_cap": market_cap, "price": price}

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
            price = Tools.get_latest_stat(h["ticker"], quarter_string, prices_df)
            # Check if price exists and is not NaN
            if pd.isna(price):
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
            price = quarter_df.loc[stock, "price"]
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
            price = quarter_df.loc[h["ticker"], "price"]
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
        print(f"{quarter_string}: {value:0.2f}")
        # print(f"{quarter_string}: \n{[h['ticker'] for h in holdings]}\n\n")

    results = results / results.iloc[0]
    results_list.append(results)

figure = plt.figure()
plot = figure.add_subplot()

# prices_df.to_csv("prices_edited.csv")

for i, results in enumerate(results_list):
    plot.plot(results, label=f"{p['starting_quarters'][i]}")
    with open('data/spy.json', 'r') as openfile:
        spy_daily_stock_prices = json.load(openfile)
    spy_prices = pd.DataFrame().from_records([{"date": d, "price": Tools.get_price(dt.datetime.strftime(d, "%Y-%m-%d"), spy_daily_stock_prices)} for d in results.index], index="date") / Tools.get_price(dt.datetime.strftime(results.index[0], "%Y-%m-%d"), spy_daily_stock_prices)
    plot.plot(spy_prices, label=f"Spy For {p['starting_quarters'][i]}", color="black")
plot.legend()
plt.show()