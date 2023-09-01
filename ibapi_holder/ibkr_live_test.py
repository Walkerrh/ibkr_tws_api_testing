
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def tickPrice(self, reqId, tickType, price, attrib):
        # Check if the tickType corresponds to the last traded price (usually tickType 4)
        if tickType == 4:
            if reqId == 1:
                print()
                print(f"F Price: {price}")
            self.cancelMktData(reqId)  # Cancel the market data subscription after getting the price

    def error(self, *args):
        print('Error:', args)

def run_loop():
    app.run()

app = IBapi()
app.connect('127.0.0.1', 7497, 123)  # 7497 is the typical port for paper trading, 123 is a random clientId

# Define the AAPL stock (contract)
contract_aapl = Contract()
contract_aapl.symbol = 'SPY'
contract_aapl.secType = 'STK'
contract_aapl.exchange = 'SMART'
contract_aapl.currency = 'USD'

# Start the socket in a thread
import threading
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Give some time for connection to establish
time.sleep(1)

while True:
    app.reqMktData(1, contract_aapl, '', False, False, [])  # Request ID 1 for AAPL
    time.sleep(1)  # Adjust the frequency as needed

# To stop it, you'd typically call app.disconnect(). But since this script keeps running, I've omitted that.
