from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import time

class ForexData(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, *args):
        print(f"Error: {args}")
        if args[1] == 504:  # This is the "Not Connected" error code
            print("Error 504: Ensure that TWS is running and that you've enabled API connections.")

    def tickPrice(self, reqId, tickType, price, attribs):
        print(f"Price for request {reqId}: {price}")

def main():
    app = ForexData()
    app.connect("127.0.0.1", 7497, clientId=0)  # 7497 is the default port for TWS paper trading
    app.run()
    time.sleep(1)  # Let the data come in for a few seconds


    # Define the forex contract
    contract = Contract()
    contract.symbol = "EUR"
    contract.secType = "CASH"
    contract.exchange = "IDEALPRO"
    contract.currency = "GBP"

    # Request market data
    app.reqMarketDataType(4)  # 4 is for delayed data. Use 1 for real-time data.
    app.reqMktData(1, contract, "", False, False, [])  # 1 is a unique request ID

    time.sleep(5)  # Let the data come in for a few seconds
    app.disconnect()

if __name__ == "__main__":
    main()
