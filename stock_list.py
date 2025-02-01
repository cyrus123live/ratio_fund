import requests
from dotenv import load_dotenv
import os
import pandas as pd

BASE_URL = "https://financialmodelingprep.com/api/v3/stock-screener"
price_ranges = [
    (0, 10),
    (10, 20),
    (20, 30),
    (30, 40),
    (40, 50),
    (50, 60),
    (60, 70),
    (70, 80),
    (80, 90),
    (90, 100),
    (100, 200),
    (200, 500),
    (500, 1000),
    (1000, None)  # None implies no upper limit
]
load_dotenv() 
api_key = os.getenv('FMP_KEY')

stocks_parsed = []

for lower, upper in price_ranges:
    params = {
        "apikey": api_key,
        "limit": 1000000, 
        "priceMoreThan":lower
    }
    if upper:
        params["priceLowerThan"] = upper

    # Sticking to American stocks for now
    stocks = requests.get(BASE_URL, params=params).json()

    print(len(stocks))

    for s in stocks:
        if s["sector"] in ["Consumer Cyclical", "Technology", "Industrials", "Basic Materials", "Communication Services", "Consumer Defensive", "Healthcare", "Real Estate", "Industrial Goods", "Services", "Conglomerates"] \
            and (s["country"] == "US" or s["country"] == "CA") \
            and "ADR" not in s["companyName"]:
            stocks_parsed.append(s)

print([s["symbol"] for s in stocks_parsed])
print(stocks_parsed)
stock_df = pd.DataFrame.from_records(stocks_parsed, index="symbol")
stock_df.to_csv("stock_tickers.csv")