# hurst.py

"""
H < 0.5 The time series is mean reverting
H = 0.5 The time series is a Geometric Bronian Motion
H > 0.5 The time series is trending
"""
"""
A time series (or stochastic process) is defined to be strongly stationary if its joint probability
distribution is invariant under translations in time or space. In particular-and of key importance
for traders-the mean and variance of the process do not change over time or space and they each
do not follow a trend.
"""
"""    
The goal of the Hurst Exponent is to provide a scalar value that helps identify-within the limits
of statistical estimation-whether a series is mean reverting, randomly walking or trending.
"""
from numpy import array, cumsum, log, polyfit, sqrt, std, subtract
from datetime import datetime as dt
from numpy.random import randn
import sys
import os

sys.path.append("/Users/walkerhutchinson/Desktop/ThunderFund/meteor_code/get_hist_data") # https://stackoverflow.com/questions/17663634/no-module-named-using-sys-path-append
from a_v_data import AlphaVantage

def hurst(time_series):
    """
    Calculates the Hurst Exponent of the time series vector ts.

    Parameters
    ----------
    ts : `np.ndarray`
        Time series array of prices

    Returns
    -------
    `float`
        The Hurst Exponent of the time series
    """
    # Create the range of lag values
    lags = range(2, 100)

    # Calculate the array of the variances of the lagged differences
    tau = [
        sqrt(std(subtract(time_series[lag:], time_series[:-lag])))
        for lag in lags
    ]

    # Use a linear fit to estimate the Hurst Exponent
    poly = polyfit(log(lags), log(tau), 1)

    # Return the Hurst exponent from the polyfit output
    return poly[0] * 2.0


if __name__ == "__main__":
    # Create a Gometric Brownian Motion, Mean-Reverting, and Trending Series
    gbm = log(cumsum(randn(100000)) + 1000)
    mr = log(randn(100000) + 1000)
    tr = log(cumsum(randn(100000) + 1) + 1000)

    # Create an AlphaVantage API instance
    av = AlphaVantage()

    # Download the Amazon OHLCV data from 1/1/2000 to 1/1/2015
    start_date = dt(2020, 1, 1)
    end_date = dt(2023, 6, 1)
    ticker = "PLTR"
    stock_data = av.get_daily_historic_data(ticker, start_date, end_date)

    # Output the Hurst Exponent for each of the above series
    # and the price of Amazon (the Adjusted Close price) for 
    # the ADF test given above in the article
    print("Hurst(GBM):   %0.2f" % hurst(gbm))
    print("Hurst(MR):    %0.2f" % hurst(mr))
    print("Hurst(TR):    %0.2f" % hurst(tr))

    # Calculate the Hurst exponent for the stock_data adjusted closing prices
    hurst_stock = hurst(array(stock_data['Close'].tolist()))
    print("Hurst({}):  {:.2f}".format(ticker, hurst_stock))

    # Print the conclusion
    if hurst_stock < 0.5:
        print("The time series is mean reverting")
    elif hurst_stock > 0.45 and hurst_stock < 0.55:
        print("The time series is a Geometric Brownian Motion")
    elif hurst_stock > 0.5:
        print("The time series is trending")
