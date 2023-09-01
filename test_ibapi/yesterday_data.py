from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import datetime
import time

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []

    def historicalData(self, reqId, bar):
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])

    def historicalDataEnd(self, reqId, start, end):
        print('Historical data received')
        app.disconnect()

def get_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    return contract

def get_historical_data(app, contract, duration, bar_size):
    # End time is the end of previous day
    end_time = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=16, minute=15, second=0).strftime('%Y%m%d %H:%M:%S US/Eastern')

    # Request historical candles
    app.reqHistoricalData(reqId=1, 
                          contract=contract,
                          endDateTime='',
                          durationStr=duration,
                          barSizeSetting=bar_size,
                          whatToShow='TRADES',
                          useRTH=1,
                          formatDate=1,
                          keepUpToDate=False,
                          chartOptions=[])

app = IBapi()
app.connect('127.0.0.1', 7497, 123)

# Give some time for connection to establish
time.sleep(1)

# Get historical data for, e.g., Apple
contract = get_contract('AAPL')
get_historical_data(app, contract, '1 D', '15 mins')

# Run the app
app.run()

# Print data
for bar in app.data:
    print(bar)

""" will return
Timestamp: The start time of the bar.
Open: The opening price at the start of the bar (at the given timestamp).
High: The highest traded price during the bar's time period.
Low: The lowest traded price during the bar's time period.
Close: The closing price at the end of the bar.
"""