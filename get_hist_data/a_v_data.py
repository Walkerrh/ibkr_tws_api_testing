# alpha_vantage.py

from datetime import datetime as dt
import datetime
import json

import numpy as np
import pandas as pd
import requests


ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co'
ALPHA_VANTAGE_TIME_SERIES_CALL = 'query?function=TIME_SERIES_DAILY'
COLUMNS = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']


class AlphaVantage(object):
    """
    Encapsulates calls to the AlphaVantage API with a provided
    API key.
    """

    def __init__(self, api_key='CZAVRQSYV9ZTXUOQ'):
        """
        Initialise the AlphaVantage instance.

        Parameters
        ----------
        api_key : `str`, optional
            The API key for the associated AlphaVantage account
        """
        self.api_key = api_key 

    def _construct_alpha_vantage_symbol_call(self, ticker):
        """
        Construct the full API call to AlphaVantage based on the user
        provided API key and the desired ticker symbol.

        Parameters
        ----------
        ticker : `str`
            The ticker symbol, e.g. 'AAPL'

        Returns
        -------
        `str`
            The full API call for a ticker time series
        """
        return "%s/%s&symbol=%s&outputsize=full&apikey=%s" % (
            ALPHA_VANTAGE_BASE_URL,
            ALPHA_VANTAGE_TIME_SERIES_CALL,
            ticker,
            self.api_key
        )

    def _correct_back_adjusted_prices(self, price_df):
        """
        Adjusts (if necessary) the back-adjusted closing price column to
        ensure that the final closing price row matches the final adjusted
        closing price row.

        This may not be the case if the data has been generated for a date
        in excess of the final truncation data of the pricing.

        Parameters
        ----------
        price_df : `pd.DataFrame`
            The DataFrame containing the date-indexed EOD price/volumes

        Returns
        -------
        None
        """

        # final_adj_close = price_df.iloc[-1]['Adj Close']
        # if final_adj_close > 0.0:
        #     final_close = price_df.iloc[-1]['Close']
        #     if not np.allclose(final_close, final_adj_close):
        #         adj_factor = final_close / final_adj_close
        #         price_df['Adj Close'] *= adj_factor

    def get_daily_historic_data(self, ticker, start_date, end_date):
        """
        Use the generated API call to query AlphaVantage with the
        appropriate API key and return a list of price tuples
        for a particular ticker.

        Parameters
        ----------
        ticker : `str`
            The ticker symbol, e.g. 'AAPL'
        start_date : `datetime`
            The starting date to obtain pricing for
        end_date : `datetime`
            The ending date to obtain pricing for

        Returns
        -------
        `pd.DataFrame`
            The frame of OHLCV prices and volumes
        """

        # use this is dates inputed are not datetime objects
        # start_date = dt.strptime(start_date, '%Y-%m-%d')
        # end_date = dt.strptime(end_date, '%Y-%m-%d')

        av_url = self._construct_alpha_vantage_symbol_call(ticker)
        print(av_url)

        try:
            av_data_js = requests.get(av_url)
            data = json.loads(av_data_js.text)['Time Series (Daily)']
        except Exception as e:
            print(
                "Could not download AlphaVantage data for %s ticker "
                "(%s)...stopping." % (ticker, e)
            )
            return pd.DataFrame(columns=COLUMNS).set_index('Date')
        else:
            prices = []
            for date_str in sorted(data.keys()):
                date = dt.strptime(date_str, '%Y-%m-%d')
                if date < start_date or date > end_date:
                    continue

                bar = data[date_str]
                prices.append(
                    (
                        date, 
                        float(bar['1. open']),
                        float(bar['2. high']),
                        float(bar['3. low']),
                        float(bar['4. close']),
                        int(bar['5. volume']),
                    )
                )
            price_df = pd.DataFrame(prices, columns=COLUMNS).set_index('Date').sort_index()
            # self._correct_back_adjusted_prices(price_df)
            # print(price_df)
            return price_df

# get_data = AlphaVantage()
# get_data.get_daily_historic_data(ticker="AAPL", start_date="2020-01-01", end_date="2021-01-01")


""" as of 12 July 2023 this code works 
> note that dates need to be inputed as datetime objects or adjust the script above to convert them
> this file is to pass the above "price_df to the scripts in the file
> to test, Instantiate the Class below
# get_data = AlphaVantage()
# get_data.get_daily_historic_data(ticker="AAPL", start_date="2020-01-01", end_date="2021-01-01")
> add a print(price_df) to see what is passed

# use this is dates inputed are not datetime objects
# start_date = dt.strptime(start_date, '%Y-%m-%d')
# end_date = dt.strptime(end_date, '%Y-%m-%d')
"""
