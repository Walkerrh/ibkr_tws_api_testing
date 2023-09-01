from __future__ import print_function

import datetime
import pytz

import statsmodels.api as sm
from sklearn.linear_model import LinearRegression


from Events import SignalEvent, MarketEvent
from Strategy import Strategy
import numpy as np


class OLSMRStrategy(Strategy):
    """
    Uses ordinary least squares (OLS) to perform a rolling linear
    regression to determine the hedge ratio between a pair of equities.
    The z-score of the residuals time series is then calculated in a
    rolling fashion and if it exceeds an interval of thresholds
    (defaulting to [0.5, 3.0]) then a long/short signal pair are generated
    (for the high threshold) or an exit signal pair are generated (for the
    low threshold).
    """

    def __init__(self, bars, events, ols_window=50, zscore_low=0.4, zscore_high=3.0):
        """
        Initialises the stat arb strategy.
        Parameters:
        bars - The DataHandler object that provides bar information
        events - The Event Queue object.
        """
        self.bars         = bars
        self.symbol_list  = self.bars.symbol_list
        self.events       = events
        self.ols_window   = ols_window
        self.zscore_low   = zscore_low
        self.zscore_high  = zscore_high
        self.pair         = tuple(self.symbol_list)
        self.datetime     = datetime.datetime.utcnow()
        self.long_market  = False
        self.short_market = False

        self.all_traded_dates = []
    
    def parse_time_with_timezone(self, time_str):
        # Split the string into the datetime and timezone parts
        dt_str, tz_str = time_str.rsplit(' ', 1)
        
        # Parse the datetime part
        dt = datetime.datetime.strptime(dt_str, '%Y%m%d %H:%M:%S')
        
        # Attach the timezone information if it exists
        if tz_str in pytz.all_timezones:
            dt = dt.replace(tzinfo=pytz.timezone(tz_str))
        
        return dt

    def calculate_xy_signals(self, zscore_last, timestamp):
        """
        Calculates the actual x, y signal pairings
        to be sent to the signal generator.
        Parameters
        zscore_last - The current zscore to test against
        """
        y_signal = None
        x_signal = None
        p0       = self.pair[0]
        p1       = self.pair[1]
        dt       = timestamp
        hr       = abs(self.hedge_ratio)



        # If we’re long the market and below the
        # negative of the high zscore threshold
        if zscore_last <= self.zscore_high and not self.long_market:
            self.long_market = True
            y_signal = SignalEvent(p0, dt, 'SHORT', 1.0)
            x_signal = SignalEvent(p1, dt, 'LONG', hr)

        # If we’re long the market and between the
        # absolute value of the low zscore threshold
        if abs(zscore_last) <= self.zscore_low and self.long_market:
            self.long_market = False
            y_signal = SignalEvent(p0, dt, 'EXIT', 1.0)
            x_signal = SignalEvent(p1, dt, 'EXIT', 1.0)

        # If we’re short the market and above
        # the high zscore threshold
        if zscore_last >= self.zscore_high and not self.short_market:
            self.short_market = True
            y_signal = SignalEvent(p0, dt, 'LONG', 1.0)
            x_signal = SignalEvent(p1, dt, 'SHORT', hr)

        # If we’re short the market and between the
        # absolute value of the low zscore threshold
        if abs(zscore_last) <= self.zscore_low and self.short_market:
            self.short_market = False
            y_signal = SignalEvent(p0, dt, 'EXIT', 1.0)
            x_signal = SignalEvent(p1, dt, 'EXIT', 1.0)

        return y_signal, x_signal

    def calculate_signals(self, event):
        """
        Generates a new set of signals based on the mean reversion
        strategy.
        Calculates the hedge ratio between the pair of tickers.
        We use OLS for this, although we should ideally use CADF.
        """

        if isinstance(event, MarketEvent):
            # Obtain the latest window of values for each
            # component of the pair of tickers
            x = self.bars.get_latest_bars_values(
                self.pair[0], "Close", N=self.ols_window
            )
            y = self.bars.get_latest_bars_values(
                self.pair[1], "Close", N=self.ols_window
            )

            # print(self.bars.get_latest_bars_values(
            #                                     self.pair[0], 
            #                                     "name", 
            #                                     N=self.ols_window
            #     )
            # )

            if y is not None and x is not None:
                # Check that all window periods are available
                if len(y) >= self.ols_window and len(x) >= self.ols_window:

                    xyt = self.bars.get_latest_bar_value(
                                                            symbol=self.pair[0], 
                                                            value_type="name",
                    )
                    datetime_obj = self.parse_time_with_timezone(xyt)
                    if (datetime_obj.hour == 15 and datetime_obj.minute > 50) or (16 <= datetime_obj.hour < 24) or (0 <= datetime_obj.hour < 9) or (datetime_obj.hour == 9 and datetime_obj.minute < 30):
                        print("after 3:50 exiting positions")
                        if self.long_market:
                            self.long_market = False
                            self.events.put(SignalEvent(self.pair[0], datetime_obj, 'EXIT', 1.0))
                            self.events.put(SignalEvent(self.pair[1], datetime_obj, 'EXIT', 1.0))

                        elif self.short_market:
                            self.short_market = False
                            self.events.put(SignalEvent(self.pair[0], datetime_obj, 'EXIT', 1.0))
                            self.events.put(SignalEvent(self.pair[1], datetime_obj, 'EXIT', 1.0))
                    else:
                        # Take the last 2 stock prices
                        last_2_prices_x = x[-2:]
                        last_2_prices_y = y[-2:]

                        # Create an array of indices representing time for these prices
                        time_indices_x = np.arange(len(x)-2, len(x))
                        time_indices_y = np.arange(len(y)-2, len(y))

                        # Perform linear regression
                        model_x = LinearRegression()
                        model_y = LinearRegression()
                        model_x.fit(time_indices_x.reshape(-1, 1), last_2_prices_x)
                        model_y.fit(time_indices_y.reshape(-1, 1), last_2_prices_y)

                        # Extract the slope
                        slope_x = model_x.coef_[0]
                        slope_y = model_y.coef_[0]

                        signs_opposite = np.all(slope_x == -slope_y)
                        
                        if signs_opposite:
                            # Calculate the current hedge ratio using OLS
                            self.hedge_ratio = sm.OLS(x, y).fit().params[0]

                            # Calculate the current z-score of the residuals
                            spread = x - self.hedge_ratio * y
                            zscore_last = ((spread - spread.mean()) / spread.std())[-1]

                            # Calculate signals and add to events queue
                            y_signal, x_signal = self.calculate_xy_signals(zscore_last, datetime_obj)
                            if y_signal is not None and x_signal is not None:
                                self.events.put(y_signal)
                                self.events.put(x_signal)
                                self.all_traded_dates.append(datetime_obj)

        # print(self.all_traded_dates)
