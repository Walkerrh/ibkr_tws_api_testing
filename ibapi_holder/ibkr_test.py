

# """  
# https://stackoverflow.com/questions/48470613/adding-the-ibapi-library-to-pythonpath-module-in-spyder-python-3-6

# A new API generic tick for realtime news is available via generic tick 292
# """
 


# # from ibapi.client import *
# # from ibapi.wrapper import *
# # import time 


# # class TestApp(EClient, EWrapper):
# #     def __init__(self):
# #         EClient.__init__(self, self)
# #         self.request_timer = None

# #         # Define mycontract as an instance variable
# #         self.mycontract = Contract()
# #         self.mycontract.symbol = "AAPL"
# #         self.mycontract.secType = "STK"
# #         self.mycontract.exchange = "SMART"
# #         self.mycontract.currency = "USD"

# #     def start_timer(self):
# #         self.request_timer = self.reqMktData(1001, self.mycontract, "", 0, 0, []) 
# #         self._timer = threading.Timer(5, self.request_data)  # Set a timer for 5 minutes
# #         self._timer.start()

# #     def request_data(self):
# #         self.reqMarketDataType(4)
# #         self.reqMktData(1001, self.mycontract, "", 0, 0, [])  # Using the instance variable here
# #         self.start_timer()  # Restart the timer after making the request

# # if __name__ == "__main__":
    
# #     app = TestApp()
# #     app.connect("127.0.0.1", 7497, 1000)
# #     app.run()  # Keep the event loop running















# # # /Users/walkerhutchinson/Jts/twsapi_macunix.1019.01/IBJts/source/pythonclient/tests/ibkr_test.py

# import time
# from ibapi.client import EClient
# from ibapi.wrapper import EWrapper
# from ibapi.contract import Contract

# class IBapi(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)

#     def tickPrice(self, reqId, tickType, price, attrib):
#         # Check if the tickType corresponds to the last traded price (usually tickType 4)
#         if tickType == 4:
#             if reqId == 1:
#                 print()
#                 print(f"F Price: {price}")
#             elif reqId == 2:
#                 print(f"GM Price: {price}")
#             self.cancelMktData(reqId)  # Cancel the market data subscription after getting the price

#     def error(self, *args):
#         print('Error:', args)

# def run_loop():
#     app.run()

# app = IBapi()
# app.connect('127.0.0.1', 7497, 123)  # 7497 is the typical port for paper trading, 123 is a random clientId

# # Define the AAPL stock (contract)
# contract_aapl = Contract()
# contract_aapl.symbol = 'F'
# contract_aapl.secType = 'STK'
# contract_aapl.exchange = 'SMART'
# contract_aapl.currency = 'USD'

# # Define the MSFT stock (contract)
# contract_msft = Contract()
# contract_msft.symbol = 'GM'
# contract_msft.secType = 'STK'
# contract_msft.exchange = 'SMART'
# contract_msft.currency = 'USD'

# # Start the socket in a thread
# import threading
# api_thread = threading.Thread(target=run_loop, daemon=True)
# api_thread.start()

# # Give some time for connection to establish
# time.sleep(1)

# while True:
#     app.reqMktData(1, contract_aapl, '', False, False, [])  # Request ID 1 for AAPL
#     app.reqMktData(2, contract_msft, '', False, False, [])  # Request ID 2 for MSFT
#     time.sleep(1)  # Adjust the frequency as needed

# # To stop it, you'd typically call app.disconnect(). But since this script keeps running, I've omitted that.


















import time
# ibapi imports
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.execution import ExecutionFilter
from ibapi.order import Order

import datetime as dt

d = dt.datetime.now()
formatted_string = d.strftime("%Y-%m-%d %H:%M:%S")

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def tickPrice(self, reqId, tickType, price, attrib):
        print("tickType", tickType)
        # Check if the tickType corresponds to the last traded price (usually tickType 4)
        if tickType == 4:
            if reqId == 1:
                print()
                print(f"F Price: {price}, Time: {formatted_string}")
                print("attrib", attrib)
            elif reqId == 2:
                print(f"GM Price: {price}, Time: {formatted_string}")
            self.cancelMktData(reqId)  # Cancel the market data subscription after getting the price
    
    def updateAccountValue(self, key, val, currency, accountName):
        print(f"AccountUpdate: Key: {key}, Value: {val}, Currency: {currency}, AccountName: {accountName}")

    def accountSummary(self, reqId, account, tag, value, currency):
        print(f"AccountSummary. ReqId: {reqId}, Account: {account}, Tag: {tag}, Value: {value}, Currency: {currency}")

    def position(self, account, contract, position, avgCost):
        print(f"Position. Account: {account}, Symbol: {contract.symbol}, SecType: {contract.secType}, Currency: {contract.currency}, Position: {position}, Avg cost: {avgCost}")

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"OrderStatus. OrderId: {orderId}, Status: {status}, Filled: {filled}, Remaining: {remaining}, AvgFillPrice: {avgFillPrice}, PermId: {permId}, ParentId: {parentId}, LastFillPrice: {lastFillPrice}, ClientId: {clientId}, WhyHeld: {whyHeld}, MktCapPrice: {mktCapPrice}")

    def contractDetails(self, reqId, contractDetails):
        print(f"ContractDetails. ReqId: {reqId}, Contract: {contractDetails.timeZoneId}")

    def execDetails(self, reqId, contract, execution):
        # print(execution)
        print(f"ExecutionDetails. ReqId: {reqId}, Symbol: {contract.symbol}, SecType: {contract.secType}, Currency: {contract.currency}, Execution: {execution.execId}, Price: {execution.price}, Shares: {execution.shares}")

    def error(self, *args):
        print('Error:', args)

def run_loop():
    app.run()

app = IBapi()
app.connect('127.0.0.1', 7497, 123)  # 7497 is the typical port for paper trading, 123 is a random clientId

# Define the AAPL stock (contract)
contract_top = Contract()
contract_top.symbol = 'F'
contract_top.secType = 'STK'
contract_top.exchange = 'SMART'
contract_top.currency = 'USD'

# Define the MSFT stock (contract)
contract_bottom = Contract()
contract_bottom.symbol = 'GM'
contract_bottom.secType = 'STK'
contract_bottom.exchange = 'SMART'
contract_bottom.currency = 'USD'

# Define an order
order = Order()
order.action = 'BUY'
order.totalQuantity = 1
order.tif = 'GTC'  # For a Good-Til-Canceled order
order.orderType = 'MKT'
order.lmtPrice = 1000  # Set a limit price
order.outsideRth = True  # This is the crucial line to enable after-hours trading

# order.action = 'BUY'
# order.totalQuantity = 100
# order.orderType = 'LMT'
# order.lmtPrice = 150
# order.auxPrice = 148
# order.tif = 'GTC'
# order.ocaGroup = 'MyOCAGroup'
# order.ocaType = 1
# order.outsideRth = True
# order.hidden = False
# order.goodAfterTime = '20230825 12:45:00'
# order.goodTillDate = '20230830 12:45:00'
# order.orderRef = 'MyOrderRef123'
# order.trailStopPrice = 147
# order.trailingPercent = 0.02
# order.faGroup = 'MyFAGroup'
# order.faProfile = 'MyFAProfile'
# order.faMethod = 'NetLiq'
# order.faPercentage = '0.75'
# order.openClose = 'O'
# order.origin = 0
# order.transmit = True
# order.parentId = 0
# order.blockOrder = True
# order.sweepToFill = True
# order.displaySize = 10
# order.triggerMethod = 0
# order.percentOffset = 0.05
# order.minQty = 1
# order.nbboPriceCap = 151
# order.volatility = 0.5
# order.volatilityType = 1
# order.continuousUpdate = 1
# order.referencePriceType = 1
# order.deltaNeutralOrderType = 'LMT'
# order.deltaNeutralAuxPrice = 150
# order.deltaNeutralConId = 0
# order.hedgeType = 'D'
# order.hedgeParam = '0.5'

# Start the socket in a thread
import threading
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Give some time for connection to establish
time.sleep(1)

while True:

    if not app.isConnected():
        print("Attempting to reconnect...")
        app.connect('127.0.0.1', 7497, 123)
        time.sleep(2)  # give it some time to reconnect

    else:
        app.reqMktData(1, contract_top, '', False, False, [])  # Request ID 1 for AAPL
        app.reqMktData(2, contract_bottom, '', False, False, [])  # Request ID 2 for MSFT

        # # Request account updates
        # app.reqAccountUpdates(True, '')

        # # Request account summary
        # app.reqAccountSummary(1, 'All', 'NetLiquidation,TotalCashValue')  # Example tags

        # # Request current positions
        # app.reqPositions()

        # # Here you can place the order if you wish
        # unique_order_id = 101
        # app.placeOrder(unique_order_id, contract_top, order)

        # # Request contract details (Example for AAPL contract)
        app.reqContractDetails(2, contract_top)
        app.reqContractDetails(3, contract_bottom)

        # Request executions (You may need to define a filter)
        # app.reqExecutions(2, ExecutionFilter())
        # app.reqExecutions(3, ExecutionFilter())

        time.sleep(20)  # Adjust the frequency as needed

# To stop it, you'd typically call app.disconnect(). But since this script keeps running, I've omitted that.
