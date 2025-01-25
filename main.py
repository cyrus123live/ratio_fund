from datetime import datetime, timedelta
import pandas as pd
import requests

# search up to 7 days backward for stock price data
def get_price(date, daily_stock_prices):
    look_date = datetime.strptime(date, "%Y-%m-%d")
    for _ in range(7): 
        ds = look_date.strftime("%Y-%m-%d")
        if ds in daily_stock_prices:
            current_price = float(daily_stock_prices[ds]["4. close"])
            break
        look_date -= timedelta(days=1)
    return current_price

def main():

    income_statements = requests.get("https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=IBM&apikey=demo").json()["quarterlyReports"]
    balance_statements = requests.get("https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol=IBM&apikey=demo").json()["quarterlyReports"]
    daily_stock_prices = requests.get("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&outputsize=full&apikey=demo").json()["Time Series (Daily)"]

    is_df = pd.DataFrame.from_records(income_statements,index="fiscalDateEnding")
    bs_df = pd.DataFrame.from_records(balance_statements,index="fiscalDateEnding")
    price_df = pd.DataFrame.from_records([{"fiscalDateEnding": date, "price": get_price(date, daily_stock_prices)} for date in is_df.index], index="fiscalDateEnding")

    # ROA = Net income / Total assets
    roa_df = is_df["netIncome"].astype(float) / bs_df["totalAssets"].astype(float)

    # P/E Ratio = Current price / EPS for EPS = Net income / Shares Outstanding
    pe_df = price_df["price"] / (is_df["netIncome"].astype(float) / bs_df["commonStockSharesOutstanding"].astype(float))
    
    print(roa_df)
    print(pe_df)

if __name__ == "__main__":
    main()