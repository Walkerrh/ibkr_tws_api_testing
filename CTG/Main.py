"""
Main program to run a backtest for a particular strategy
"""

# Importing some packages
from datetime import datetime
from pathlib import Path

# Import the different components of the backtester
from BacktesterLoop import Backtest
from DataHandler import YahooDataHandler, HistoricCSVDataHandler
from Execution import SimpleSimulatedExecutionHandler
from Portfolio import Portfolio
 
from Strategies.OLS_MR_Strategy import OLSMRStrategy
from Strategies.ETF_Forecast import ETFDailyForecastStrategy
from Strategies.MAC_Strat import MovingAverageCrossOverStrat
from Strategies.CTG_PAIR import CointegratedPair


if __name__ == "__main__":
    # data_dir = Path.cwd() / 'z_CPED/DataDir/Short_file'  # For reading from CSV files
    data_dir = Path.cwd() / 'CTG/DataDir'  # For reading from CSV files
    symbol_list = ["F", "GM"]  
    initial_capital = 100000.0
    start_date = datetime(2011, 1, 1, 0, 0, 0)
    end_date = datetime(2016, 1, 1, 0, 0, 0)
    interval = '1m'
    heartbeat = 0.0  # necessary for live feed

    backtest = Backtest(data_dir          = data_dir,  # data directory of CSV files
                        symbol_list       = symbol_list,  # list of symbols
                        initial_capital   = initial_capital,  # initial capital available for trading
                        heartbeat         = heartbeat,  # heartbeat to count time in real live trading simulation
                        start_date        = start_date,  # starting time of the trading
                        end_date          = end_date,  # ending time of the trading
                        interval          = interval,  # interval of the data
                        data_handler      = HistoricCSVDataHandler,  # data management method
                        execution_handler = SimpleSimulatedExecutionHandler,  # Type of execution in relationship to broker
                        portfolio         = Portfolio,  # portfolio management method
                        strategy          = OLSMRStrategy # strategy chosen
    )  

    backtest.simulate_trading()

