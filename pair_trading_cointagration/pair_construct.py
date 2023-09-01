# https://www.r-bloggers.com/2021/01/example-of-pairs-trading/

from statsmodels.tsa.stattools import adfuller
from scipy.stats import pearsonr
from statsmodels.api import OLS
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import numpy as np
import itertools


# List of symbols
SYMBOLS = [
    'GOOGL', 'TSLA', 'META', 'AMZN', 'AAPL', 'MSFT', 'VOD', 'ADBE', 'NVDA', 'CRM',
    'EBAY', 'YNDX', 'TRIP', 'NFLX', 'DBX', 'ETSY', 'PYPL','EA', 'BIDU', 'TMUS',
    'SPLK', 'JPM', 'OKTA', 'MDB', 'GM', 'INTC', 'GT', 'SBUX', 'WIX', 'F'
]

def download_stock(symbol: str) -> pd.Series:
    """Download and return closing prices for a given stock symbol."""
    data = yf.download(symbol, start="2020-01-01", end="2021-01-03", progress=False)
    return data['Close']

# Download stock data for all symbols and create a DataFrame
close_prices = pd.DataFrame({symbol: download_stock(symbol) for symbol in SYMBOLS})

# Calculate the log of closing prices and split into train and test datasets
close_prices_log = np.log(close_prices)
train = close_prices_log.iloc[:220]
test = close_prices_log.iloc[220:252]

# Calculate correlation, beta, and p-value for each pair of stocks
results = []
for i, stock_i in enumerate(SYMBOLS):
    for j, stock_j in enumerate(SYMBOLS):
        if i > j:
            # Calculate correlation
            corr, _ = pearsonr(train[stock_i], train[stock_j])
            
            # Perform linear regression without intercept and calculate residuals
            model = OLS(train[stock_i], train[stock_j]).fit(disp=False) # disp=False keeps a massive array from printing to the terminal automatically
            spread = model.resid
            
            # Perform Augmented Dickey-Fuller test
            adf_result = adfuller(spread)
            
            results.append({
                'left_side': stock_i,
                'right_side': stock_j,
                'correlation': corr,
                'beta': model.params[0],
                'pvalue': adf_result[1]
            })
"""
# Calculate correlation, beta, and p-value for each pair of stocks
results = []
for stock_i, stock_j in itertools.combinations(SYMBOLS, 2):
    # Calculate correlation
    corr, _ = pearsonr(train[stock_i], train[stock_j])

    # Perform linear regression without intercept and calculate residuals
    model = OLS(train[stock_i], train[stock_j]).fit()
    spread = model.resid

    # Perform Augmented Dickey-Fuller test
    adf_result = adfuller(spread)

    results.append({
        'left_side': stock_i,
        'right_side': stock_j,
        'correlation': corr,
        'beta': model.params[0],
        'pvalue': adf_result[1]
    })
"""
# Create DataFrame with results and filter pairs based on correlation and p-value
results_df = pd.DataFrame(results)
results_df = results_df[(results_df['correlation'] > 0.95) & (results_df['pvalue'] < 0.05)]

# Sort pairs by correlation in descending order
results_df.sort_values('correlation', ascending=False, inplace=True)

print(results_df)

# Plotting the spread
pair = results_df.iloc[0]  # Assuming you want to plot the spread of the first pair in the results

left_stock = pair['left_side']
right_stock = pair['right_side']
beta = pair['beta']

spread = train[left_stock] - beta * train[right_stock]
plt.plot(spread)
plt.title(f'{left_stock} vs {right_stock}')
plt.show()
