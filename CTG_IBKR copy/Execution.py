

from abc import ABCMeta, abstractmethod

from Events import FillEvent, OrderEvent
from datetime import datetime


from ibapi.contract import Contract
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.order import Order

class ExecutionHandler(object):
    """
    Execution handler class to handle Order and Fill events
    for different types of APIs (brokers, exchanges), or protocols such as FIX
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        """
        Takes an Order event and executes it, producing
        a Fill event that gets placed onto the Events queue.

        Parameters:
        event - Contains an Event object with order information.
        """
        raise NotImplementedError("Should implement execute_order()")


class SimpleSimulatedExecutionHandler(ExecutionHandler):
    """
    Simple handler with no latency or slippage modelling
    """

    def __init__(self, events):
        """
        Initialises the handler, setting the event queues
        up internally.

        Parameters:
        events - The Queue of Event objects.
        """
        self.events = events

    def execute_order(self, event):
        """
        Order event converted to Fill event to
        execute the order on "live" broker. The event is
        then added to the queue

        Parameters:
        event - Contains an Event object with order information.
        """



        """ 
        # class OrderEvent(symbol, order_type, quantity, direction)
        # class FillEvent(datetime, symbol, exchange, quantity, direction, fill_cost, commission=None)

        datetime = 
        symbol = symbol
        exchange = FAKE_EXCHANGE
        quantity = quantity
        direction = direction
        fill_cost = 
        commission = None
        """
        if isinstance(event, OrderEvent):
            fill_event = FillEvent(
                                datetime=event.timestamp, 
                                symbol=event.symbol, 
                                exchange="FAKE_EXCHANGE",
                                quantity=event.quantity,
                                direction=event.direction,
                                fill_cost=None,
                                commission=None,
            )
            self.events.put(fill_event)


class IBKRExecutionHandler(EWrapper, EClient, ExecutionHandler):
    def __init__(self, events, order_routing="SMART", currency="USD"):
        EClient.__init__(self, self)
        self.events = events
        self.order_routing = order_routing
        self.currency = currency

    def error(self, reqId, errorCode, errorString):
        print(f"Error: {reqId} {errorCode} {errorString}")

    def execDetails(self, reqId, contract, execution):
        fill_event = FillEvent(
            datetime.datetime.utcnow(),
            contract.symbol,
            self.currency,
            execution.execId,
            execution.orderId,
            execution.side,
            execution.shares,
            execution.price
        )
        self.events.put(fill_event)

    def execute_order(self, event): # responsible for placing orders based on OrderEvent
        contract = Contract()
        contract.symbol = event.symbol
        contract.secType = "STK"
        contract.exchange = self.order_routing
        contract.currency = self.currency

        order = Order()
        order.action = event.order_type
        order.totalQuantity = event.quantity
        order.orderType = event.direction
        order.transmit = True

        self.placeOrder(self.client_id, contract, order)  # Assuming client_id is unique per order

    def start(self, host, port, client_id):
        self.connect(host, port, client_id)
        thread = threading.Thread(target=self.run)
        thread.start()

    def stop(self):
        self.disconnect()
