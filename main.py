from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import os
import requests
import numpy as np

# search up to 7 days backward for stock price data
def get_price(date, daily_stock_prices):
    look_date = datetime.strptime(date, "%Y-%m-%d")
    current_price = np.nan
    for _ in range(7): 
        ds = look_date.strftime("%Y-%m-%d")
        if ds in daily_stock_prices:
            current_price = float(daily_stock_prices[ds]["4. close"])
            break
        look_date -= timedelta(days=1)
    return current_price

def main():

    load_dotenv() 
    api_key = os.getenv('ALPHA_KEY')

    stock_list = pd.read_csv("stock_tickers.csv")
    result = pd.DataFrame()

    for i, ticker in enumerate(stock_list["symbol"]):
        income_statements = requests.get(f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={api_key}").json()["quarterlyReports"]
        balance_statements = requests.get(f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={api_key}").json()["quarterlyReports"]
        daily_stock_prices = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={api_key}").json()["Time Series (Daily)"]

        # print(daily_stock_prices)
        # quit()

        is_df = pd.DataFrame.from_records(income_statements,index="fiscalDateEnding", columns=["fiscalDateEnding", "netIncome"]).dropna()
        bs_df = pd.DataFrame.from_records(balance_statements,index="fiscalDateEnding", columns=["fiscalDateEnding", "totalAssets", "commonStockSharesOutstanding"]).dropna()
        price_df = pd.DataFrame.from_records([{"fiscalDateEnding": date, "price": get_price(date, daily_stock_prices)} for date in is_df.index ], index="fiscalDateEnding").dropna()

        company_info = pd.DataFrame(index = is_df.index)
        company_info["netIncome"] = is_df["netIncome"]
        company_info["totalAssets"] = bs_df["totalAssets"]
        company_info["commonStockSharesOutstanding"] = bs_df["commonStockSharesOutstanding"]
        company_info["price"] = price_df["price"]

        company_info.dropna(inplace=True)

        print(company_info)

        # ROA = Net income / Total assets
        result[f"{ticker}_roa"] = company_info["netIncome"].astype(float) / company_info["totalAssets"].astype(float)

        # P/E Ratio = Current price / EPS for EPS = Net income / Shares Outstanding
        result[f"{ticker}_pe"] = price_df["price"] / (company_info["netIncome"].astype(float) / company_info["commonStockSharesOutstanding"].astype(float))
    
    result.to_csv("roa_pe.csv")

if __name__ == "__main__":
    main()