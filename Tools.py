from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import os
import requests
import numpy as np
from dotenv import load_dotenv

# search up to 7 days backward for stock price data
def get_price(date, daily_stock_prices):
    look_date = datetime.strptime(date, "%Y-%m-%d")
    current_price = np.nan
    for _ in range(7): 
        ds = look_date.strftime("%Y-%m-%d")
        if ds in daily_stock_prices:
            if "5. adjusted close" in daily_stock_prices[ds]:
                current_price = float(daily_stock_prices[ds]["5. adjusted close"])
            else:
                current_price = float(daily_stock_prices[ds]["4. close"])
            break
        look_date -= timedelta(days=1)
    return current_price


def get_price_request(date, ticker):
    load_dotenv() 
    api_key = os.getenv('ALPHA_KEY')
    return get_price(date, requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={api_key}").json()["Time Series (Daily)"])

def get_price_df():
    load_dotenv()
    api_key = os.getenv('ALPHA_KEY')
    stock_list = pd.read_csv("stock_tickers.csv")
    prices = pd.DataFrame()
    for i, ticker in enumerate(stock_list["symbol"]):
        try:
            balance_statements = requests.get(f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={api_key}").json()["quarterlyReports"]
            daily_stock_prices = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={api_key}").json()["Time Series (Daily)"]
            bs_df = pd.DataFrame.from_records(balance_statements,index="fiscalDateEnding").dropna()
            company_dates = bs_df.index
            price_df = pd.DataFrame(
                [{"price": get_price(date, daily_stock_prices)} for date in company_dates],
                index=company_dates
            ).rename(columns={"price": f"{ticker}_price"})
            prices = pd.concat([prices, price_df], axis=1)
        except Exception as e:
            print(f"Skipping {ticker} due to error: {str(e)}")
            continue
    prices.to_csv("price_new.csv")