
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.order import Order

import threading
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
        self.data[reqId] += price

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        if status == "Filled":
            print(f"Order {orderId} has been filled at {avgFillPrice}!")

    def execDetails(self, reqId, contract, execution):
        print(f"Order executed: {execution.side} {execution.shares} {contract.symbol} at {execution.price}")

def create_contracts(tickers):
    contracts = []
    for ticker in tickers:
        contract = Contract()
        contract.symbol = ticker
        contract.secType = 'CRYPTO'
        contract.exchange = 'PAXOS'
        contract.currency = 'USD'
        contracts.append(contract)
    return contracts

def create_order(action, quantity, price):
    order = Order()
    order.action = action
    order.totalQuantity = quantity
    order.orderType = 'MKT'
    # order.lmtPrice = price
    return order

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

def position(self, account, contract, position, avgCost):
    key = (contract.symbol, contract.secType, contract.currency, contract.exchange)
    self.positions[key] = {
        'position': position,
        'avgCost': avgCost
    }

def exit_position(app, contract):
    key = (contract.symbol, contract.secType, contract.currency, contract.exchange)
    if key in app.positions:
        quantity = app.positions[key]['position']
        if quantity > 0:  # Long position, so we sell
            return create_order('SELL', abs(quantity), None)  # Market order to sell all shares
        elif quantity < 0:  # Short position, so we buy to cover
            return create_order('BUY', abs(quantity), None)  # Market order to buy to cover
    return None

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

def main():
    app = IBapi()
    app.connect('127.0.0.1', 7497, 123)
    time.sleep(1)  # wait for the price data to be updated

    app.reqPositions()  # Request current positions

    tickers = ['BTC', 'ETH']  # Example tickers; add/remove as needed
    contracts = create_contracts(tickers)

    app.events = {}  # Dictionary to store threading events for each ticker

    while True:
        for contract in contracts:
            order_id = req_id_manager.get_id()
            app.events[order_id] = threading.Event()  # Create an event for this ticker
            app.reqMktData(order_id, contract, '', False, False, [])

            app.events[order_id].wait()  # Wait for the event to be set (i.e., data received)
            
            price = app.data.get(order_id)
            print(price)
            
            if price is not None:
                print(f"Current Price of {contract.symbol}: {price}")

                order_params = determine_order_parameters(price)
                order = create_order(order_params['action'], order_params['quantity'], order_params['price'])
                app.placeOrder(order_id + 1, contract, order)
                print(f"Order placed to {order_params['action']} {order_params['quantity']} shares at: {price}")
            else:
                # Assuming some condition is met to exit the position
                order = exit_position(app, contract)
                if order:
                    app.placeOrder(order_id + 1, contract, order)
                    print(f"Order placed to exit position for {contract.symbol}")

            req_id_manager.increment_id()
        time.sleep(5)  # Check every minute
    app.disconnect()

if __name__ == "__main__":
    main()

