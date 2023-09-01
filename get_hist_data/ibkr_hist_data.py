


import csv
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []  # Store the historical data

    def historicalData(self, reqId, bar):
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])

    def historicalDataEnd(self, reqId, start, end):
        # When data ends, write to CSV
        with open('/Users/walkerhutchinson/Desktop/ThunderFund/meteor_code/F_2014_15min.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Open", "High", "Low", "Close", "Volume"])  # Header
            for row in self.data:
                writer.writerow(row)
        print("Data saved to historical_data.csv")
        self.disconnect()

def run_loop():
    app.run()

app = IBapi()
app.connect('127.0.0.1', 7497, 123)

# Define the contract
contract = Contract()
contract.symbol = 'F'
contract.secType = 'STK'
contract.exchange = 'SMART'
contract.currency = 'USD'

# Start the socket in a thread
import threading
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Give time for the connection to establish
time.sleep(1)

# Request historical data
end_date = "20141231 23:59:59 US/Eastern"
app.reqHistoricalData(1, contract, end_date, '1 Y', '15 mins', 'TRADES', 1, 1, False, [])

# The script will automatically save the data to "historical_data.csv" when it's done retrieving.

