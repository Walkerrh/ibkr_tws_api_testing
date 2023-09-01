 
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
        self.next_order_id = None  # To store the next valid order ID
        self.nextValidOrderId = None
        self.TotalCashValue = None

    def error(self, *args):
        print(f"Error: {args}")
        if args[1] == 504:  # This is the "Not Connected" error code
            print("Error 504: Ensure that TWS is running and that you've enabled API connections.")

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:
            self.data[reqId] = (price, datetime.datetime.now())
            self.cancelMktData(reqId)  # Cancel the market data subscription
            self.events[reqId].set()  # Signal that the data has been received

    # def nextValidId(self, orderId: int):
    #     """ Callback that receives the next valid order ID """
    #     super().nextValidId(orderId)
    #     print(f"Received next valid order ID: {self.next_order_id}")
    #     return orderId

    # @iswrapper
    def accountSummary(self, reqId:int, account:str, tag:str, value:str, currency:str):
        # if tag == "AvailableFunds": # or whatever you want
        # print(value)
        
        self.TotalCashValue = self.reqAccountSummary(self.nextValidOrderId, "All", tags = "TotalCashValue") # "$LEDGER")
        # self.totalCashValue = value
        return self.TotalCashValue


  

    def position(self, account, contract, pos, avgCost):
        index = str(account)+str(contract.symbol)
        self.all_positions.loc[index]= account, contract.symbol, pos, avgCost, contract.secType


    def nextValidId(self, orderId: int):
        """ Callback that receives the next valid order ID """
        super().nextValidId(orderId)
        # logging.debug("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId
        print("nextValidOrderId:", self.nextValidOrderId)
    
    # reqContractDetails(orderId, mycoontract)

    def request_contract_details(self, contract):
        self.reqContractDetails(1, contract)
    
    # def contractDetails(self, reqId, contractDetails):
    #     print(contractDetails)
    
    def openOrder(self, orderId, contract, order, orderState):
        print(f"orderId: {orderId}, contract: {contract}, order:{order}")

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        if status == "Filled":
            print(f"Order {orderId} has been filled at {avgFillPrice}!")

    def execDetails(self, reqId, contract, execution):
        print(f"Order executed: {execution.side} {execution.shares} {contract.symbol} at {execution.price}")

    def position(self, account, contract, position, avgCost):
        """   
        contract:
            conId
            symbol
            lastTradeDateOrContractMonth
            strike
            right
            multiplier
            exchange
            primaryExchange
            currency
            localSymbol
            tradingClass
            includeExpired
            secIdType
            secId
            comboLegsDescrip
            comboLegs
            position
            Average Cost  
        position     
        avgCost
        """
        print()
        print(f"conId: {contract.conId},\nsymbol: {contract.symbol},\nlastTradeDateOrContractMonth: {contract.lastTradeDateOrContractMonth},\nstrike: {contract.strike},\nright: {contract.right},\nmultiplier: {contract.multiplier},\nexchange: {contract.exchange},\nprimaryExchange: {contract.primaryExchange},\ncurrency: {contract.currency},\nlocalSymbol: {contract.localSymbol},\ntradingClass: {contract.tradingClass},\nincludeExpired: {contract.includeExpired},\nsecIdType: {contract.secIdType},\nsecId: {contract.secId},\ncomboLegsDescrip: {contract.comboLegsDescrip},\ncomboLegs: {contract.comboLegs},\nposition: {position},\nAverage Cost: {avgCost}")

    # def position(self, account, contract, position, avgCost):
    #     key = (contract.symbol, contract.secType, contract.currency, contract.exchange)
    #     self.positions[key] = {
    #         'position': position,
    #         'avgCost': avgCost
    #     }

    # # Method to request account summary for cash balance
    # def request_account_summary(self):
    #     # Requesting account summary for cash balance
    #     # The tag 'TotalCashValue' will give the total cash balance
    #     self.reqAccountSummary(1, "All", "TotalCashValue")

    # # Handling the returned account summary
    # def accountSummary(self, reqId, account, tag, value, currency):
    #     if tag == "TotalCashValue":
    #         # self.cash_balance = float(value)
    #         print(f"Total Cash Balance: {value}")

    # # Method to retrieve open positions
    # def get_open_positions(self):
    #     return self.positions


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
            self.current_id += 2
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
        self.current_id += 2
    
    def get_id(self):
        return self.current_id

req_id_manager = ReqIDManager()

class ReqOrderId:
    def __init__(self):
        self.last_id = 2
        self.current_id = 2

    def increment_id(self):
        self.last_id = self.current_id
        self.current_id += 2
    
    def get_id(self):
        return self.current_id

req_orderid_manager = ReqOrderId()

def create_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK' 
    contract.exchange = 'SMART'
    contract.currency = "USD"
    # contract.tradingClass = 'MNQ'

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
    order.totalQuantity = quantity # for stock
    order.cashQty = 1000 # for crypto
    order.orderType = 'MKT'
    order.tif = "DAY" # or GTC, IOC, GTD (needs order.goodTillDate)
    order.account = "DU7518334"
    # order.orderType = 'LMT'
    # order.lmtPrice = price
    return order

def exit_position(app, contract):
    key = (contract.symbol, contract.secType, contract.currency, contract.exchange)
    if key in app.positions:
        quantity = app.positions[key]['position']
        if quantity > 0:  # Long position, so we sell
            # return create_order('SELL', abs(quantity), None)
            print("SELL", abs(quantity))
        elif quantity < 0:  # Short position, so we buy to cover
            # return create_order('BUY', abs(quantity), None)
            print("BUY", abs(quantity))
    return None

def get_z_score(x_data, y_data):
    model = sm.OLS(x_data, y_data) 
    res = model.fit()
    beta_hr = res.params[0]
    #
    residuals = x_data - beta_hr * y_data # also known as spread
    #
    zscore_current = ((residuals - residuals.mean()) / residuals.std()).iloc[-1]
    return zscore_current

def get_signs_opposite(x_data, y_data):
    last_2_prices_x = x_data[-2:]
    last_2_prices_y = y_data[-2:]
    #
    time_indices_x = np.arange(len(x_data)-2, len(x_data))
    time_indices_y = np.arange(len(y_data)-2, len(y_data))
    #
    model_x = LinearRegression()
    model_y = LinearRegression()
    model_x.fit(time_indices_x.reshape(-1, 1), last_2_prices_x)
    model_y.fit(time_indices_y.reshape(-1, 1), last_2_prices_y)
    #
    slope_x = model_x.coef_[0]
    slope_y = model_y.coef_[0]
    #
    # round(slope_x, 1) != 0.0 and 
    # round(slope_x, 1) != -0.0 and 
    # round(slope_y, 1) != 0.0 and 
    # round(slope_y, 1) != -0.0: # IF ACTUALLY DIVERGING
    #
    signs_opposite = np.sign(slope_x) == np.sign(-slope_y)
    return signs_opposite

def determine_order_parameters(execution_price):
    if execution_price < 140:
        return {
            'action': 'BUY',
            'quantity': 2,
            'price': execution_price
        }
    else:
        return {
            'action': 'BUY',
            'quantity': 1,
            'price': execution_price
        }

def run_loop(app):
    app.run()




# # Keywords related to cash balance and open positions
# keywords = ["cash balance", "open position", "account", "balance", "position"]
# # Extracting sections where the keywords appear
# sections = {}

# for keyword in keywords:
#     a_index = ctg_ibapi_pd_order_content.find(keyword)
#     if a_index != -1:
#         start_index = max(0, a_index - 500)  # Extracting 500 characters before the keyword
#         end_index = min(len(ctg_ibapi_pd_order_content), a_index + 500)  # Extracting 500 characters after the keyword
#         sections[keyword] = ctg_ibapi_pd_order_content[start_index:end_index]


def main():
    app = IBapi()
    app.connect('127.0.0.1', 7497, 123)

    # Start the run_loop function in a separate thread
    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()

    time.sleep(1)  # Wait for the price data to be updated

    # ticker_groups = [ ['AAPL','SPY'], ["GME","AMC"], ["F","GM"] ]    
    # ticker_groups = [ ['EUR','GBP'], ["AUD","NZD"], ["CAD","JPY"] ]  
    # ticker_groups = [ ['BTC','ETH'], ["BCH","LTC"] ] # all crypto
    # ticker_groups = [ ['BTC','ETH'] ] # all crypto
    ticker_groups = [ ['AAPL','F'] ] 
    contracts_groups = [[create_contract(ticker) for ticker in group] for group in ticker_groups]
    all_tickers = [ticker for group in ticker_groups for ticker in group]
    trail = 10
    rw = RollingWindow(all_tickers, trail)
    
    # windows_single_line = [RollingWindow([ticker], 10) for group in ticker_groups for ticker in group]

    app.events = {}  # Dictionary to store threading events for each ticker

    rw_full = 0
    while True:
        print()
        time.sleep(1)  # Check every n seconds
        for group in contracts_groups:
            for contract in group:
                id_for_orders = req_orderid_manager.get_id()
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
                # app.accountSummary(reqId=order_id, account="DU7518334", ):

                app.events[order_id].wait()  # Wait for the event to be set (i.e., data received)
                price, timestamp = app.data.get(order_id, (None, None))
                # print(f"price {price}")
                # print(f"timestamp {timestamp}") 
                # print(f"@ {datetime.datetime.now()}")
                if price is not None:
                    print(f"{contract.symbol}")
                    # print(f"{price}")
                    # print(f"{timestamp}")
                    rw.update(contract.symbol, price)  
                    # print(f"{rw.get_window(contract.symbol)}")
                    # print()
                req_orderid_manager.increment_id()
                req_id_manager.increment_id()

            
            print(rw_full)
            if rw_full >= trail-1:

                # print("group[0]", group[0].symbol)
                # print("group[1]", group[1].symbol)

                # type(x) <class 'pandas.core.series.Series'>
                # x = pd.Series([11, 12, 14, 12, 15, 16, 18, 17, 18, 17])
                # y = pd.Series([10, 11, 13, 11, 14, 15, 13, 17, 18, 20])
                # # x = pd.Series([11, 12, 14, 12, 15, 16, 18, 17, 18, 17])
                # y = pd.Series([10, 11, 13, 11, 14, 15, 13, 17, 18, 20])
                x = rw.get_window(group[0].symbol)
                y = rw.get_window(group[1].symbol)
                # print(x)

                signs_opposite = get_signs_opposite(x_data=x,y_data=y)
                # print(signs_opposite)
                # app.
                ibkr_order_id = app.nextValidOrderId

            
                # id_for_orders = req_orderid_manager.get_id()
                # ibkr_order_id = app.nextValidId(order_id)
                # print("order_id", order_id)
                # print("id_for_orders", id_for_orders)
                # app.request_contract_details(contract)
                # order_details = create_order("BUY", 1)
                # app.placeOrder(nextValidOrderId, contract, order_details)

                if signs_opposite: # IF ACTUALLY DIVERGING
                    print("IF SIGNS OPPOSITE")

                    # TotalCashValue = app.reqAccountSummary(ibkr_order_id, "All", tags = "TotalCashValue") # "$LEDGER")
                    # TCV = app.reqAccountSummary(ibkr_order_id, "All", tags = "TotalCashValue") # "$LEDGER")
                    # print("\TCV", TCV, "\n")
                    # TCV = app.reqAccountSummary()
                    print("\napp.TotalCashValue", app.TotalCashValue, "\n")

                    zscore_current = get_z_score(x_data=x, y_data=y)
                    app.reqPositions()  # Request current positions

                    zscore_high = 1
                    zscore_low = 0.15
                    long_market = False
                    short_market = False

                    if zscore_current <= -zscore_high and not long_market:
                        long_market = True

                        ibkr_order_id = app.nextValidOrderId
                        determine_order_parameters()
                        order_details = create_order("BUY", 1) # long po 
                        selected_contract = group[0]
                        app.placeOrder(ibkr_order_id, selected_contract, order_details)

                        ibkr_order_id = app.nextValidOrderId
                        determine_order_parameters()
                        order_details = create_order("SELL", 1) # short p1
                        selected_contract = group[1]
                        app.placeOrder(ibkr_order_id, selected_contract, order_details)

                    if abs(zscore_current) <= zscore_low and long_market:
                        long_market = False

                        # ibkr_order_id = app.nextValidOrderId()
                        # determine_order_parameters()
                        # order_details = create_order("SELL", 1) # exit po exit p1
                        # selected_contract = group[0]
                        # app.placeOrder(ibkr_order_id, selected_contract, order_details)
                        exit_position(app,group[0])

                        # ibkr_order_id = app.nextValidOrderId()
                        # determine_order_parameters()
                        # order_details = create_order("BUY", 1) # exit p1
                        # selected_contract = group[1]
                        # app.placeOrder(ibkr_order_id, selected_contract, order_details)
                        exit_position(app,group[1])
                        
                    if zscore_current >= zscore_high and not short_market:
                        short_market = True

                        ibkr_order_id = app.nextValidOrderId
                        determine_order_parameters()
                        order_details = create_order("SELL", 1) # short po 
                        selected_contract = group[0]
                        app.placeOrder(ibkr_order_id, selected_contract, order_details)

                        ibkr_order_id = app.nextValidOrderId
                        determine_order_parameters()
                        order_details = create_order("BUY", 1) # long p1
                        selected_contract = group[1]
                        app.placeOrder(ibkr_order_id, selected_contract, order_details)                        

                    if abs(zscore_current) <= zscore_low and short_market:
                        short_market = False

                        # ibkr_order_id = app.nextValidOrderId()
                        # determine_order_parameters()
                        # order_details = create_order("BUY", 1) # exit po 
                        # selected_contract = group[0]
                        # app.placeOrder(ibkr_order_id, selected_contract, order_details)
                        exit_position(app,group[0])

                        # ibkr_order_id = app.nextValidOrderId()
                        # determine_order_parameters()
                        # order_details = create_order("SELL", 1) # exit p1
                        # selected_contract = group[1]
                        # app.placeOrder(ibkr_order_id, selected_contract, order_details)
                        exit_position(app,group[1])

                # req_orderid_manager.increment_id()
            rw_full += 1
    app.disconnect()

if __name__ == "__main__":
    main()



"""    
long market bool
short market bool

z-score-high
if s l
if e e
z-score-low
if l s 
if e e

order params
    order
        place order



Error: (-1, 2104, 'Market data farm connection is OK:usfarm.nj', '')
Error: (-1, 2104, 'Market data farm connection is OK:usfarm', '')
Error: (-1, 2106, 'HMDS data farm connection is OK:euhmds', '')
Error: (-1, 2106, 'HMDS data farm connection is OK:fundfarm', '')
Error: (-1, 2106, 'HMDS data farm connection is OK:ushmds', '')
Error: (-1, 2158, 'Sec-def data farm connection is OK:secdefil', '')

Error: (1, 504, 'Not connected')
Error 504: Ensure that TWS is running and that you've enabled API connections.
"""

