 
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.order import Order

from sklearn.linear_model import LinearRegression
from concurrent.futures import ThreadPoolExecutor
import statsmodels.api as sm
import pandas as pd
import numpy as np
import threading
import datetime
import asyncio
import time


# from ibapi.wrapper import EWrapper
# from ibapi.client import EClient
# from ibapi.contract import Contract
# from ibapi.order import Order

# import threading
# import numpy as np
# import time as TIME
# import datetime as dt

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}
        self.time = {}
        self.positions = {}

    def error(self, *args):
        print(f"Error: {args}")
        if args[1] == 504:  # This is the "Not Connected" error code
            print("Error 504: Ensure that TWS is running and that you've enabled API connections.")

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:
            self.data[reqId] = (price, datetime.datetime.now())
            self.cancelMktData(reqId)  # Cancel the market data subscription
            self.events[reqId].set()  # Signal that the data has been received

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        if status == "Filled":
            print(f"Order {orderId} has been filled at {avgFillPrice}!")

    def execDetails(self, reqId, contract, execution):
        print(f"Order executed: {execution.side} {execution.shares} {contract.symbol} at {execution.price}")

    def position(self, account, contract, position, avgCost):
        key = (contract.symbol, contract.secType, contract.currency, contract.exchange)
        self.positions[key] = {
            'position': position,
            'avgCost': avgCost
        }

class RollingWindow:
    def __init__(self, tickers, n):
        self.n = n
        self.windows = pd.DataFrame({ticker: pd.Series([np.nan] * n) for ticker in tickers})
        # self.windows = pd.DataFrame({ticker: pd.Series([pd.NA] * n) for ticker in tickers})

    def update(self, ticker, price):
        if ticker in self.windows:
            self.windows[ticker] = self.windows[ticker].shift(-1)
            self.windows.at[self.n - 1, ticker] = price

    def get_window(self, ticker):
        return self.windows.get(ticker)

class TickerIDManager:
    def __init__(self):
        self.current_id = 0
        self.ticker_to_id_map = {}

    def set_id(self, ticker):
        if ticker not in self.ticker_to_id_map:
            self.current_id += 1
            self.ticker_to_id_map[ticker] = self.current_id

    def get_id(self, ticker):
        return self.ticker_to_id_map[ticker]

ticker_id_manager = TickerIDManager()

class ReqIDManager:
    def __init__(self):
        self.last_id = 1
        self.current_id = 1

    def increment_id(self):
        self.last_id = self.current_id
        self.current_id += 1
    
    def get_id(self):
        return self.current_id

req_id_manager = ReqIDManager()

def create_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'CRYPTO' 
    contract.exchange = 'PAXOS'
    contract.currency = 'USD'

    """ Crypto
    contract.symbol = "ETH"
    contract.secType = "CRYPTO"
    contract.exchange = "PAXOS"
    contract.currency = "USD"
    """

    """ Stock
    contract.symbol = "SPY"
    contract.secType = 'STK' 
    contract.exchange = 'SMART'
    contract.currency = "USD"
    """

    """ Forex
    contract.symbol = "EUR"
    contract.secType = 'CASH' 
    contract.exchange = 'IDEALPRO'
    contract.currency = "USD"
    """
    return contract

def create_order(action, quantity, price=None):
    order = Order()
    order.action = action
    order.totalQuantity = quantity
    order.orderType = 'MKT'
    # order.orderType = 'LMT'
    # order.lmtPrice = price
    return order

def exit_position(app, contract):
    key = (contract.symbol, contract.secType, contract.currency, contract.exchange)
    if key in app.positions:
        quantity = app.positions[key]['position']
        if quantity > 0:  # Long position, so we sell
            return create_order('SELL', abs(quantity), None)
        elif quantity < 0:  # Short position, so we buy to cover
            return create_order('BUY', abs(quantity), None)
    return None

executor = ThreadPoolExecutor(max_workers=4)

async def lin_reg_xy(padas_date_price_x, padas_date_price_y):
    # lin_reg_x = []
    # lin_reg_y = []
    print("padas_date_price_x", padas_date_price_x)
    if len(padas_date_price_x) == len(padas_date_price_y):
        for itr in range(2, len(padas_date_price_x)):
            last_2_prices_x = padas_date_price_x[itr-2:itr]
            last_2_prices_y = padas_date_price_y[itr-2:itr]

            time_indices_x = np.arange(len(padas_date_price_x)-2, len(padas_date_price_x))
            time_indices_y = np.arange(len(padas_date_price_y)-2, len(padas_date_price_y))


            model_x = LinearRegression()
            model_y = LinearRegression()
            model_x.fit(time_indices_x.reshape(-1, 1), last_2_prices_x)
            model_y.fit(time_indices_y.reshape(-1, 1), last_2_prices_y)

            slope_x = model_x.coef_[0]
            slope_y = model_y.coef_[0]
            print("slope_x", slope_x)
            
            # lin_reg_x.append(slope_x)
            # lin_reg_y.append(slope_y)
    await asyncio.sleep(0.1)
    return slope_x, slope_y

def run_loop(app):
    app.run()

async def main():
    app = IBapi()
    app.connect('127.0.0.1', 7497, 123)

    # Start the run_loop function in a separate thread
    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()

    await asyncio.sleep(1)  # Wait for the price data to be updated
    # time.sleep(1)  # Wait for the price data to be updated

    app.reqPositions()  # Request current positions
    
    # ticker_groups = [ ['AAPL','SPY'], ["GME","AMC"], ["F","GM"] ]    
    # ticker_groups = [ ['EUR','GBP'], ["AUD","NZD"], ["CAD","JPY"] ]  
    # ticker_groups = [ ['BTC','ETH'], ["BCH","LTC"] ] # all crypto
    ticker_groups = [ ['BTC','ETH'] ] # all crypto
    contracts_groups = [[create_contract(ticker) for ticker in group] for group in ticker_groups]
    all_tickers = [ticker for group in ticker_groups for ticker in group]
    trail = 10
    rw = RollingWindow(all_tickers, trail)
    
    # windows_single_line = [RollingWindow([ticker], 10) for group in ticker_groups for ticker in group]

    app.events = {}  # Dictionary to store threading events for each ticker

    rw_full = 0
    while True:
        print()
        time.sleep(1)  # Check every 5 seconds
        for group in contracts_groups:
            for contract in group:
                order_id = req_id_manager.get_id()
                app.events[order_id] = threading.Event()  # Create an event for this ticker
                # app.reqMarketDataType(4)  # 4 is for delayed data. Use 1 for real-time data.
                app.reqMktData(
                    reqId=order_id, 
                    contract=contract, 
                    genericTickList='', 
                    snapshot=False, 
                    regulatorySnapshot=False,
                    mktDataOptions=[]
                )

                app.events[order_id].wait()  # Wait for the event to be set (i.e., data received)
                price, timestamp = app.data.get(order_id, (None, None))
                # print(f"price {price}")
                # print(f"time {timestamp}") 
                # print(f"@ {datetime.datetime.now()}")
                if price is not None:
                    # print(f"{contract.symbol}")
                    # print(f"{price}")
                    # print(f"{timestamp}")
                    rw.update(contract.symbol, price)  
                    print(f"{rw.get_window(contract.symbol)}")
                    # print()

                req_id_manager.increment_id()
            
            print(rw_full)
            if rw_full > trail:

                # print("group[0]", group[0].symbol)
                # print("group[1]", group[1].symbol)

                # type(x) <class 'pandas.core.series.Series'>
                x = [11, 12, 14, 12, 15, 16, 14, 18, 19, 21]
                y = [10, 11, 13, 11, 14, 15, 13, 17, 18, 20]
                # x = rw.get_window(group[0].symbol)
                # y = rw.get_window(group[1].symbol)
                print("x", x)

                lin_reg_x, lin_reg_y = await lin_reg_xy(x,y)
                print("type(lin_reg_x)", type(lin_reg_x))
                print("lin_reg_x", lin_reg_x)

                

                # signs_opposite = (lin_reg_x == -lin_reg_y).all()
                # print("signs_opposite", signs_opposite)


                # lin_reg_x_array = np.array(lin_reg_x)
                # lin_reg_y_array = np.array(lin_reg_y)
                # print("type(lin_reg_x_array)", type(lin_reg_x_array))
                # print("lin_reg_x_array", lin_reg_x_array)
                # signs_opposite = np.all(lin_reg_x_array == -lin_reg_y_array)

                # if signs_opposite: # IF ACTUALLY DIVERGING
                #     print("IF SIGNS OPPOSITE")
                    # hedge_ratio = sm.OLS(x, y).fit().params[0]
                    # spread = x - hedge_ratio * y
                    # zscore_last = ((spread - spread.mean()) / spread.std())[-1]
                    # print("hedge_ratio", hedge_ratio)
                    # print("spread", spread)
                    # print("zscore_last", zscore_last)


                # if zscore_last <= - zscore_high and not long_market:
                #     long_market = True
                #     # SHORT group[0] # # y_signal = SignalEvent(p0, dt, 'SHORT', 1.0)
                #     # LONG group[1] # # x_signal = SignalEvent(p1, dt, 'LONG', hr)
                    
                # if abs(zscore_last) <= zscore_low and long_market:
                #     long_market = False
                #     # EXIT group[0] # # y_signal = SignalEvent(p0, dt, 'EXIT', 1.0)
                #     # EXIT group[1] # # x_signal = SignalEvent(p1, dt, 'EXIT', 1.0)

                # if zscore_last >= zscore_high and not short_market:
                #     short_market = True
                #     # LONG group[0] # # y_signal = SignalEvent(p0, dt, 'LONG', 1.0)
                #     # SHORT group[1] # # x_signal = SignalEvent(p1, dt, 'SHORT', hr)

                # if abs(zscore_last) <= zscore_low and short_market:
                #     short_market = False
                #     # EXIT group[0] # # y_signal = SignalEvent(p0, dt, 'EXIT', 1.0)
                #     # EXIT group[1] # # x_signal = SignalEvent(p1, dt, 'EXIT', 1.0)

            rw_full += 1
    app.disconnect()

if __name__ == "__main__":
    asyncio.run(main())



"""    
Error: (-1, 2104, 'Market data farm connection is OK:usfarm.nj', '')
Error: (-1, 2104, 'Market data farm connection is OK:usfarm', '')
Error: (-1, 2106, 'HMDS data farm connection is OK:euhmds', '')
Error: (-1, 2106, 'HMDS data farm connection is OK:fundfarm', '')
Error: (-1, 2106, 'HMDS data farm connection is OK:ushmds', '')
Error: (-1, 2158, 'Sec-def data farm connection is OK:secdefil', '')

Error: (1, 504, 'Not connected')
Error 504: Ensure that TWS is running and that you've enabled API connections.
"""




















