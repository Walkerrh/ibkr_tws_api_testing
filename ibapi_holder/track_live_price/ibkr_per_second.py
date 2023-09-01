



from ibapi.contract import Contract
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
import datetime as dt
import threading
import time
import csv

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.csv_writer = None

    def tickPrice(self, reqId, tickType, price, attrib):
        # Check if the tickType corresponds to the last traded price (usually tickType 4)
        print("tickPrice method called")
        if tickType == 4:
            if reqId == 1:
                print()
                print(f"F Price: {price}")
                current_time_with_microseconds = dt.datetime.now().time()
                current_time = dt.time(current_time_with_microseconds.hour, current_time_with_microseconds.minute, current_time_with_microseconds.second)
                start_time = dt.time(9, 30)  # 9:00 AM
                end_time = dt.time(16, 0)  # 5:00 PM 
                # print(start_time, "<=", current_time, "<=", end_time)
                if start_time <= current_time <= end_time:
                    print("made it")
                    data = ["F", price, current_time, "EST", "Interactive Brokers", "SMART"]
                    self.write_to_csv(data)
            self.cancelMktData(reqId)

    def start_csv_writer(self):
        # Open the CSV file in write mode
        self.csv_file = open('/Users/walkerhutchinson/Desktop/ThunderFund/meteor_code/track_live_price/stock_data.csv', 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        # Write the header
        self.csv_writer.writerow(['Symbol', 'Price', 'Time', 'TimeZone', 'Brokerage', 'Exchange'])

    def write_to_csv(self, data):
        print("Writing data to CSV:", data)
        self.csv_writer.writerow(data)
        self.csv_file.flush()  # Explicitly flush the buffer

    def stop_csv_writer(self):
        self.csv_file.close()

    def error(self, *args):
        print('Error:', args)

def run_loop():
    app.run()

app = IBapi()
app.connect('127.0.0.1', 7497, 123)  # 7497 is the typical port for paper trading, 123 is a random clientId
app.start_csv_writer()

# Define the AAPL stock (contract)
contract = Contract()
contract.symbol = 'F'
contract.secType = 'STK'
contract.exchange = 'SMART'
contract.currency = 'USD'

# Start the socket in a thread
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Give some time for connection to establish
time.sleep(1)

try:
    while True:
        app.reqMktData(1, contract, '', False, False, [])
        time.sleep(1)
except KeyboardInterrupt:
    print("Gracefully shutting down...")
    app.stop_csv_writer()
    app.disconnect()




















# import time
# import csv
# from ibapi.client import EClient
# from ibapi.wrapper import EWrapper
# from ibapi.contract import Contract

# class IBapi(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)
#         self.csv_writer = None

#     def tickPrice(self, reqId, tickType, price, attrib):
#         # Check if the tickType corresponds to the last traded price (usually tickType 4)
#         if tickType == 4:
#             symbol = 'AAPL' if reqId == 1 else 'MSFT'  # Adjust as per your setup
#             current_time = time.strftime('%Y-%m-%d %H:%M:%S')
#             data = [symbol, price, current_time, "EST", "Interactive Brokers", "SMART"]
#             self.write_to_csv(data)
#             self.cancelMktData(reqId)

#     def start_csv_writer(self):
#         # Open the CSV file in write mode
#         self.csv_file = open('/Users/walkerhutchinson/Desktop/ThunderFund/meteor_code/track_live_price/stock_data.csv', 'w', newline='')
#         self.csv_writer = csv.writer(self.csv_file)
#         # Write the header
#         self.csv_writer.writerow(['Symbol', 'Price', 'Time', 'TimeZone', 'Brokerage', 'Exchange'])

#     def write_to_csv(self, data):
#         self.csv_writer.writerow(data)

#     def stop_csv_writer(self):
#         self.csv_file.close()

#     def error(self, *args):
#         print('Error:', args)

# def run_loop():
#     app.run()

# app = IBapi()
# app.connect('127.0.0.1', 7497, 123)  # 7497 is the typical port for paper trading, 123 is a random clientId
# app.start_csv_writer()

# # Define the AAPL stock (contract)
# contract_aapl = Contract()
# contract_aapl.symbol = 'AAPL'
# contract_aapl.secType = 'STK'
# contract_aapl.exchange = 'SMART'
# contract_aapl.currency = 'USD'

# # Define the MSFT stock (contract)
# contract_msft = Contract()
# contract_msft.symbol = 'MSFT'
# contract_msft.secType = 'STK'
# contract_msft.exchange = 'SMART'
# contract_msft.currency = 'USD'

# # Start the socket in a thread
# import threading
# api_thread = threading.Thread(target=run_loop, daemon=True)
# api_thread.start()

# # Give some time for connection to establish
# time.sleep(1)

# try:
#     while True:
#         app.reqMktData(1, contract_aapl, '', False, False, [])
#         app.reqMktData(2, contract_msft, '', False, False, [])
#         time.sleep(1)  # Capture data every second
# except KeyboardInterrupt:
#     app.stop_csv_writer()
#     app.disconnect()
