from item import TickData
from basic_strategy import BasicStrategy
import sys, os, logging
from engine import Engine
from simulator import Exchange

class GridTrading(BasicStrategy):
    def __init__(self, symbol: str, low_price: float, high_price: float, step_price: float, profit: float, amount: float, min_balance: float):
        super().__init__()
        self.grids = []
        self.low_price = low_price
        grid_num = int((high_price - low_price) / step_price) + 1
        self.high_price = grid_num * step_price + low_price
        self.step_price = step_price
        self.profit = profit # fixed profit for better extensibility,classical grid trading would set profit = step_price
        self.amount = amount
        self.symbol = symbol
        self.min_balance = min_balance
        for idx in range(grid_num - 1):
            self.grids.append({
                'buy_price': round(low_price + step_price * idx, 1),
                'amount': amount,
                'state': 'idle', # idle -> pending -> cover -> idle
                'sell_price': round(low_price + step_price * idx + profit, 1),
                'orderId': -1
            })

    def on_tick(self, snapshot, cur_price,timestamp):
        """
        Place order based on the current market condition (orderbook and price)
        """
        tick = snapshot[self.symbol]

        if cur_price < self.low_price or cur_price > self.high_price:
            return
        
        idx = int((cur_price - self.low_price) / self.step_price)
        if idx < 0 or idx >= len(self.grids):
            return
        
        cell = self.grids[idx]
        if cell['state'] != 'idle':
            return
        
        account = self.get_account()
        if account.balance < self.min_balance:
            print('no enough balance, stop sending order.')
            return

        def on_cover_order_finish():
            cell['state'] = 'idle'

        def on_buy_order_finish():
            cell['state'] = 'cover'
            self.sell(self.symbol, cell['sell_price'], self.amount, timestamp, on_cover_order_finish)

        cell['state'] = 'pending'
        self.buy(self.symbol, cell['buy_price'], self.amount, timestamp, on_buy_order_finish)

if __name__ == '__main__':

    engine = Engine()
    engine.init_exchange()
    engine.exchange.add_account('test', 1000000)

    engine.load_data('../data/BTCUSDT2024-11-27.csv', 'BTCUSDT', opts = {'head_num': 200000})
    st = GridTrading('BTCUSDT', 91000, 93000, 10, 10, 0.1, 200)
    st.set_engine(engine)
    engine.set_strategy(st)
    engine.start()
