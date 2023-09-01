# from ibapi.wrapper import EWrapper
# from ibapi.client import EClient

# class TestApp(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)

#     def error(self, *args):
#         print(f"Error: {args}")

# app = TestApp()
# app.connect('127.0.0.1', 7497, 123)
# app.run()

# """as i remember i think we had this problem before and fixed it with threading, does that ring a bell?"""

# """ Connection is established if terminal shows:
# Error: (-1, 2104, 'Market data farm connection is OK:usfarm.nj', '')
# Error: (-1, 2104, 'Market data farm connection is OK:usfarm', '')
# Error: (-1, 2106, 'HMDS data farm connection is OK:ushmds', '')
# Error: (-1, 2158, 'Sec-def data farm connection is OK:secdefil', '')
# """



from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
import numpy as np
import time

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}
        self.positions = {}

    def error(self, *args):
        print(f"Error: {args}")
        if args[1] == 504:  # This is the "Not Connected" error code
            print("Error 504: Ensure that TWS is running and that you've enabled API connections.")

    def tickPrice(self, reqId, tickType, price, attrib):
        self.data[reqId] = price
        self.cancelMktData(reqId)
        
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

def create_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    return contract

def create_order(action, quantity, price):
    order = Order()
    order.action = action
    order.totalQuantity = quantity
    order.orderType = 'LMT'
    order.lmtPrice = price
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




def main():
    app = IBapi()
    app.connect('127.0.0.1', 7497, 123)
    app.run()

if __name__ == "__main__":
    main()

