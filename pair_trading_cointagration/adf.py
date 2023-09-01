# adf.py
""" Augmented Dickey-Fuller Test
The ADF test makes use of the fact that if a price series possesses mean reversion then the next
price level will be proportional to the current price level. Mathematically, the ADF is based on
the idea of testing for the presence of a unit root in an autoregressive time series sample.
“Autoregressive” here indicates a time series whose current values is in some way dependent on
its previous values. 
"""

import statsmodels.tsa.stattools as ts
from datetime import datetime as dt
import pprint
import sys
import os

sys.path.append("/Users/walkerhutchinson/Desktop/ThunderFund/meteor_code/get_hist_data") # https://stackoverflow.com/questions/17663634/no-module-named-using-sys-path-append
from a_v_data import AlphaVantage

if __name__ == "__main__":
    # Create an AlphaVantage API instance
    av = AlphaVantage()

    # Download the Amazon OHLCV data from 1/1/2000 to 1/1/2015
    start_date = dt(2020, 1, 1)
    end_date = dt(2023, 6, 1)
    amzn = av.get_daily_historic_data('F', start_date, end_date)

    # Output the results of the Augmented Dickey-Fuller test for Amazon
    # with a lag order value of 1
    pprint.pprint(ts.adfuller(amzn['Close'].tolist(), 1))


""" Returns
1 adf: float The test statistic.
2 pvalue: float MacKinnon's approximate p-value based on MacKinnon (1994, 2010).
3 usedlag: int The number of lags used.
4 nobs: int The number of observations used for the ADF regression and calculation of the critical values. 
5 {critical values} : dict Critical values for the test statistic at the 1 %, 5 %, and 10 % levels. Based on MacKinnon (2010).
6 icbest: float The maximized information criterion if autolag is not None.
resstore: ResultStore, optional A dummy class with results attached as attributes
"""

"""
if the test statistic is larger (+ direction, smaller is - direction) than the critical values then the null 
hypothesis cannot be rejected, thus the series is unlikely to be mean 
reverting
"""
