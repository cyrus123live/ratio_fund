import yfinance as yf
import pandas as pd

# -----------------------------------------------
# 1. Fetch financial data using yfinance
# -----------------------------------------------
ticker_symbol = "AAPL"
ticker = yf.Ticker(ticker_symbol)

# Get annual balance sheet, income statement, and other fundamentals
balance_sheet = ticker.balance_sheet
income_statement = ticker.financials
info = ticker.info  # Contains some metadata (including P/E if available)

# Inspect the data (optional)
# print(balance_sheet)
# print(income_statement)
# print(info)

# -----------------------------------------------
# 2. Calculate ROA (Return on Assets)
# -----------------------------------------------
# Typically, "Net Income" is a row in the income_statement DataFrame
# "Total Assets" is a row in the balance_sheet DataFrame

try:
    net_income_series = income_statement.loc["Net Income"]
    total_assets_series = balance_sheet.loc["Total Assets"]
    
    # net_income_series and total_assets_series are Series indexed by dates (the columns)
    # For example, we can iterate over each year's column and compute ROA:
    
    roas = {}
    for date in net_income_series.index:
        net_income = net_income_series[date]
        # If Total Assets is available for the same date, we can compute ROA
        if date in total_assets_series.index:
            total_assets = total_assets_series[date]
            if total_assets != 0:
                roas[date] = net_income / total_assets
            else:
                roas[date] = None
        else:
            roas[date] = None
    
    print("ROA by year/period:")
    for period, roa_value in roas.items():
        print(f"{period}: {roa_value}")
except KeyError as e:
    print(f"Could not find the necessary rows in the statements: {e}")

# -----------------------------------------------
# 3. Retrieve or Calculate P/E Ratio
# -----------------------------------------------
# Option A: Use existing P/E from the 'info' dictionary
pe_ratio = info.get("trailingPE", None)
print(f"\nTrailing P/E (from Yahoo info): {pe_ratio}")

# Option B: Manually calculate P/E for the most recent period
# You'd need the recent net income, the share count, and the current price.
# For demonstration, we'll show a rough approach:

try:
    # Current price
    current_price = yf.download(ticker_symbol, period='1d')['Adj Close'][-1]
    
    # TTM Net Income can be found in the last column of the income_statement
    # or from "Quarterly" data to get the trailing 12 months. 
    # In this example, we'll use annual as a simplification:
    recent_net_income = net_income_series[net_income_series.index[0]]  # The newest column might be index[0]
    
    # Number of shares outstanding (if available in info)
    # This is typically 'sharesOutstanding' in the info dictionary
    shares_outstanding = info.get('sharesOutstanding', None)
    
    if shares_outstanding and recent_net_income:
        # EPS = net_income / shares_outstanding
        # P/E = current_price / EPS
        eps = recent_net_income / shares_outstanding
        manual_pe = current_price / eps if eps != 0 else None
        
        print(f"Manually calculated P/E: {manual_pe}")
    else:
        print("Unable to calculate P/E manually due to missing share count or net income.")
        
except Exception as e:
    print(f"Error fetching data or calculating manual P/E: {e}")
