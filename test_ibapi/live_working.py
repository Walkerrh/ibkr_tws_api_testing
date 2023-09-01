

# /Users/walkerhutchinson/Jts
# /Users/walkerhutchinson/Jts/twsapi_macunix.1019.01/IBJts/source/pythonclient

import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

class IBapi(EWrapper, EClient):
    def __init__(self):
        self.data = {}
        EClient.__init__(self, self)

    def tickPrice(self, reqId, tickType, price, attrib):
        # Check if the tickType corresponds to the last traded price (usually tickType 4)
        if tickType == 4:
            self.data[reqId] = price
            print(f"\nPrice: {price}")
            self.cancelMktData(reqId)  # Cancel the market data subscription after getting the price

    def error(self, *args):
        print('Error:', args)

def run_loop():
    app.run()

app = IBapi()
app.connect('127.0.0.1', 7497, 123)  # 7497 is the typical port for paper trading, 123 is a random clientId

# Define the AAPL stock (contract)
contract = Contract()
contract.symbol = "SPY"
contract.secType = 'STK'
contract.currency = 'USD'
contract.exchange = 'SMART'

""" CRYPTO
contract.symbol = "ETH"
contract.secType = "CRYPTO"
contract.currency = "USD"
contract.exchange = "PAXOS"
"""

""" STOCK
# contract.symbol = 'SPY'
# contract.secType = 'STK'
# contract.currency = 'USD'
# contract.exchange = 'SMART'
"""

""" FOREX
contract.symbol = "EUR"
contract.secType = "CASH"
contract.currency = "USD"
contract.exchange = "IDEALPRO"
"""

# Start the socket in a thread
import threading
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Give some time for connection to establish
time.sleep(1)

newID = 0 
while True:
    app.reqMktData(newID, contract, '', False, False, [])  # Request ID 1 for AAPL
    time.sleep(5)  # Adjust the frequency as needed
    newID += 1

# To stop it, you'd typically call app.disconnect(). But since this script keeps running, I've omitted that.
