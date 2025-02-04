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
    "capital_invested_per_year": 1,
    "stock_purchases_per_quarter": 25, # 20 works well
    "stock_shorts_per_quarter": 0,
    # "starting_quarters": ["2014-03-31", "2018-03-31", "2020-03-31", "2023-03-31"], # 2014-03-31, 2018-03-31 good. 2019-03-31 bad but 2019-06-30 good?
    "starting_quarters": ["2020-03-31"], # 202[0, 1, 2, 3]-03-31 only 2 did well
    "roic_lower_threshold": 0.25,
    "short_criteria": "low_ey",  # Options: low_ey, negative_roic, etc.
    "short_roic_upper_threshold": 0.05,  # Only short stocks with ROIC < 5%
    "short_interest_rate": 0.02,  # Annualized borrow cost
    "margin_requirement": 0.5,  # 50% collateral required for short positions
}

results_list = []

for starting_quarter in p["starting_quarters"]:

    capital = p["starting_capital"]
    holdings = [] # list of dicts: name, date purchased, amount of stock, shorting T/F
    results = pd.DataFrame(columns=["portfolio value"])

    roic_ey_df = pd.read_csv("roic_ey.csv", index_col="fiscalDateEnding")
    prices_df = pd.read_csv("prices_edited.csv", index_col="fiscalDateEnding")

    # print(prices_df["CTBB_price"])
    # print(roic_ey_df["CTBB_ey"])

    for quarter in range(roic_ey_df.index.get_loc(starting_quarter), -1, -1):

        quarter_string = roic_ey_df.index[quarter]
        quarterly_capital = 0

        roic_cols = [col for col in roic_ey_df.columns if "roic" in col]
        roic = roic_ey_df.iloc[quarter][roic_cols].dropna().sort_values(ascending=False)

        # Get buy list
        prospects_names = [name.replace("_roic", "") for name in roic[roic > p["roic_lower_threshold"]].index]
        ey_cols = [col for col in roic_ey_df.columns if "ey" in col and col.replace("_ey", "") in prospects_names]
        ey = roic_ey_df.iloc[quarter][ey_cols].dropna().sort_values(ascending=False)
        picks = ey.head(p["stock_purchases_per_quarter"])

        # Get short list
        shorts = pd.DataFrame()
        roic_short = roic[roic < p["short_roic_upper_threshold"]]
        if p["short_criteria"] == "low_ey":
            # Get worst EY performers
            # ey_short = roic_ey_df.loc[quarter_string][roic[roic < p["short_roic_upper_threshold"]].index].dropna().sort_values(ascending=True)  # Ascending = worst first
            ey_short_names = [col for col in roic_ey_df.columns if "ey" in col and col.replace("_ey", "") in [name.replace("_roic", "") for name in roic_short.index]]
            shorts = roic_ey_df.loc[quarter_string][ey_short_names].sort_values(ascending=True).head(p["stock_shorts_per_quarter"])
        elif p["short_criteria"] == "negative_roic":
            # Get stocks with ROIC < threshold
            roic_short = roic[roic < p["short_roic_upper_threshold"]]
            shorts = roic_short.sort_values(ascending=True).head(p["stock_shorts_per_quarter"])

        if capital > 0:
            quarterly_capital = p["starting_capital"] * p["capital_invested_per_year"] / 4
            capital -= quarterly_capital

        # Calculate value of sellings 
        for h in list(holdings):
            purchase_date = dt.datetime.strptime(h["date"], "%Y-%m-%d")
            current_date = dt.datetime.strptime(quarter_string, "%Y-%m-%d")
            if (current_date - purchase_date) > dt.timedelta(days=360):
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
                if h["type"] == "long":
                    quarterly_capital += h["amount"] * price
                elif h["type"] == "short":
                    # Buy back shares to cover the short
                    buyback_cost = abs(h["quantity"]) * price
                    capital += h["collateral"] - buyback_cost  # Return collateral minus cost
                holdings.remove(h)

        # Purchases
        for stock in [p.replace("_ey", "") for p in picks.index]:
            price = prices_df.loc[quarter_string][f"{stock}_price"]
            holdings.append({
                "ticker": stock,
                "date": quarter_string,
                "type": "long",
                "amount": (quarterly_capital / (p["stock_purchases_per_quarter"] + p["stock_shorts_per_quarter"])) / price
                # "amount": (quarterly_capital / p["stock_purchases_per_quarter"]) / Tools.get_price_request(quarter_string, stock)
            })
        
        # New Shorts
        for stock in [p.replace("_ey", "").replace("_roic", "") for p in shorts.index]:
                price = prices_df.loc[quarter_string][f"{stock}_price"]
                if pd.isna(price):
                    price = Tools.get_price_request(quarter_string, stock)
                    prices_df.loc[quarter_string, f"{stock}_price"] = price
                max_shares = (quarterly_capital / (p["stock_purchases_per_quarter"] + p["stock_shorts_per_quarter"])) / (price * p["margin_requirement"])
                holdings.append({
                "ticker": stock,
                "date": quarter_string,
                "quantity": -max_shares,  # Negative = short
                "type": "short",
                "entry_price": price,
                "collateral": max_shares * price * p["margin_requirement"]
            })

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
            if h["type"] == "long":
                current_value += h["amount"] * price

            elif h["type"] == "short":
                # Mark-to-market loss/profit: (entry - current) × quantity
                mtm = (h["entry_price"] - price) * abs(h["quantity"])
                current_value += mtm
                
                # Subtract collateral (already accounted for in capital)
                current_value -= h["collateral"] * p["short_interest_rate"] / 4  # Quarterly interest
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