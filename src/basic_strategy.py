from item import TickData
from constant import OrderType, Direction, Offset, Status

class BasicStrategy:

    def __init__(self):
        self.eng = None

    def set_engine(self, eng):
        self.eng = eng

    def buy(self, symbol: str, price: float, volume: float, timestamp: int, callback = None):
        self.eng.place_order({
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.LONG,
            'offset': Offset.OPEN,
            'callback': callback,
            'timestamp': timestamp
        }, 'test')

    def sell(self, symbol: str, price: float, volume: float, timestamp: int, callback = None):
        self.eng.place_order({
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.LONG,
            'offset': Offset.CLOSE,
            'callback': callback,
            'timestamp': timestamp
        }, 'test')

    def short(self, symbol: str, price: float, volume: float, timestamp: int, callback = None):
        self.eng.place_order({
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.SHORT,
            'offset': Offset.OPEN,
            'callback': callback,
            'timestamp': timestamp
        }, 'test')

    def long(self, symbol: str, price: float, volume: float, timestamp: int,callback = None):
        self.eng.place_order({
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.LONG,
            'offset': Offset.OPEN,
            'callback': callback,
            'timestamp': timestamp
        }, 'test')
    
    def get_account(self):
        return self.eng.exchange.accounts['test']
