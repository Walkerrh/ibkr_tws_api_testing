from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.next_order_id = None
        self.nextValidOrderId = None

    def nextValidId(self, orderId: int):
        """ Callback that receives the next valid order ID """
        super().nextValidId(orderId)
        # logging.debug("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId
        self.next_order_id = orderId
        print("nextValidOrderId:", self.nextValidOrderId)
        print("NextValidId:", orderId)
        self.start_trading()

    def start_trading(self):
        # Define the Bitcoin contract
        bitcoin_contract = Contract()
        bitcoin_contract.symbol = "AAPL"
        bitcoin_contract.secType = "STK"
        bitcoin_contract.exchange = "SMART"  # Adjust this based on your preference
        # bitcoin_contract.PrimaryExch = 
        bitcoin_contract.currency = "USD"
        
        
        # Define the order (MKT order to buy 1 Bitcoin)
        order = Order()
        order.action = "BUY"
        order.totalQuantity = 1
        order.orderType = "MKT"
        # order.cashQty = 100000 # for crypto
        order.tif = "DAY"

        # Place the order
        self.placeOrder(self.next_order_id, bitcoin_contract, order)
        
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"Order ID: {orderId}, Status: {status}, Filled: {filled}, Remaining: {remaining}, Last Fill Price: {lastFillPrice}")

    def error(self, *args):
        print(f"Error: {args}")
        if args[1] == 504:  # This is the "Not Connected" error code
            print("Error 504: Ensure that TWS is running and that you've enabled API connections.")


# Start the app
app = IBapi()
app.connect('127.0.0.1', 7497, 0)  # TWS must be running and the IP and port should match its configuration
time.sleep(1)

# Start a thread to keep the app running
api_thread = threading.Thread(target=app.run(), daemon=True)
api_thread.start()

# Request the next valid order ID (this will initiate the trading once received)
app.reqIds(-1)


