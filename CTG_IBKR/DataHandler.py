

# dunder over-ride
from __future__ import print_function

# event driven structure imports
from Events import MarketEvent

# python3 base code import
from abc import ABCMeta, abstractmethod

# ibapi imports
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

# package imports
import datetime as dt
import yfinance as yf
import pandas as pd
import numpy as np
import time
import os




class DataManagement(object):
    """
    Data management class implemented in an abstract manner to handle different
    types of datafeed (coming from database, webscraping, direct datafeed, csv, etc..)
    this generates a Market event in the back test loop
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bar(self, symbol):
        """
        Returns the last bar updated.
        """
        raise NotImplementedError("Should implement get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars updated.
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the last bar.
        """
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        """
        Returns one of the Open, High, Low, Close, Volume or OI
        from the last bar.
        """
        raise NotImplementedError("Should implement get_latest_bar_value()")

    @abstractmethod
    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Returns the last N bar values from the
        latest_symbol list, or N-k if less available.
        """
        raise NotImplementedError("Should implement get_latest_bars_values()")

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bars to the bars_queue for each symbol
        in a tuple OHLCVI format: (datetime, open, high, low,
        close, volume, adj closing price).
        """
        raise NotImplementedError("Should implement update_bars()")



class IBKRDataHandler(EWrapper, EClient, DataManagement):
    """
    Link to IBKR TWS python api for live tick-by-tick (time adjusted) data
    for trading
    """
    def __init__(self, events, symbols, interval="1 min"):
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        super().__init__()
        self.symbol_list = symbols
        self.continue_backtest = True
        self.events = events  # Set events as an instance attribute
        self.interval = interval
        self.contracts = {} # Map to associate request ID to a ticker
        self.reqId = 1
        self.symbol_data = {}
        self.latest_symbol_data = {}

        # Connect to TWS
        self.connect('127.0.0.1', 7497, 123)  # Use your own clientId

        for symbol in self.symbol_list:
            contract = Contract()
            contract.symbol = symbol
            contract.secType = 'STK'
            contract.exchange = 'SMART'
            contract.currency = 'USD'
            self.contracts[self.reqId] = contract
            self.reqId += 1

        # To store the latest bars
        self.latest_bars_list = {symbol: [] for symbol in symbols}
        
        self.interval = interval

    # def _start_market_data_stream(self):
    #     for reqId, contract in self.contracts.items():
    #         self.reqHistoricalData(reqId, contract, "", self.interval, "1 D", "TRADES", 1, 1, False, [])

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:  # Last traded price
            contract = self.contracts.get(reqId)
            if contract:
                symbol = contract.symbol
                timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                self.latest_bars_list[symbol].append((timestamp, price))
                print(f"Received data for {symbol} at {timestamp}: Price {price}")  # Add this line

            self.cancelMktData(reqId)  # Cancel the market data subscription after getting the price

    # def _get_new_request_id(self):
    #     self.request_id_counter += 1
    #     return self.request_id_counter

    # def _subscribe_market_data(self, symbol):
    #     contract = Contract()
    #     contract.symbol = symbol
    #     contract.secType = 'STK'
    #     contract.exchange = 'SMART'
    #     contract.currency = 'USD'
        
    #     reqId = self._get_new_request_id()
    #     self.contracts[reqId] = contract
    #     self.reqMktData(reqId, contract, '', False, False, [])

    # def _start_data_retrieval_loop(self):
    #     while True:
    #         for reqId, contract in self.contracts.items():
    #             self.reqMktData(reqId, contract, '', False, False, [])
    #         time.sleep(self.interval)

    # def get_latest_bar(self, symbol):
    #     return self.latest_bars.get(symbol, None)
    # def get_latest_bar(self):
    #     """
    #     Return the most recent price for a given symbol.
    #     """
    #     for bar in self.latest_bars_list[symbol][-1]:
    #         yield bar
    def get_latest_bar(self, symbol):
        """
        Return the most recent price for a given symbol.
        """
        return self.latest_bars_list[symbol][-1]
                
        # for symbol in self.symbol_list:
        #     try:
        #         bar = next(self._get_new_bar(symbol))
        #     except StopIteration:
        #         self.continue_backtest = False
        #     else:
        #         if bar is not None:
        #             self.latest_symbol_data[symbol].append(bar)
    
    # def _get_new_bar(self, symbol):
    #     """
    #     Appends a new bar (price) to the bar list for the given symbol.
    #     """
    #     for bar in self.symbol_data[symbol]:
    #         yield bar

    #     self.latest_bars_list[symbol].append((datetime.now(), price))

    def get_latest_bar_datetime(self, symbol):
        """
        Return the datetime of the most recent price.
        """
        return self.latest_bars_list[symbol][-1][0]

    def get_latest_bar_value(self, symbol, value_type):
        """
        Return a specific attribute (e.g., close price) of the latest bar for a given symbol.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1][1], value_type)

    def get_latest_bars_values(self, symbol, value_type, N=1):
        """
        Return a list of specific attributes (e.g., close prices) for the last N bars.
        """
        bars_list = self.latest_symbol_data[symbol][-N:]
        return getattr(bars_list[-1][1], value_type)       

    def get_latest_bars(self, symbol, N=1):
        """
        Return the last N prices for a given symbol.
        """
        return self.latest_bars_list[symbol][-N:]

    # def update_bars(self):
    #     for symbol in self.symbol_list:
    #         try:
    #             self.tickPrice()
    #             bar = next(self.get_latest_bar(symbol))
    #         except StopIteration:
    #             self.continue_backtest = False
    #         else:
    #             if bar is not None:
    #                 self.latest_symbol_data[symbol].append(bar)
    #     self.events.put(MarketEvent())
    def update_bars(self):
        for reqId, contract in self.contracts.items():
            self.reqMktData(reqId, contract, '', False, False, [])
        
        # Allow some time for the tickPrice method to be called and data to be updated
        time.sleep(1)
        
        for symbol in self.symbol_list:
            try:
                bar = next(self.get_latest_bar(symbol))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol].append(bar)
        
        # Put a MarketEvent to indicate that new data has been added
        self.events.put(MarketEvent())



class YahooDataHandler(DataManagement):
    """
    Get data directly from Yahoo Finance website, and provide an interface
    to obtain the "latest" bar in a manner identical to a live
    trading interface.
    """

    def __init__(self, events, symbol_list, interval, start_date, end_date):
        """
        Initialize Queries from yahoo finance api to
        receive historical data transformed to dataframe

        Parameters:
        events - The Event Queue.
        symbol_list - A list of symbol strings.
        interval - 1d, 1wk, 1mo - daily, weekly monthly data
        start_date - starting date for the historical data (format: datetime)
        end_date - final date of the data (format: datetime)
        """

        self.events = events
        self.symbol_list = symbol_list
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True
        self._load_data_from_Yahoo_finance()

    def _load_data_from_Yahoo_finance(self):
        """
        Queries yfinance api to receive historical data in csv file format
        """

        combined_index = None
        for symbol in self.symbol_list:

            # download data from yfinance for symbol. This could be improved as yfinance can download several
            # symbols at the same time
            self.symbol_data[symbol] = yf.download(tickers=[symbol], start=self.start_date,
                                                   end=self.end_date, interval=self.interval)
            # rename columns for consistency
            self.symbol_data[symbol].rename(columns={'Open': 'open',
                                                     'High': 'high',
                                                     'Low': 'low',
                                                     'Close': 'close',
                                                     'Adj Close': 'adj_close',
                                                     'Volume': 'volume'}, inplace=True)

            # rename index as well from 'Date' to 'datetime'
            self.symbol_data[symbol].index.name = 'datetime'

            # create returns column (used for some strategies)
            self.symbol_data[symbol]['returns'] = self.symbol_data[symbol]["adj_close"].pct_change() * 100.0

            # Combine the index to pad forward values
            if combined_index is None:
                combined_index = self.symbol_data[symbol].index
            else:
                combined_index.union(self.symbol_data[symbol].index)

            # Set the latest symbol_data to None
            self.latest_symbol_data[symbol] = []

        # Reindex the dataframes
        for symbol in self.symbol_list:
            self.symbol_data[symbol] = self.symbol_data[symbol].reindex(index=combined_index, method="pad").iterrows()

    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed as a tuple of
        (symbol, datetime, open, low, high, close, volume, adj_close, etc).
        """
        for bar in self.symbol_data[symbol]:
            yield bar

    def get_latest_bar(self, symbol):
        """
        Returns the last bar from the latest_symbol list.
        """

        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or N-k if less available.
        """

        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the last bar.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, value_type):
        """
        Returns one of the Open, High, Low, Close, Volume or OI
        values from the pandas Bar series object.
        """
        print("bars_list", bars_list)
        return bars_list

        # try:
        #     bars_list = self.latest_bars_list[symbol]
        #     print("bars_list", bars_list)
        # except KeyError:
        #     print("That symbol is not available in the current data set.")
        #     raise
        # else:
        #     if value_type == "datetime":
        #         print("bars_list[-1][0]", bars_list[-1][0])
        #         return bars_list[-1][0]
        #     elif value_type == "price":
        #         print("bars_list[-1][1]", bars_list[-1][1])
        #         return bars_list[-1][1]
            # else:
            #     raise KeyError(f"{value_type} is not a recognized value type for IBKRDataHandler.")

    def get_latest_bars_values(self, symbol, value_type, N=1):
        """
        Returns the last N bar values from the
        latest_symbol list, or N-k if less available.
        """
        try:
            bars_list = self.get_latest_bars(symbol, N)  # bars_list = bars_list[-N:]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return np.array([getattr(bar[1], value_type) for bar in bars_list])

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """
        for symbol in self.symbol_list:
            try:
                bar = next(self._get_new_bar(symbol))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol].append(bar)
        self.events.put(MarketEvent())


class HistoricCSVDataHandler(DataManagement):
    """
    HistoricCSVDataHandler is designed to read CSV files for
    each requested symbol from disk and provide an interface
    to obtain the "latest" bar in a manner identical to a live
    trading interface.
    """

    def __init__(self, events, csv_dir, symbol_list):

        """
        Initialises the historic data handler by requesting
        the location of the CSV files and a list of symbols.
        It will be assumed that all files are of the form
        'symbol.csv', where symbol is a string in the list.
        Parameters:
        events - The Event Queue.
        csv_dir - Absolute directory path to the CSV files.
        symbol_list - A list of symbol strings.
        """

        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True
        self._data_conversion_from_csv_files()

    def _data_conversion_from_csv_files(self):
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a symbol dictionary.
        """

        combined_index = None
        for symbol in self.symbol_list:
            # Load the CSV file with no header information, indexed on date
            self.symbol_data[symbol] = pd.io.parsers.read_csv(
                os.path.join(self.csv_dir, "%s.csv" % symbol),
                header=0, index_col=0,
                # names=["datetime", "open", "high", "low", "close", "adj_close", "volume"]
                # names=["timestamp", "open", "high", "low", "close", "volume"]
                names=["Date", "Open", "High", "Low", "Close", "Volume"]
            )

            # Combine the index to pad forward values
            if combined_index is None:
                combined_index = self.symbol_data[symbol].index
            else:
                combined_index.union(self.symbol_data[symbol].index)

            # Set the latest symbol_data to None
            self.latest_symbol_data[symbol] = []

        # Reindex the dataframes
        for symbol in self.symbol_list:
            self.symbol_data[symbol] = self.symbol_data[symbol].reindex(index=combined_index, method="pad").iterrows()

    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed as a tuple of
        (symbol, datetime, open, low, high, close, volume, adj_close).
        """
        for bar in self.symbol_data[symbol]:
            yield bar

    def get_latest_bar(self, symbol):
        """
        Returns the last bar from the latest_symbol list.
        """

        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or N-k if less available.
        """

        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the last bar.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, value_type):
        """
        Returns one of the Open, High, Low, Close, Volume or OI
        values from the pandas Bar series object.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1][1], value_type)

    def get_latest_bars_values(self, symbol, value_type, N=1):
        """
        Returns the last N bar values from the
        latest_symbol list, or N-k if less available.
        """
        try:
            bars_list = self.get_latest_bars(symbol, N)  # bars_list = bars_list[-N:]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return np.array([getattr(bar[1], value_type) for bar in bars_list])

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """
        for symbol in self.symbol_list:
            try:
                bar = next(self._get_new_bar(symbol))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol].append(bar)
        self.events.put(MarketEvent())


'''
class HistoricMySQLDataHandler(DataManagement):
    """
    HistoricMySQLDataHandler is designed to read a MySQL database for each requested symbol from disk and 
    provide an interface to obtain the "latest" bar in a manner identical to a live trading interface.
    """

    def __init__(self, events, db_host, db_user, db_pass, db_name, symbol_list):

        """
        Initialises the historic data handler by requesting
        the location of the database and a list of symbols.
        It will be assumed that all price data is in a table called 
        'symbols', where the field 'symbol' is a string in the list.
        Parameters:
        events - The Event Queue.
        db_host - host of the database
        db_user - database user
        db_pass - password to access database
        db_name - database's name
        symbol_list - A list of symbol stringss
        """

        self.events = events
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name  

        self.symbol_list = symbol_list
        self.symbol_data = {}
        self.latest_symbol_data = {}

        self.continue_backtest = True
        self._data_conversion_from_database()


    def _get_data_from_database(self, symbol, columns):
        try:
            connection = MySQLdb.connect(host=self.db_host, user=self.db_user, passwd=self.db_pass, db=self.db_name)
        except MySQLdb.Error as e:  
            print("Error:%d:%s" % (e.args[0], e.args[1]))

        sql = SELECT {},{},{},{},{},{},{}
                FROM {}.format(columns[0],
                                    columns[1],
                                        columns[2],
                                            columns[3],
                                              columns[4],
                                                columns[5],
                                                    columns[6],
                                                        symbol)

        return pd.read_sql_query(sql, con=connection, index_col="datetime")

    def _data_conversion_from_database(self):
        """
        Opens the database files, converting them into 
        pandas DataFrames within a symbol dictionary.
        For this handler it will be assumed that the data is
        assumed to be stored in a database with similar columns 
        as the pandas dataframes. Thus, the format will be respected.
        """

        combined_index = None
        columns = ["datetime","open","high","low","close","volume","adj_close"]

        for symbol in self.symbol_list:
            self.symbol_data[symbol] = self._get_data_from_database(symbol, columns)


            # Combine the index to pad forward values
            if combined_index is None:
                combined_index = self.symbol_data[symbol].index
            else:
                combined_index.union(self.symbol_data[symbol].index)

            # Set the latest symbol_data to None
            self.latest_symbol_data[symbol] = []

        # Reindex the dataframes
        for symbol in self.symbol_list:
            self.symbol_data[symbol] = self.symbol_data[symbol].reindex(index=combined_index, method="pad").iterrows()

    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed as a tuple of 
        (symbol, datetime, open, low, high, close, volume, adj_close).
        """
        for bar in self.symbol_data[symbol]:
            yield bar


    def get_latest_bar(self, symbol):
        """
        Returns the last bar from the latest_symbol list.
        """

        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or N-k if less available.
        """

        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the last bar.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, value_type):
        """
        Returns one of the Open, High, Low, Close, Volume or OI
        values from the pandas Bar series object.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
                print("That symbol is not available in the historical data set.")
                raise
        else:
            return getattr(bars_list[-1][1], value_type)


    def get_latest_bars_values(self, symbol, value_type, N=1):
        """
        Returns the last N bar values from the
        latest_symbol list, or N-k if less available.
        """
        try:
            bars_list = self.get_latest_bars(symbol, N) # bars_list = bars_list[-N:]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return np.array([getattr(bar[1], value_type) for bar in bars_list])

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """
        for symbol in self.symbol_list:
            try:
                bar = next(self._get_new_bar(symbol))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol].append(bar)
        self.events.put(MarketEvent())
'''