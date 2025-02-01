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
            if "5. adjusted close" in daily_stock_prices[ds]:
                current_price = float(daily_stock_prices[ds]["5. adjusted close"])
            else:
                current_price = float(daily_stock_prices[ds]["4. close"])
            break
        look_date -= timedelta(days=1)
    return current_price