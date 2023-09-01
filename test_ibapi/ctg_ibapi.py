
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import datetime as dt
import threading
from queue import Queue

class IBKRDataRetriever(EWrapper, EClient):
    def __init__(self, symbols, order_queue, event_queue):
        EWrapper.__init__(self)
        EClient.__init__(self, self)

        self.symbols = symbols
        self.latest_prices = {symbol: None for symbol in symbols}
        self.order_queue = order_queue
        self.event_queue = event_queue

        self.connect('127.0.0.1', 7497, 123)  # clientId=123

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:  # Last traded price
            symbol = self.symbols[reqId]
            self.latest_prices[symbol] = price
            self.event_queue.put({"type": "MarketEvent", "symbol": symbol, "price": price, "timestamp": dt.datetime.now()})

    def order_processor(self):
        while True:
            order = self.order_queue.get()
            if order is None:
                break
            
            # Extract order details and send to IBKR for execution.
            # Once executed, push a FillEvent to the main system's event queue.

    def run(self):
        order_thread = threading.Thread(target=self.order_processor)
        order_thread.start()

        # Request data for symbols
        for symbol in self.symbols:
            contract = Contract()
            contract.symbol = symbol
            contract.secType = 'STK'
            contract.exchange = 'SMART'
            contract.currency = 'USD'
            self.reqMktData(symbol, contract, '', False, False, [])

        order_thread.join()

if __name__ == "__main__":
    symbols = ["AAPL", "MSFT"]  # Add your symbols here
    order_queue = Queue()
    event_queue = Queue()

    retriever = IBKRDataRetriever(symbols, order_queue, event_queue)
    retriever.run()
