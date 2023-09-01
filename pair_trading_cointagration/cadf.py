# cadf.py
""" 
Cointegration describes a long-term relationship between two (or more) asset prices 
"""
"""
The simplest form of mean-reverting trade strategies is the classic “pairs trade”, which usually
involves a dollar-neutral long-short pair of equities. The theory goes that two companies in the
same sector are likely to be exposed to similar market factors, which affect the performance of
their respective businesses. Occasionally their relative stock prices will diverge due to certain
events that affect one but not the other and their price differences will eventually revert to the
long-running mean
"""
"""  
find high correlating BETA
"""

"""     
That is, if the p-value is < significance level (say 0.05), then the series is non-stationary

Non-stationarity is a condition where the mean, variance, or autocorrelation of a time series data 
change over time. This implies that the data does not have a stable or predictable behavior, and 
that the past observations may not be representative of the future ones.
"""

"""
The null hypothesis in the context of any statistical test is a general statement or default position that there is no relationship between two measured phenomena. Rejecting the null hypothesis generally means that there is sufficient statistical evidence to suggest that the null hypothesis is not true.

The Augmented Dickey-Fuller (ADF) test is a type of statistical test that is commonly used to test whether a time series is stationary. The null hypothesis of the ADF test is that the time series is non-stationary (has some sort of time-dependent structure).

ADF Test Value and Critical Value: If the ADF test value is less than the critical value, we reject the null hypothesis. In the context of the ADF test, this would mean we have enough evidence to say the time series is stationary. The critical value is a point beyond which we start to reject the null hypothesis. Think of it as a threshold that the test statistic should surpass for the result to be significant.

P-value: The p-value is a statistical concept that measures the strength of evidence in support of a hypothesis. A smaller p-value means that there is stronger evidence in favor of the alternative hypothesis. The commonly used threshold to determine significance is 0.05 (or 5%). If the p-value is less than 0.05, we reject the null hypothesis. In the context of the ADF test, a p-value less than 0.05 would suggest that the time series is stationary.

In essence, rejecting the null hypothesis in an ADF test if the ADF test value is less than the critical value, or if the p-value is less than 0.05, means that the time series being tested has no unit root and is stationary
"""

""" 
If your Augmented Dickey-Fuller (ADF) test statistic is not lower (less negative) than any of your critical values at the 1%, 5%, and 10% significance levels, it means that you fail to reject the null hypothesis of the ADF test. In other words, you do not have enough evidence to conclude that the time series is stationary or that there is a cointegrating relationship among the variables.

for example:
At the 1% significance level: Since the ADF test statistic is not smaller (more negative) than the critical value at the 1% level, you fail to reject the null hypothesis. This means that you do not have enough evidence to conclude that the time series is stationary or cointegrated at the 1% significance level.
At the 5% significance level: Since the ADF test statistic is smaller (more negative) than the critical value at the 5% level, you reject the null hypothesis. This suggests that the time series is stationary or cointegrated at the 5% significance level.
At the 10% significance level: Similarly, since the ADF test statistic is smaller (more negative) than the critical value at the 10% level, you also reject the null hypothesis at the 10% significance level, indicating that the time series is stationary or cointegrated at this level of significance.
"""

from pandas.plotting import register_matplotlib_converters
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt, timedelta
import statsmodels.tsa.stattools as ts
from datetime import datetime as dt
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import statsmodels.api as sm
import pandas as pd
import numpy as np
import pprint
import sys
import os

register_matplotlib_converters()

sys.path.append("/Users/walkerhutchinson/Desktop/ThunderFund/meteor_code/get_hist_data") # https://stackoverflow.com/questions/17663634/no-module-named-using-sys-path-append
from a_v_data import AlphaVantage

def plot_price_series(df, ts1, ts2, ax):
    """
    Plot both time series on the same line graph.
    """
    months = mdates.MonthLocator()  # every month
    
    ax.plot(df.index, df[ts1], label=ts1)
    ax.plot(df.index, df[ts2], label=ts2)
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    # ax.set_xticklabels(mdates.DateFormatter('%b %Y'), rotation=90)
    ax.grid(True)
    
    ax.set_xlabel('Month/Year')
    ax.set_ylabel('Price ($)')
    ax.set_title('%s and %s Daily Prices' % (ts1, ts2))
    ax.legend()

    plt.setp(ax.get_xticklabels(), rotation=90, )
    # horizontalalignment='right')



def plot_scatter_series(df, ts1, ts2, ax):
    """
    Plot a scatter plot of both time series.
    """
    ax.set_xlabel('%s Price ($)' % ts1)
    ax.set_ylabel('%s Price ($)' % ts2)
    ax.set_title('%s and %s Price Scatterplot' % (ts1, ts2))
    ax.scatter(df[ts1], df[ts2])
    
    # Fit a linear regression model to the data and plot the line
    model = np.polyfit(df[ts1], df[ts2], 1)
    predicted = np.poly1d(model)
    ax.plot(df[ts1], predicted(df[ts1]), color='red')


# def plot_residuals(df, ax):
#     """
#     Plot the residuals of OLS procedure for both
#     time series.
#     """
#     months = mdates.MonthLocator()  # every month
    
#     ax.plot(df.index, df["res"], label="Residuals", color='blue')
#     ax.xaxis.set_major_locator(months)
#     ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
#     # ax.set_xticklabels(mdates.DateFormatter('%b %Y'), rotation=90)
#     ax.grid(True)
    
#     ax.set_xlabel('Month/Year')
#     ax.set_ylabel('Price ($)')
#     ax.set_title('Residual Plot')
#     ax.legend()

#     plt.setp(ax.get_xticklabels(), rotation=90, )
#     # horizontalalignment='right')

def plot_residuals(df, ax):
    """
    Plot the residuals of OLS procedure for both
    time series.
    """
    
    """ 
    In statistics and machine learning, a residual is the difference between the observed value and the predicted value of a variable. In other words, it's the error in your prediction.
    """
    months = mdates.MonthLocator()  # every month

    # residuals = df["res"]
    residuals = df["z-s"]
    ax.plot(df.index, residuals, label="Residuals", color='blue')
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.grid(True)

    ax.set_xlabel('Month/Year')
    ax.set_ylabel('Price ($)')
    ax.set_title('Residual Plot')
    ax.legend()

    plt.setp(ax.get_xticklabels(), rotation=90)

    # Check for residuals crossing or near zero
    epsilon = 0.1  # Define what you consider to be 'near zero'
    last_value = residuals[0]
    for date, value in zip(df.index[1:], residuals[1:]):
        if abs(value) <= epsilon:
            # print(f"Residual is near zero on {date}")
            continue
        elif (last_value < 0 and value > 0) or (last_value > 0 and value < 0):
            print(f"Residual crosses zero on {date}")

        if (last_value < -3 and value > -3) or (last_value > -3 and value < -3):
            print(f"Residual crosses -3 on {date}:", last_value)

        last_value = value

if __name__ == "__main__":
    # Create an AlphaVantage API instance
    av = AlphaVantage()

    # Set tickers
    ticker1 = "F"
    ticker2 = "GM"

    # Download ticker-data-1 and ticker-data-2 for the duration of 2015
    start_date = dt(2011, 1, 1)
    end_date = dt(2016, 1, 1)
    # start_date="2020-01-01", end_date="2021-01-01"
    ticker_data_1 = av.get_daily_historic_data(ticker1, start_date, end_date)
    ticker_data_2 = av.get_daily_historic_data(ticker2, start_date, end_date)

    # Place them into the Pandas DataFrame format
    df = pd.DataFrame(index=ticker_data_1.index)
    df[ticker1] = ticker_data_1["Close"]
    df[ticker2] = ticker_data_2["Close"]

    fig, axs = plt.subplots(1, 4, figsize=(20, 5))

    # Plot the two time series
    plot_price_series(df, ticker1, ticker2, axs[0])
    
    # Display a scatter plot of the two time series
    plot_scatter_series(df, ticker1, ticker2, axs[1])

    # Calculate optimal hedge ratio "beta" via Statsmodels
    model = sm.OLS(df[ticker1], df[ticker2]) 
    res = model.fit()
    beta_hr = res.params[0]

    # Calculate the residuals of the linear combination
    df["res"] = df[ticker1] - beta_hr * df[ticker2]

    # Calculate and output the CADF test on the residuals
    cadf = ts.adfuller(df["res"])

    zscore = ((df["res"] - df["res"].mean())/ df["res"].std())[-1]
    print("type(zscore)", type(zscore))
    df["z-s"] = ((df["res"] - df["res"].mean())/ df["res"].std())

    # Plot the residuals or zscore
    plot_residuals(df, axs[2])

    # Add the text to the fourth subplot
    cadf_text = f'ADF Statistic: {round(cadf[0], 4)} \np-value: {round(cadf[1],4)} \nLags used: {cadf[2]} \nObservations: {round(cadf[3],4)}\nCurrent Z-score: {round(zscore, 4)}\n'
    for i, val in enumerate(cadf[4].items()):
        cadf_text += f'Critical Value : {val[0]} , {round(val[1],4)} \n'

    axs[3].axis('off')
    axs[3].text(0.1, 0.5, cadf_text, horizontalalignment='left', verticalalignment='center', fontsize=16)

    plt.tight_layout()
    plt.show()
    # # Replace '/path/to/your/desktop' with the actual path to your desktop
    # plt.savefig('/Users/walkerhutchinson/Desktop/F GM Cointegration 2011 to 2023.png')




















# if __name__ == "__main__":
#     # Create an AlphaVantage API instance
#     av = AlphaVantage()

#     # Set tickers
#     ticker1 = "F"
#     ticker2 = "GM"

#     # Download ticker-data-1 and ticker-data-2 for the duration of 2015
#     start_date = dt(2011, 1, 2)
#     end_date = dt(2015, 1, 3)

#     # start_date="2020-01-01", end_date="2021-01-01"
#     ticker_data_1 = av.get_daily_historic_data(ticker1, start_date, end_date)
#     ticker_data_2 = av.get_daily_historic_data(ticker2, start_date, end_date)

#     # Place them into the Pandas DataFrame format
#     df = pd.DataFrame(index=ticker_data_1.index)
#     df[ticker1] = ticker_data_1["Close"]
#     df[ticker2] = ticker_data_2["Close"]

#     # Calculate optimal hedge ratio "beta" via Statsmodels
#     model = sm.OLS(df[ticker1], df[ticker2])
#     res = model.fit()
#     beta_hr = res.params[0]
#     # Calculate the residuals of the linear combination
#     df["res"] = df[ticker1] - beta_hr * df[ticker2]

#     # Convert the index to a DatetimeIndex
#     df.index = pd.to_datetime(df.index)

#     # Plot the residuals
#     plt.figure(figsize=(10, 5))

#     # Check for residuals crossing or near zero
#     epsilon = 0.1  # Define what you consider to be 'near zero'
#     last_value = df["res"].iat[0]
    
#     for date, value in zip(df["res"].index[1:], df["res"].values[1:]):
#         if abs(value) <= epsilon:
#             # print(f"Residual is near zero on {date}")
#             continue
#         elif (last_value < 0 and value > 0):
#             print(f"Residual upward crosses zero on {date}")
#             print("last_value", last_value)
#             print("value", value)

#         elif (last_value > 0 and value < 0):
#             print(f"Residual downward crosses zero on {date}")
#             print("last_value", last_value)
#             print("value", value)

#         elif (last_value < 1 and value > 1):
#             print(f"\nResidual diverging past 1 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)

#         elif (last_value > 1 and value < 1):
#             print(f"\nResidual converging past 1 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)
        
#         elif (last_value < -1 and value > -1):
#             print(f"\nResidual converging past -1 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)

#         elif (last_value > -1 and value < -1):
#             print(f"\nResidual diverging past -1 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)
#         elif (last_value < 2 and value > 2):
#             print(f"\nResidual diverging past 2 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)

#         elif (last_value > 2 and value < 2):
#             print(f"\nResidual converging past 2 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)
        
#         elif (last_value < -2 and value > -2):
#             print(f"\nResidual converging past -2 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)

#         elif (last_value > -2 and value < -2):
#             print(f"\nResidual diverging past -2 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)

#         elif (last_value < 3 and value > 3):
#             print(f"\nResidual diverging past 3 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)

#         elif (last_value > 3 and value < 3):
#             print(f"\nResidual converging past 3 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)
        
#         elif (last_value < -3 and value > -3):
#             print(f"\nResidual converging past -3 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)

#         elif (last_value > -3 and value < -3):
#             print(f"\nResidual diverging past -3 on {date}:", last_value)
#             print("last_value", last_value)
#             print("value", value)
        
#         last_value = value









