from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import os
import requests
import numpy as np
import Tools

pd.set_option('future.no_silent_downcasting', True)

def main():
    load_dotenv() 
    api_key = os.getenv('ALPHA_KEY')

    stock_list = pd.read_csv("stock_tickers.csv")
    
    # Initialize lists to collect data
    roic_dfs = []
    ey_dfs = []
    price_dfs = []
    market_cap_dfs = []

    for i, ticker in enumerate(stock_list["symbol"]):
        try:
            # Fetch data
            income_statements = requests.get(f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={api_key}").json()["quarterlyReports"]
            balance_statements = requests.get(f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={api_key}").json()["quarterlyReports"]
            daily_stock_prices = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={api_key}").json()["Time Series (Daily)"]

            # Create DataFrames and remove duplicate indices
            is_df = pd.DataFrame.from_records(income_statements, index="fiscalDateEnding").replace("None", np.nan)
            bs_df = pd.DataFrame.from_records(balance_statements, index="fiscalDateEnding").replace("None", 0)
            
            # Deduplicate indices by keeping the first occurrence
            is_df = is_df[~is_df.index.duplicated(keep='first')]
            bs_df = bs_df[~bs_df.index.duplicated(keep='first')]
            
            # Merge income and balance sheets on dates
            merged_df = is_df.merge(bs_df, left_index=True, right_index=True, how='inner')
            
            # Get prices for merged dates
            prices_list = []
            for date in merged_df.index:
                price = Tools.get_price(date, daily_stock_prices)
                prices_list.append({"fiscalDateEnding": date, "price": price})
            price_df = pd.DataFrame(prices_list).set_index("fiscalDateEnding").dropna()
            
            # Merge prices with merged_df and ensure no duplicates
            merged_df = merged_df.merge(price_df, left_index=True, right_index=True, how='inner')
            merged_df = merged_df[~merged_df.index.duplicated(keep='first')]
            
            # Calculate metrics
            merged_df["market_value"] = merged_df["price"].astype(float) * merged_df["commonStockSharesOutstanding"].astype(float)
            merged_df["net_working_capital"] = merged_df["totalCurrentAssets"].astype(float) - merged_df["totalCurrentLiabilities"].astype(float)
            merged_df["net_fixed_assets"] = merged_df["propertyPlantEquipment"].astype(float) - merged_df["accumulatedDepreciationAmortizationPPE"].astype(float)
            merged_df["debt"] = merged_df["longTermDebtNoncurrent"].astype(float) + merged_df["shortTermDebt"].astype(float) + merged_df["currentLongTermDebt"].astype(float)
            
            # Compute ROIC and EY
            merged_df["roic"] = merged_df["ebit"].astype(float) / (merged_df["net_working_capital"] + merged_df["net_fixed_assets"])
            merged_df["ey"] = merged_df["ebit"].astype(float) / (merged_df["market_value"] + merged_df["debt"] - merged_df["cashAndCashEquivalentsAtCarryingValue"].astype(float))
            
            # Append to lists
            roic_series = merged_df["roic"].rename(f"{ticker}")
            ey_series = merged_df["ey"].rename(f"{ticker}")
            price_series = merged_df["price"].rename(f"{ticker}")
            market_cap_series = merged_df["market_value"].rename(f"{ticker}")
            
            roic_dfs.append(roic_series)
            ey_dfs.append(ey_series)
            price_dfs.append(price_series)
            market_cap_dfs.append(market_cap_series)
            
        except KeyboardInterrupt:
            quit()
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
    
    # Concatenate all data
    roic = pd.concat(roic_dfs, axis=1)
    ey = pd.concat(ey_dfs, axis=1)
    prices = pd.concat(price_dfs, axis=1)
    market_caps = pd.concat(market_cap_dfs, axis=1)
    
    # Save to CSV
    roic.to_csv("roic.csv")
    ey.to_csv("ey.csv")
    prices.to_csv("price.csv")
    market_caps.to_csv("market_caps.csv")

if __name__ == "__main__":
    main()