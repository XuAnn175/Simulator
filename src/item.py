import numpy as np
import datetime as dt
from typing import List, Dict, Callable, Any
from constant import OrderType, Direction, Offset, Status
import logging

logger = logging.getLogger('item')

class Account:
    name: str
    balance: float
    position: Dict[str, Dict[str, float]]

    def __init__(self, name: str, balance = 0, symbols: List[str] = []):
        self.name = name
        self.balance = balance
        self.position = {}
        for s in symbols:
            self.position[s] = {'long': 0, 'short': 0}

class TickData:
    symbol: str
    timestamp: int

    data_depth: int
    bid_price: List[float] # large -> small
    ask_price: List[float] # small -> large
    bid_volume: List[float]
    ask_volume: List[float]


    def __init__(self, d = {}):
        if d == {}:
            pass
        if 'data_depth' in d:
            self.set_data_depth(d['data_depth'])
        keys = ['symbol', 'timestamp', 'bid_price', 'ask_price', 'bid_volume', 'ask_volume']
        for k in keys:
            if k in d:
                setattr(self, k, d[k])

    def set_data_depth(self, data_depth):
        self.data_depth = data_depth
        self.bid_price = [0 for i in range(data_depth)]
        self.ask_price = [0 for i in range(data_depth)]
        self.bid_volume = [0 for i in range(data_depth)]
        self.ask_volume = [0 for i in range(data_depth)]

    def show(self):
        print(f'symbol: {self.symbol}')
        for i in range(self.data_depth):
            print(f'ask_price: {self.ask_price[self.data_depth - i - 1]}, ask_volume: {self.ask_volume[self.data_depth - i - 1]}')
        print('--------------------------------')
        for i in range(self.data_depth):
            print(f'bid_price: {self.bid_price[i]}, bid_volume: {self.bid_volume[i]}')
        print('')
# exchange snapshot is a dict from symbols to tick data
Snapshot = Dict[str, TickData]

class OrderData:
    order_count: int = 0
    order_dict: Dict[int, 'OrderData'] = {}
    estimated_latency: int = 5
    symbol: str
    is_history: bool
    order_id: int
    order_type: OrderType
    direction: Direction
    offset: Offset
    price: float
    volume: float
    traded: float
    status: Status
    callback: Callable[['OrderData'], None]
    timestamp: int

    def __init__(self, d: Dict[str, Any]):
        keys = ['symbol', 'is_history', 'order_type', 'direction', 'offset', 'price', 'volume', 'traded', 'status', 'callback', 'timestamp']
        for k in keys:
            if k in d:
                setattr(self, k, d[k])
        OrderData.order_count += 1
        self.order_id = OrderData.order_count
        OrderData.order_dict[self.order_id] = self

    def remain(self):
        return self.volume - self.traded

    @staticmethod
    def get_order(order_id: int) -> 'OrderData':
        return OrderData.order_dict[order_id]

class TradeData():
    """
    Trade data contains information of a fill of an order. 
    One order can have several trade fills.
    """
    order_id: int
    price: float
    fill_amount: float

    def __init__(self, order_id, price, fill_amount):
        self.order_id = order_id
        self.price = price
        self.fill_amount = fill_amount
