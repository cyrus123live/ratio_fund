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
    all_dates = pd.DataFrame.from_records(requests.get(f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=ibm&apikey={api_key}").json()["quarterlyReports"])["fiscalDateEnding"]
    result = pd.DataFrame(index=all_dates)
    prices = pd.DataFrame(index=all_dates)
    market_caps = pd.DataFrame(index=all_dates)

    for i, ticker in enumerate(stock_list["symbol"]):
    # for i, ticker in enumerate(["ibm"]):
        try:
            income_statements = requests.get(f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={api_key}").json()["quarterlyReports"]
            balance_statements = requests.get(f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={api_key}").json()["quarterlyReports"]
            daily_stock_prices = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={api_key}").json()["Time Series (Daily)"]

            # print(daily_stock_prices)
            # quit()

            is_df = pd.DataFrame.from_records(income_statements,index="fiscalDateEnding").dropna()
            bs_df = pd.DataFrame.from_records(balance_statements,index="fiscalDateEnding").dropna()
            price_df = pd.DataFrame.from_records([{"fiscalDateEnding": date, "price": Tools.get_price(date, daily_stock_prices)} for date in is_df.index ], index="fiscalDateEnding").dropna()

            bs_df = bs_df.replace("None", 0)
            is_df = is_df.replace("None", np.nan)
            if bs_df.index.duplicated().any() or is_df.index.duplicated().any():
                continue

            company_info = pd.DataFrame(index = is_df.index)
            company_info["ebit"] = is_df["ebit"] 
            company_info["net_working_capital"] = bs_df["totalCurrentAssets"].astype(float) - bs_df["totalCurrentLiabilities"].astype(float)
            company_info["net_fixed_assets"] = bs_df["propertyPlantEquipment"].astype(float) - bs_df["accumulatedDepreciationAmortizationPPE"].astype(float)
            company_info["cash"] = bs_df["cashAndCashEquivalentsAtCarryingValue"]
            company_info["debt"] = bs_df["longTermDebtNoncurrent"].astype(float) + bs_df["shortTermDebt"].astype(float) + bs_df["currentLongTermDebt"].astype(float)
            company_info["market_value"] = price_df["price"].astype(float) * bs_df["commonStockSharesOutstanding"].astype(float)

            company_info.dropna(inplace=True)

            # prices[f"{ticker}_price"] = price_df["price"].astype(float)
            market_caps[f"{ticker}_market_cap"] = company_info["market_value"].astype(float)

            # result[f"{ticker}_roic"] = company_info["ebit"].astype(float) / (company_info["net_working_capital"].astype(float) + company_info["net_fixed_assets"].astype(float))
            # result[f"{ticker}_ey"] = company_info["ebit"].astype(float) / (company_info["market_value"].astype(float) + company_info["debt"].astype(float) - company_info["cash"].astype(float))
        except KeyboardInterrupt:
            quit()
        except:
            continue
    
    # result.to_csv("roic_ey.csv")
    # prices.to_csv("price.csv")
    market_caps.to_csv("market_caps.csv")

if __name__ == "__main__":
    main()


'''

     for i in range(len(income_statements)):

        date = income_statements[i]["fiscalDateEnding"]
        net_income = float(income_statements[i]["netIncome"])
        total_assets = float(balance_statements[i]["totalAssets"])
        shares_outstanding = float(balance_statements[i]["commonStockSharesOutstanding"])
        current_price = get_price(date, daily_stock_prices)

        # ROA = Net income / Total assets
        roa = net_income / total_assets

        # EPS = Net income / Shares Outstanding
        # P/E Ratio = Current price / EPS
        eps = net_income / shares_outstanding
        p_e = current_price / eps

        print(f"---{date}---")
        print(roa)
        print(p_e)
        print("\n")


'''