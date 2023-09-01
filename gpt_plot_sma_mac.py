from data import HistoricCSVDataHandler
from mac import MovingAverageCrossStrategy
from portfolio import Portfolio
from execution import SimulatedExecutionHandler
from backtest import Backtest
import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import queue
NaivePortfolio = Portfolio.generate_naive_order


# Set the CSV file path
csv_dir = '/Users/walkerhutchinson/Desktop/CODE/'

# Set the symbol list
symbol_list = ['AAPL']

# Set the initial capital
initial_capital = 100000.0

# Set the heartbeat (pause between each processing of the event queue)
heartbeat = 0.0

# Set the dates
start_date = datetime.datetime(2000, 1, 1)
end_date = datetime.datetime(2020, 12, 31)

# Set the moving averages parameters
short_window = 100
long_window = 400

# Create the events queue
events = queue.Queue()

# Create the DataHandler, Strategy, Portfolio, and ExecutionHandler
bars = HistoricCSVDataHandler(events, csv_dir, symbol_list)
strategy = MovingAverageCrossStrategy(bars, events, short_window, long_window)
port = NaivePortfolio(bars, events, strategy, start_date, initial_capital)
broker = SimulatedExecutionHandler(events)

# Create the Backtest
bt = Backtest(csv_dir, symbol_list, initial_capital, heartbeat, start_date, end_date, 
              HistoricCSVDataHandler, SimulatedExecutionHandler, NaivePortfolio, MovingAverageCrossStrategy,
              short_window=short_window, long_window=long_window)

# Run the Backtest
bt.simulate_trading()

# Get the equity curve DataFrame
equity_curve = port.equity_curve

# Calculate the short and long moving averages of the adjusted close prices
short_sma = equity_curve['total'].rolling(window=short_window).mean()
long_sma = equity_curve['total'].rolling(window=long_window).mean()

# Plot the adjusted close prices and the moving averages
plt.figure(figsize=(10,7))
plt.plot(equity_curve.index, equity_curve['total'], label='Adj Close')
plt.plot(equity_curve.index, short_sma, label=f'Short SMA ({short_window} periods)')
plt.plot(equity_curve.index, long_sma, label=f'Long SMA ({long_window} periods)')
plt.title('Adjusted Close Prices and SMA')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.grid()
plt.show()
