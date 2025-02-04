Alphavantage: OBXVZ1S0Q6LU4IGH

Automatically investing in businesses with Greenblatt's magic formula:
- High earnings yield
- High return on tangible capital
- Highest combined scores are above average businesses trading at below average prices
- Greenblatt switched out 30 stocks yearly, 30% return in backtests from 1988-2004
- From the book The Little Book That Beats the Market
- Short worst companies?
- Quantitative approach to long-term value investing 

### Summary of Greenblatt's instructions below:
Finding stocks:
- Get list of stocks: no utilities, financial stocks (mutual funds, banks, and insurance companies), no foreign companies ("name contains ADR")
    - NOTE: why no foreign companies?
- Calculate ROA, and find stocks with >25%
- Calculate Price/Earnings ratios, lower is better
- Eliminate:
    - 5 or less is likely an error (is this modern?)
    - Earnings announced in last week

Investing: 
- 20-33% of capital in first year
- Invest equally in 5-7 top companies every 2-3 months until portfolio of 20-30
- Sell each stock after holding for one year
    - Winners sold few days after, losers sold few days before for tax reasons
    - After sales, purchase equal number of new highest stocks using any float

### Updates For Modern Era (From 'Modernizing Greenblatt DeepSeek Chat')
Issue: results after 2022ish seem to consistently underperform spy
Potential Solutions:
1. Find out which sectors are being chosen, restrict sectors to same proportions +-5% as in spy
    - Optional: sector neutrality, choose top x companies from each sector
2. Calculate rolling 1-year Spearman rank correlation for each metric (ROIC, EY) vs. forward returns, see if correlation dropped
3. Rank stocks based on 60% EY ROIC 50/50, and 40% 6 month momentum (minus most recent month)
    - Can change proportion based on regime changes (SPY 200 day moving average): 
        If SPX > 200DMA: 60% MF / 40% momentum.
        If SPX < 200DMA: 70% MF / 30% momentum (tilt defensive)
4. Exclude companies with Debt/EBITDA > 3x, or sector standard +1std and Interest Coverage Ratio < 4x
5. Replace EBIT/EV with Free Cash Flow Yield (FCF/EV) for Tech/biotech firms and Companies with capex > 50% of EBITDA.
6. EY = Adjusted EY = 0.7*(EBIT/EV) + 0.3*(1/forward PEG) for PEG = (forward P/E ÷ 3-year EPS growth)
7. Size positions based on inverse volatility (portfolio vol / stock vol) for 90 day vol
8. Stop trading and switch to cash if strategy underperforms Spy by >10% in rolling 3 month window, re-enter when MF+momentum composite rank Z-score > 0.5
9. Optimize parameters separately for each regime (year), then find a middle ground
10. Potentially add 10% allocation to equal-weight MAG7 (AAPL, MSFT, etc.).
11. Rebalance quarterly, 10% trailing stop loss on individual positions


### GreenBlatt's Instructions from book:
- Use Return on Assets (ROA) as a screening criterion.
- Set the minimum ROA at 25%. (This will take the place of return on capital from the magic formula study.)
- From the resulting group of high ROA stocks, screen for those stocks with the lowest Price/Earning (P/E) ratios. (This will take the place of earnings yield from the magic formula study.)
- Eliminate all utilities and financial stocks (i.e., mutual funds, banks and insurance companies) from the list.
- Eliminate all foreign companies from the list. In most cases, these will have the suffix “ADR” (for "American Depository Receipt”) after the name of the stock.
- If a stock has a very low P/E ratio, say 5 or less, that may indicate that the previous year or the data being used are unusual in some way. You may want to eliminate these stocks from your list. You may also want to eliminate any company that has announced earnings in the last week. (This should help minimize the incidence of incorrect or untimely data.)
- After obtaining your list, follow steps 4 and 8 from the magicformulainvesting.com instruction page:
    1. Buy five to seven top-ranked companies. To start, invest only 20 to 33 percent of the money you intend to invest during the first year (for smaller amounts of capital, lowerpriced Web brokers such as foliofn.com, buyandhold.com, and scottrade.com may be a good place to start).
    2. Repeat Step 1 every two to three months until you have invested all of the money you have chosen to allocate to your magic formula portfolio. After 9 or 10 months, this should result in a portfolio of 20 to 30 stocks (e.g., seven stocks every three months, five or six stocks every two months).
    3. Sell each stock after holding it for one year. For taxable accounts, sell winners after holding them a few days more than one year and sell losers after holding them a few days less than one year (as previously described). Use the proceeds from any sale and any additional investment money to replace the sold companies with an equal number of new magic formula selections (Step 1).
    4. Continue this process for many years. Remember, you must be committed to continuing this process for a minimum of three to five years, regardless of results. Otherwise, you will most likely quit before the magic formula has a chance to work!


Note: worst case scenario: https://www.alphavantage.co/documentation/#etf-profile
- Also: https://www.alphavantage.co/documentation/#insider-transactions

