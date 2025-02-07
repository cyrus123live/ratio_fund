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

# Try 10 purchases, 0.6 ey threshold again
p = {
    "starting_capital": 1000000000,
    "percent_sold_per_quarter": 1,
    "stock_purchases_per_quarter": 25,
    # "starting_quarters": ["2014-03-31", "2018-03-31", "2020-03-31", "2023-03-31"], # 2014-03-31, 2018-03-31 good. 2019-03-31 bad but 2019-06-30 good?
    # "starting_quarters": ["2018-12-31", "2019-12-31", "2020-12-31", "2021-12-31", "2022-12-31", "2023-12-31"], # 202[0, 1, 2, 3]-03-31 only 2 did well
    "starting_quarters": ["2019-12-31"],
    "roic_lower_threshold": 0.25, # 0.25 before, 0 works well
    "ey_lower_threshold": 0.2, # 0 before
    "market_cap_lower_threshold": 0,
    "momentum_preference": 0.8,
    "plot": "graph" # "bar" for bar graph
}

results_list = []
starting_time = dt.datetime.now()

for starting_quarter in p["starting_quarters"]: 

    capital = p["starting_capital"]
    holdings = [] # list of dicts: name, date purchased, amount of stock, shorting T/F
    results = pd.DataFrame(columns=["portfolio value"])

    roic_df = pd.read_csv("data/roic.csv", index_col="fiscalDateEnding")
    ey_df = pd.read_csv("data/ey.csv", index_col="fiscalDateEnding")
    prices_df = pd.read_csv("data/prices.csv", index_col="fiscalDateEnding")
    market_caps_df = pd.read_csv("data/market_caps.csv", index_col="fiscalDateEnding")

    # Go through each quarter from starting quarter onwards
    for i, quarter_string in enumerate(quarters[quarters.index(starting_quarter):]):

        # Find stats for this quarter's contenders in new df
        quarter_df = pd.DataFrame(columns=["roic", "ey", "market_cap", "price", "momentum", "score"])
        for ticker in roic_df.columns:
            roic = Tools.get_latest_stat(ticker, quarter_string, roic_df)
            ey = Tools.get_latest_stat(ticker, quarter_string, ey_df)
            price = Tools.get_latest_stat(ticker, quarter_string, prices_df)
            market_cap = Tools.get_latest_stat(ticker, quarter_string, market_caps_df)

            if p["momentum_preference"] > 0:
                price_1 = Tools.get_latest_stat(ticker, quarters[i - 2], prices_df)
                price_2 = Tools.get_latest_stat(ticker, quarters[i - 1], prices_df)
                momentum = (price_2 - price_1) / price_2
            else:
                momentum = 1

            if not pd.isna(roic) and not pd.isna(ey) and not pd.isna(price) and not pd.isna(market_cap) and not pd.isna(momentum):
                quarter_df.loc[ticker] = {"roic": roic, "ey": ey, "market_cap": market_cap, "price": price, "momentum": momentum}

        # Apply thresholds
        quarter_df = quarter_df[quarter_df["ey"] > p["ey_lower_threshold"]]
        quarter_df = quarter_df[quarter_df["roic"] > p["roic_lower_threshold"]]
        quarter_df = quarter_df[quarter_df["market_cap"] > p["market_cap_lower_threshold"]]

        # Calculate and sort by score to find picks
        quarter_df["score"] = (1-p["momentum_preference"]) * (0.5 * quarter_df.roic.rank(pct = True) + 0.5 * quarter_df.ey.rank(pct = True)) + p["momentum_preference"] * quarter_df.momentum.rank(pct = True)
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

    results_list.append(results)

print(f"Finished in {(dt.datetime.now() - starting_time).seconds} seconds.")

sharpe, vol = Tools.get_sharpe_and_vol(results_list[0], 4)
max_drawdown = Tools.get_max_drawdown(results_list[0])
cumulative_return, annual_return = Tools.get_cumulative_and_annual_returns(results_list[0])
print(f"Sharpe:          {sharpe:20.6f}\n"
    f"Vol:            {vol:20.6f}\n"
    f"Max Drawdown:   {max_drawdown:20.6f}\n"
    f"Cumulative Return: {cumulative_return:20.6f}\n"
    f"Annual Return:  {annual_return:20.6f}\n\n\n")

if p["plot"] == "bar":

    with open('data/spy.json', 'r') as openfile:
        spy_daily_stock_prices = json.load(openfile)
    spy_prices = pd.DataFrame().from_records([{"date": d, "price": Tools.get_price(dt.datetime.strftime(d, "%Y-%m-%d"), spy_daily_stock_prices)} for d in results_list[0].index], index="date") / Tools.get_price(dt.datetime.strftime(results_list[0].index[0], "%Y-%m-%d"), spy_daily_stock_prices)

    barWidth = 0.25
    fig = plt.subplots(figsize =(12, 8)) 

    # diff = results_list[0].diff().values.flatten()
    diff = results_list[0].pct_change().values.flatten()
    diff_spy = spy_prices.pct_change().values.flatten()

    br1 = np.arange(len(diff)) 
    br2 = [x + barWidth for x in br1] 

    plt.bar(br1, diff, color ='r', width = barWidth, 
            edgecolor ='grey', label ='Test') 
    plt.bar(br2, diff_spy, color ='g', width = barWidth, 
            edgecolor ='grey', label ='SPY') 

    plt.xlabel('Fiscal Quarter', fontweight ='bold', fontsize = 15) 
    plt.ylabel('Pct_change', fontweight ='bold', fontsize = 15) 
    plt.xticks([r + barWidth for r in range(len(diff))], 
            quarters[quarters.index(starting_quarter):])

    plt.legend()
    plt.show() 

else:

    figure = plt.figure()
    plot = figure.add_subplot()

    # prices_df.to_csv("prices_edited.csv")

    # Plot spy
    with open('data/spy.json', 'r') as openfile:
        spy_daily_stock_prices = json.load(openfile)
    spy_prices = pd.DataFrame().from_records([{"date": d, "price": Tools.get_price(dt.datetime.strftime(d, "%Y-%m-%d"), spy_daily_stock_prices)} for d in results_list[0].index], index="date") / Tools.get_price(dt.datetime.strftime(results_list[0].index[0], "%Y-%m-%d"), spy_daily_stock_prices)
    plot.plot(spy_prices, label=f"Spy", color="black")

    for i, results in enumerate(results_list):
        results = results / results.iloc[0]
        plot.plot(results * spy_prices.loc[results.index[0]]["price"], label=f"{p['starting_quarters'][i]}")
    plot.legend()
    plt.show()