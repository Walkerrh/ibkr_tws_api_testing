# from ibapi.wrapper import EWrapper
# from ibapi.client import EClient
# from ibapi.utils import iswrapper #just for decorator
# from ibapi.common import *
# import threading
# import time

# class IBapi(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)

#     def accountSummary(self, reqId:int, account:str, tag:str, value:str, currency:str):
#         print(value)
#         # if tag == "BuyingPower": # or whatever you want
#             # print(value)

#     def position(self, account: str, contract, position: float, avgCost: float):
#         """Callback for position details"""
#         print(f"Position: {contract.symbol}, {position} shares, Average Cost: {avgCost}")

#     def positionEnd(self):
#         """Callback indicating end of position data"""
#         print("End of positions")

#     def error(self, *args):
#         print(f"Error: {args}")
#         if args[1] == 504:  # This is the "Not Connected" error code
#             print("Error 504: Ensure that TWS is running and that you've enabled API connections.")


# def main():
#     app = IBapi()
#     app.connect('127.0.0.1', 7497, 0)  # TWS must be running and the IP and port should match its configuration

#     time.sleep(1)
    
#     # Start a thread to keep the app running
#     api_thread = threading.Thread(target=app.run(), daemon=True)
#     api_thread.start()

#     # Request account updates
#     app.reqAccountUpdates(True, "")

#     # Request all open positions
#     app.reqPositions()

#     # Keep the script running for a while to allow callbacks to execute
#     # You can replace this with a more sophisticated approach if needed
#     input("Press Enter to exit...")

#     # app.disconnect()

# if __name__ == "__main__":
#     main()



from ibapi import wrapper
from ibapi.client import EClient
# from ibapi.utils import iswrapper #just for decorator
# from ibapi.common import *
# import math
# import os.path
# from os import path
import time
import threading

class TestApp(wrapper.EWrapper, EClient):
    posns = []
    def __init__(self):
        wrapper.EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.nextValidOrderId = None
        self.positions = {}

    # @iswrapper
    def nextValidId(self, orderId:int):
        print("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId
        # here is where you start using api
        self.reqAccountSummary(self.nextValidOrderId, "All", tags = "TotalCashValue") # "$LEDGER")

    def position(self, account, contract, position, avgCost):
        """   
        contract:
            conId
            symbol
            lastTradeDateOrContractMonth
            strike
            right
            multiplier
            exchange
            primaryExchange
            currency
            localSymbol
            tradingClass
            includeExpired
            secIdType
            secId
            comboLegsDescrip
            comboLegs
            position
            Average Cost  
        position     
        avgCost
        """
        print()
        print(f"conId: {contract.conId},\nsymbol: {contract.symbol},\nlastTradeDateOrContractMonth: {contract.lastTradeDateOrContractMonth},\nstrike: {contract.strike},\nright: {contract.right},\nmultiplier: {contract.multiplier},\nexchange: {contract.exchange},\nprimaryExchange: {contract.primaryExchange},\ncurrency: {contract.currency},\nlocalSymbol: {contract.localSymbol},\ntradingClass: {contract.tradingClass},\nincludeExpired: {contract.includeExpired},\nsecIdType: {contract.secIdType},\nsecId: {contract.secId},\ncomboLegsDescrip: {contract.comboLegsDescrip},\ncomboLegs: {contract.comboLegs},\nposition: {position},\nAverage Cost: {avgCost}")

    # @iswrapper
    def accountSummaryEnd(self, reqId:int):
        
        # now we can disconnect
        self.disconnect()
   
def main():
    app = TestApp()
    app.connect("127.0.0.1", 7497, clientId=123)
    time.sleep(1)

    app.reqPositions()

    # Start a thread to keep the app running
    api_thread = threading.Thread(target=app.run(), daemon=True)
    api_thread.start()

  
if __name__ == "__main__":
    main()
    