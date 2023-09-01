 

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order

import threading
import numpy as np
import time as TIME
import datetime as dt

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
            self.data[reqId] = price
            self.time[reqId] = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # print("tickPrice reqId", reqId)
            self.cancelMktData(reqId)  # Cancel the market data subscription after getting the price

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
        self.windows = {ticker: np.full(n, np.nan) for ticker in tickers}

    def update(self, ticker, price):
        if ticker in self.windows:
            self.windows[ticker] = np.roll(self.windows[ticker], shift=-1)
            self.windows[ticker][-1] = price

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
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
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

def run_loop(app):
    app.run()

def main():
    app = IBapi()
    app.connect('127.0.0.1', 7497, 123)

    # Start the run_loop function in a separate thread
    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()
    TIME.sleep(1)  # Wait for the price data to be updated

    app.reqPositions()  # Request current positions

    tickers = ['AAPL', 'SPY']
    contracts = [create_contract(ticker) for ticker in tickers]

    for c in contracts:
        ticker_id_manager.set_id(c.symbol)  # Use OrderIDManager to get the order_id

    rw = RollingWindow(tickers, 10)  # Example window size of 10

    while True:
        print()
        TIME.sleep(5)  # Check every num of seconds
        for contract in contracts:

            SYMBOL = contract.symbol
            ID = req_id_manager.get_id()
            IDreq = ticker_id_manager.get_id(SYMBOL)

            app.reqMktData(
                            reqId=IDreq, 
                            contract=contract, 
                            genericTickList='', 
                            snapshot=False, 
                            regulatorySnapshot=False,
                            mktDataOptions=[]
            )
            price = app.data.get(IDreq)
            time = app.time.get(IDreq)
            print("price", price, "time", time, "@", dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            if price is not None:
                print(f"Current Price of {SYMBOL}: {price} @ {time}")
                rw.update(SYMBOL, price)  # Update the rolling window

                # Just for demonstration, print the rolling window
                print(f"Rolling Window for {SYMBOL}: {rw.get_window(SYMBOL)}")

                # # Add your logic for order placement, etc. here
                # ...

            req_id_manager.increment_id()


if __name__ == "__main__":
    main()



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























# from ibapi.client import *
# from ibapi.wrapper import *

# class TestApp(EClient, EWrapper):
#     def __init__(self):
#         EClient.__init__(self, self)

#     def nextValidId(self, orderId: int):

#         mycontract = Contract()
#         mycontract.symbol = "F"
#         mycontract.secType = "STK"
#         mycontract.exchange = "SMART"
#         mycontract.currency = "USD"

#         self.reqContractDetails(orderId, mycontract)

#     def contractDetails(self, reqId: int, contractDetails: ContractDetails):
#         print(contractDetails.contract)

#         myorder = Order()
#         myorder.orderId = reqId 
#         myorder.action = "BUY"
#         myorder.orderType = "MKT"
#         myorder.totalQuantity = 10

#         self.placeOrder(reqId, contractDetails.contract, myorder)

#     def openOrder(self, orderId:OrderId, contract:Contract, order:Order, orderState:OrderState):
#         print(f"orderId: {orderId}, contract: {contract}, order:{order}")
    
#     def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
#         if status == "Filled":
#             print(f"Order {orderId}, status {filled}, at {avgFillPrice}!")

#     def execDetails(self, reqId, contract, execution):
#         print(f"Order executed: {execution}")
#         # {execution.execId} {execution.time} {execution.acctNumber} {execution.side} {execution.shares} {contract.symbol} at {execution.price}")


# app = TestApp()
# app.connect("127.0.0.1", 7497, 123)
# app.run()


# """ Market Order
# myorder = Order()
# myorder.orderId = reqId 
# myorder.action = "BUY"
# myorder.orderType = "MKT"
# myorder.totalQuantity = 10
# """

# """ Limit Order
# myorder = Order()
# myorder.orderId = reqId 
# myorder.action = "BUY"
# myorder.tif = "GTC" # DAY by default
# myorder.orderType = "MKT"
# myorder.lmtPrice = 144.80
# myorder.totalQuantity = 10
# """


# from ibapi.wrapper import EWrapper
# from ibapi.client import EClient
# from ibapi.contract import Contract
# from ibapi.order import Order
# import time

# class IBapi(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)
#         self.data = {}

#     def error(self, reqId, errorCode, errorString):
#         print(f"Error: {reqId} {errorCode} {errorString}")

#     def tickPrice(self, reqId, tickType, price, attrib):
#         self.data[reqId] = price

# def create_contract(symbol):
#     contract = Contract()
#     contract.symbol = symbol
#     contract.secType = 'STK'
#     contract.exchange = 'SMART'
#     contract.currency = 'USD'
#     return contract

# def create_order(action, quantity, price):
#     order = Order()
#     order.action = action
#     order.totalQuantity = quantity
#     order.orderType = 'LMT'
#     order.lmtPrice = price
#     return order

# def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
#     if status == "Filled":
#         print(f"Order {orderId}, status {filled}, at {avgFillPrice}!")

# def position(self, account, contract, position, avgCost):
#     self.positions[contract.symbol] = {
#         'position': position,
#         'avgCost': avgCost
#     }

# def exit_position(app, contract):
#     symbol = contract.symbol
#     if symbol in app.positions:
#         quantity = app.positions[symbol]['position']
#         if quantity > 0:  # Long position, so we sell
#             return create_order('SELL', abs(quantity), None)  # Market order to sell all shares
#         elif quantity < 0:  # Short position, so we buy to cover
#             return create_order('BUY', abs(quantity), None)  # Market order to buy to cover
#     return None

# def main():
#     app = IBapi()
#     app.connect('127.0.0.1', 7497, 123)

#     contract = create_contract('AAPL')
#     order_id = 1

#     while True:
#         app.reqMktData(order_id, contract, '', False, False, [])
#         price = app.data.get(order_id)
#         time.sleep(1)  # wait for the price data to be updated
        
#         price = app.data.get(order_id)
        
#         if price is not None:
#             print(f"Current Price: {price}")

#             # Example condition: buy if the price drops below $140
#             if price < 140:
#                 order = create_order('BUY', 1, price)  # Buy 1 share
#                 app.placeOrder(order_id + 1, contract, order)
#                 print(f"Order placed to buy at: {price}")
#             else:
#                 # Assuming some condition is met to exit the position
#                 order = exit_position(app, contract)
#                 if order:
#                     app.placeOrder(order_id + 1, contract, order)
#                     print(f"Order placed to exit position for {contract.symbol}")

#         time.sleep(60)  # Check every minute

#     app.disconnect()

# if __name__ == "__main__":
#     main()
























# from ibapi.wrapper import EWrapper
# from ibapi.client import EClient
# from ibapi.contract import Contract
# from ibapi.order import Order
# import time

# class IBapi(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)
#         self.data = {}
#         self.positions = {}

#     def error(self, reqId, errorCode, errorString):
#         print(f"Error: {reqId} {errorCode} {errorString}")

#     def tickPrice(self, reqId, tickType, price, attrib):
#         self.data[reqId] += price

#     def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
#                     permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
#         if status == "Filled":
#             print(f"Order {orderId} has been filled at {avgFillPrice}!")

#     def execDetails(self, reqId, contract, execution):
#         print(f"Order executed: {execution.side} {execution.shares} {contract.symbol} at {execution.price}")

# def create_contracts(tickers):
#     contracts = []
#     for ticker in tickers:
#         contract = Contract()
#         contract.symbol = ticker
#         contract.secType = 'STK'
#         contract.exchange = 'SMART'
#         contract.currency = 'USD'
#         contracts.append(contract)
#     return contracts

# def create_order(action, quantity, price):
#     order = Order()
#     order.action = action
#     order.totalQuantity = quantity
#     order.orderType = 'LMT'
#     order.lmtPrice = price
#     return order

# def determine_order_parameters(execution_price):
#     if execution_price < 140:
#         return {
#             'action': 'BUY',
#             'quantity': 2,
#             'price': execution_price
#         }
#     else:
#         return {
#             'action': 'BUY',
#             'quantity': 1,
#             'price': execution_price
#         }

# def position(self, account, contract, position, avgCost):
#     key = (contract.symbol, contract.secType, contract.currency, contract.exchange)
#     self.positions[key] = {
#         'position': position,
#         'avgCost': avgCost
#     }

# def exit_position(app, contract):
#     key = (contract.symbol, contract.secType, contract.currency, contract.exchange)
#     if key in app.positions:
#         quantity = app.positions[key]['position']
#         if quantity > 0:  # Long position, so we sell
#             return create_order('SELL', abs(quantity), None)  # Market order to sell all shares
#         elif quantity < 0:  # Short position, so we buy to cover
#             return create_order('BUY', abs(quantity), None)  # Market order to buy to cover
#     return None


# def main():
#     app = IBapi()
#     app.connect('127.0.0.1', 7497, 123)

#     app.reqPositions()  # Request current positions

#     tickers = ['AAPL', 'GOOGL']  # Example tickers; add/remove as needed
#     contracts = create_contracts(tickers)

#     while True:
#         for contract in contracts:
#             app.reqMktData(order_id, contract, '', False, False, [])
#             time.sleep(1)  # wait for the price data to be updated
            
#             price = app.data.get(order_id)
            
#             if price is not None:
#                 print(f"Current Price of {contract.symbol}: {price}")

#                 order_params = determine_order_parameters(price)
#                 order = create_order(order_params['action'], order_params['quantity'], order_params['price'])
#                 app.placeOrder(order_id + 1, contract, order)
#                 print(f"Order placed to {order_params['action']} {order_params['quantity']} shares at: {price}")
#             else:
#                 # Assuming some condition is met to exit the position
#                 order = exit_position(app, contract)
#                 if order:
#                     app.placeOrder(order_id + 1, contract, order)
#                     print(f"Order placed to exit position for {contract.symbol}")

#         time.sleep(60)  # Check every minute

#     app.disconnect()

# if __name__ == "__main__":
#     main()






















