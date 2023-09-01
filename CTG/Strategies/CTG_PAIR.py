

from Events import MarketEvent, SignalEvent
from Strategy import Strategy

from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import statsmodels.api as sm
import pandas as pd
import numpy as np
import datetime
import pytz



class CointegratedPair(Strategy):
    """
    Uses ordinary least squares (OLS) to perform a rolling linear
    regression to determine the hedge ratio between a pair of equities.
    The z-score of the residuals time series is then calculated in a
    rolling fashion and if it exceeds an interval of thresholds
    (defaulting to [0.5, 3.0]) then a long/short signal pair are generated
    (for the high threshold) or an exit signal pair are generated (for the
    low threshold).
    """

    def __init__(self, bars, events, ols_window=1000):
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
        self.pair         = tuple(self.symbol_list)
        self.datetime     = datetime.datetime.utcnow()
        self.long_market  = False
        self.short_market = False

        self.all_residuals = []
        self.all_bars_datetime = []

    def parse_time_with_timezone(self, time_str):
        # Split the string into the datetime and timezone parts
        dt_str, tz_str = time_str.rsplit(' ', 1)
        
        # Parse the datetime part
        dt = datetime.datetime.strptime(dt_str, '%Y%m%d %H:%M:%S')
        
        # Attach the timezone information if it exists
        if tz_str in pytz.all_timezones:
            dt = dt.replace(tzinfo=pytz.timezone(tz_str))
        
        return dt

    def calculate_p_signals(self, position_signal, timestamp):
        """
        Calculates the actual signal pairings
        to be sent to the signal generator.
        Parameters
        """
        p0_signal = None
        p1_signal = None
        p0       = self.pair[0] # ticker 1
        p1       = self.pair[1] # ticker 2
        dt       = self.datetime

        if position_signal == 0: # crosses 0
            self.long_market = False
            p0_signal = SignalEvent(
                                    symbol=p0, 
                                    datetime=timestamp, 
                                    signal_type='EXIT', 
                                    strength=1.0
            )
            p1_signal = SignalEvent(
                                    symbol=p1, 
                                    datetime=timestamp,
                                    signal_type='EXIT', 
                                    strength=1.0
            )

        if position_signal == 1: # converges a positive residual
            self.long_market = True
            p0_signal = SignalEvent(
                                    symbol=p0, 
                                    datetime=timestamp,
                                    signal_type='SHORT', 
                                    strength=1.0
            )
            p1_signal = SignalEvent(
                                    symbol=p1, 
                                    datetime=timestamp,
                                    signal_type='LONG', 
                                    strength=1.0
            )
            
        if position_signal == 2: # converges a negative residual
            self.short_market = True
            p0_signal = SignalEvent(
                                    symbol=p0, 
                                    datetime=timestamp, 
                                    signal_type='LONG', 
                                    strength= 1.0
            )
            p1_signal = SignalEvent(
                                    symbol=p1, 
                                    datetime=timestamp, 
                                    signal_type='SHORT', 
                                    strength=1.0
            )

        return p0_signal, p1_signal

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
                                                symbol=self.pair[0], 
                                                value_type="Close", 
                                                N=self.ols_window
            )
            y = self.bars.get_latest_bars_values(
                                                symbol=self.pair[1], 
                                                value_type="Close",
                                                N=self.ols_window
            )
            xyt = self.bars.get_latest_bar_value(
                                                symbol=self.pair[0], 
                                                value_type="name",
            )

            datetime_obj = self.parse_time_with_timezone(xyt)

            if y is not None and x is not None:
                # Check that all window periods are available
                if len(y) >= self.ols_window and len(x) >= self.ols_window:

                    # Calculate optimal hedge ratio "beta" via Statsmodels
                    model = sm.OLS(x, y)
                    res = model.fit()
                    beta_hr = res.params[0]

                    # Calculate the residuals of the linear combination
                    residuals = x - beta_hr * y

                    # Check for residuals crossing or near zero
                    # epsilon = 0.1  # Define what you consider to be 'near zero'
                    curr_residual = residuals[-1] * 10
                    last_residual = residuals[-2] * 10

                    # Take the last 20 stock prices
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
                    # print(round(curr_residual * 10, 3), round(curr_residual * 100, 3))

                    # if abs(value) <= epsilon:
                    #     # print(f"Residual is near zero on {date}")
                    #     continue

                    self.all_residuals.append(curr_residual)
                    self.all_bars_datetime.append(datetime_obj)

                    if (datetime_obj.hour == 15 and datetime_obj.minute > 50) or (16 <= datetime_obj.hour < 24) or (0 <= datetime_obj.hour < 9) or (datetime_obj.hour == 9 and datetime_obj.minute < 30):
                        # exit all positions with 10 minutes left for the trading day
                        p0_signal, p1_signal = self.calculate_p_signals(position_signal=0, timestamp=xyt)
                        if p0_signal is not None and p1_signal is not None:
                            self.events.put(p0_signal)
                            self.events.put(p1_signal)
                    
                    elif (last_residual < 0 and curr_residual > 0) or (last_residual > 0 and curr_residual < 0):
                        # elif residual crosses zero
                        # Calculate signals and add to events queue
                        p0_signal, p1_signal = self.calculate_p_signals(position_signal=0, timestamp=xyt)
                        if p0_signal is not None and p1_signal is not None:
                            self.events.put(p0_signal)
                            self.events.put(p1_signal)

                    elif signs_opposite: 
                        # time is not between 3:50pm and 9:30am
                        # and
                        # 

                        if (last_residual > 1 and curr_residual < 1):
                            # Calculate signals and add to events queue
                            p0_signal, p1_signal = self.calculate_p_signals(position_signal=1, timestamp=xyt)
                            if p0_signal is not None and p1_signal is not None:
                                self.events.put(p0_signal)
                                self.events.put(p1_signal)
                            # print(f"\nResidual converging past 1 on {self.bars.get_latest_bar_datetime(self.pair[0])}:")
                            # print(f"\nResidual converging past 1 on {self.bars.get_latest_bar_datetime(self.pair[1])}:")
                            # print("last_residual", last_residual)
                            # print("curr_residual", curr_residual)

                        if (last_residual > 2 and curr_residual < 2):
                            # Calculate signals and add to events queue
                            p0_signal, p1_signal = self.calculate_p_signals(position_signal=1, timestamp=xyt)
                            if p0_signal is not None and p1_signal is not None:
                                self.events.put(p0_signal)
                                self.events.put(p1_signal)
                            # print(f"\nResidual converging past 2 on {self.bars.get_latest_bar_datetime(self.pair[0])}:")
                            # print(f"\nResidual converging past 2 on {self.bars.get_latest_bar_datetime(self.pair[1])}:")
                            # print("last_residual", last_residual)
                            # print("curr_residual", curr_residual)

                        if (last_residual > 3 and curr_residual < 3):
                            # Calculate signals and add to events queue
                            p0_signal, p1_signal = self.calculate_p_signals(position_signal=1, timestamp=xyt)
                            if p0_signal is not None and p1_signal is not None:
                                self.events.put(p0_signal)
                                self.events.put(p1_signal)
                            # print(f"\nResidual converging past 3 on {self.bars.get_latest_bar_datetime(self.pair[0])}:")
                            # print(f"\nResidual converging past 3 on {self.bars.get_latest_bar_datetime(self.pair[1])}:")
                            # print("last_residual", last_residual)
                            # print("curr_residual", curr_residual)


                        if (last_residual < -1 and curr_residual > -1):
                            # Calculate signals and add to events queue
                            p0_signal, p1_signal = self.calculate_p_signals(position_signal=2, timestamp=xyt)
                            if p0_signal is not None and p1_signal is not None:
                                self.events.put(p0_signal)
                                self.events.put(p1_signal)
                            # print(f"\nResidual converging past -1 on {self.bars.get_latest_bar_datetime(self.pair[0])}:")
                            # print("last_residual", last_residual)
                            # print("curr_residual", curr_residual)

                        if (last_residual < -2 and curr_residual > -2):
                            # Calculate signals and add to events queue
                            p0_signal, p1_signal = self.calculate_p_signals(position_signal=2, timestamp=xyt)
                            if p0_signal is not None and p1_signal is not None:
                                self.events.put(p0_signal)
                                self.events.put(p1_signal)
                            # print(f"\nResidual converging past -2 on {self.bars.get_latest_bar_datetime(self.pair[0])}:")
                            # print("last_residual", last_residual)
                            # print("curr_residual", curr_residual)

                        if (last_residual < -3 and curr_residual > -3):
                            # Calculate signals and add to events queue
                            p0_signal, p1_signal = self.calculate_p_signals(position_signal=2, timestamp=xyt)
                            if p0_signal is not None and p1_signal is not None:
                                self.events.put(p0_signal)
                                self.events.put(p1_signal)
                            # print(f"\nResidual converging past -3 on {self.bars.get_latest_bar_datetime(self.pair[0])}:")
                            # print("last_residual", last_residual)
                            # print("curr_residual", curr_residual)

    def plot_data(self):
        # Plot the adjusted close prices and the moving averages
        plt.figure(figsize=(10,7))
        plt.plot(
                self.all_bars_datetime, 
                self.all_residuals, 
                label='f gm'
        ) 

        plt.title('Adjusted Close Prices and SMA')
        plt.xlabel('Date')
        plt.ylabel('res')
        plt.legend()
        plt.grid()
        plt.show() 