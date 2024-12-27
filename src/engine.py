import datetime as dt
import pandas as pd
from constant import OrderType, Direction, Offset
import logging
from simulator import Exchange
from item import TickData
from tqdm import tqdm
from data_loader import DataLoader
logger = logging.getLogger('engine')

class Engine:
    '''
    Engine aggregates basic functions, it loads data, runs simulator and strategies.
    '''
    def __init__(self):
        self.order_data = []  
        self.tick_idx = 0   
        self.symbol = 'BTCUSDT'  
        self.exchange = None
        self.current_time = None
        self.prev_time = 0
        self.data_loader = DataLoader()
        self.strategy = None
        self.account_history = {} # timestamp, balance, position total value, long position, short position, price
    
    def load_data(self, filename: str, symbol: str, opts = {}):
        """
        Load trade data from CSV file
        """
        df = self.data_loader.load_data(filename, symbol, opts)
        
        # Store as list of dictionaries for easier processing
        self.order_data = df.to_dict('records')
        self.tick_idx = 0
        
        return df

    def init_exchange(self):
        snapshot = {'BTCUSDT': TickData({
            'symbol': 'BTCUSDT',
            'bid_price': [0,0,0,0,0],
            'bid_volume': [0,0,0,0,0],
            'ask_price': [0,0,0,0,0],
            'ask_volume': [0,0,0,0,0],
            'data_depth': 5
        })}
        self.exchange = Exchange(snapshot, 5)
        self.account_history['test'] = []
    
    def set_strategy(self, strategy):
        self.strategy = strategy

    def set_exchange(self, exchange):
        self.exchange = exchange

    def step(self):
        """
        Process one order at a time
        Returns the current market snapshot or None if finished
        """
        # Check if we've processed all orders
        if self.tick_idx >= len(self.order_data):
            print('backtesting finished')
            return None
            
        # Get next order
        next_order = self.order_data[self.tick_idx]
        
        # Update current time and tick index
        self.current_time = round(next_order['timestamp'] * 1000)
        self.tick_idx += 1
        
        # Send order to exchange
        self.exchange.place_order({
            'symbol': next_order['symbol'],
            'price': next_order['price'],
            'volume': next_order['size'],
            'direction': Direction.LONG if next_order['side'] == 'Buy' else Direction.SHORT,
            'order_type': OrderType.LIMIT,
            'offset': Offset.OPEN,
            'is_history': True,
            'timestamp': self.current_time
        },'test')
        # Get current orderbook data snapshot
        tick = self.exchange.snapshot()
        cur_price = float(self.exchange.cur_price[self.symbol])
        # Pass the current orderbook data and price to the strategy every 5 milliseconds
        if self.current_time - self.prev_time >= 10:
            self.strategy.on_tick(tick,cur_price,self.current_time)

        self.prev_time = self.current_time
        return tick
    
    def save_trade_history(self, filename):
        self.exchange.save_trade_history(filename)

    def start(self):
        """
        Run the simulation until all orders are processed
        """
        for _ in tqdm(range(len(self.order_data)), desc='processing orders'):
            tick = self.step()
            # if len(tick['BTCUSDT'].ask_price) == 0 and len(tick['BTCUSDT'].bid_price) == 0:
            #     continue
            # print(f'current time: {self.current_time}')
            # print(f'current price: {self.exchange.cur_price[self.symbol]}')
            # tick['BTCUSDT'].show()
            if tick is None:
                break
        self.save_trade_history('account_history.csv')

    def place_order(self, order_dict, account_name=None):
        """
        Place a new order through the exchange
        """
        return self.exchange.place_order(order_dict, account_name)

if __name__ == '__main__':
    
    snapshot = {'BTCUSDT': TickData({
        'symbol': 'BTCUSDT',
        'bid_price': [0,0,0,0,0],
        'bid_volume': [0,0,0,0,0],
        'ask_price': [0,0,0,0,0],
        'ask_volume': [0,0,0,0,0],
        'data_depth': 5
    })}
    exchange = Exchange(snapshot, 5)
    exchange.add_account('test')
    engine = Engine()

    engine.load_data('../data/BTCUSDT2024-11-27.csv', 'BTCUSDT', opts = {'head_num': 200000})
    engine.set_exchange(exchange)
    engine.start()
    engine.save_trade_history('trade_history.csv')