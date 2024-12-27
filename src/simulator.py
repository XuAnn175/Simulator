import pandas as pd
import numpy as np
import collections, sortedcontainers, datetime, sys
from tqdm import tqdm
from item import TickData, Snapshot, OrderData, Account, TradeData
from typing import List, Dict, Tuple
from inspect import isfunction
from constant import OrderType, Direction, Offset, Status
import csv
'''
TODO:
* consider last trade information(on event generation)
* visualization
'''

order_fill_list = []

class OrderQueue:
    '''
    in the bid/ask book, there is an order book for each price, consisted of
    all the orders on this price level.
    '''
    queue: List[Tuple[OrderData, List[OrderData]]]
    next_orders: List[OrderData]
    total_amount_var: float
    price: float

    def __init__(self, price: float):
        self.price = price
        self.queue = []
        self.next_orders = []
        self.total_amount_var = 0
        

    def __del__(self):
        self._consume_algo_order_list(self.next_orders, float('inf'))

    def add_order(self, order: OrderData):
        if order.is_history:
            self.queue.append([order, self.next_orders])
            self.next_orders = []
        else:
            self.next_orders.append(order)
        self.total_amount_var += order.remain()

    def _consume_algo_order_list(self, orders: List[OrderData], amount: float):
        global order_fill_list
        while len(orders) > 0:
            order = orders[0]
            if amount >= order.remain():
                trade_amount = order.remain()
                amount -= trade_amount
                order.traded += trade_amount
                self.total_amount_var -= trade_amount
                if hasattr(order, 'callback') and isfunction(order.callback):
                    order.callback()
                order_fill_list.append(TradeData(order.order_id, self.price, trade_amount))
                orders.pop(0)
            else:
                order.traded += amount
                order_fill_list.append(TradeData(order.order_id, self.price, amount))
                self.total_amount_var -= amount
                break

    def match_order(self, amount: float) -> float:
        '''
        match orders by given amount, return remaining amount that is not consumed.
        using FIFO algorithm currently
        '''
        hist_amount = amount
        while len(self.queue) > 0:
            hist_order, algo_orders = self.queue[0]
            if amount >= hist_order.remain():
                amount -= hist_order.remain()
                self._consume_algo_order_list(algo_orders, hist_order.remain())
                if len(algo_orders) > 0:
                    if len(self.queue) > 1:
                        self.queue[1][1] = algo_orders + self.queue[1][1] # 如果下一個hist_order存在,則將algo_orders加到下一個queue的algo_orders
                    else:
                        self.next_orders = algo_orders + self.next_orders # 如果沒有下一個hist_order,則將algo_orders加到next_orders
                self.queue.pop(0)
            else:
                hist_order.traded += amount
                self._consume_algo_order_list(algo_orders, amount)
                amount = 0
                break
        self.total_amount_var -= hist_amount - amount
        return amount

    def total_amount(self):
        return self.total_amount_var  # total volume of ALL orders (both hist and algo)

    def history_amount(self):
        return sum(map(lambda tp: tp[0].remain(), self.queue)) # sum of remaining volume for ONLY historical orders

    def cancel_data_order(self, amount: float):
        hist_amount = amount
        while len(self.queue) > 0:
            hist_order, algo_orders = self.queue[0]
            if amount >= hist_order.remain():
                amount -= hist_order.remain()
                if len(algo_orders) > 0:
                    if len(self.queue) > 1:
                        self.queue[1][1] = algo_orders + self.queue[1][1]
                    else:
                        self.next_orders = algo_orders + self.next_orders
                self.queue.pop(0)
            else:
                hist_order.volume -= amount
                amount = 0
                break
        self.total_amount_var -= hist_amount - amount
        return amount

    def cancel_algo_order(self, order_id: int):
        for hist, algos in self.queue:
            for idx, order in enumerate(algos):
                if order.order_id == order_id:
                    self.total_amount_var -= order.remain()
                    algos.pop(idx)
                    return

class Future:
    symbol: str
    buy_book: Dict[float, OrderQueue]
    sell_book: Dict[float, OrderQueue]

    def __init__(self, symbol: str, tick: TickData, max_depth: int):
        self.symbol = symbol
        self.max_depth = max_depth
        self.buy_book  = sortedcontainers.SortedDict()
        self.sell_book = sortedcontainers.SortedDict()
        for idx in range(tick.data_depth):
            q = OrderQueue(tick.bid_price[idx])
            q.add_order(OrderData({'volume': tick.bid_volume[idx], 'is_history': True, 'traded': 0}))
            self.buy_book[tick.bid_price[idx]] = q
            q = OrderQueue(tick.ask_price[idx])
            q.add_order(OrderData({'volume': tick.ask_volume[idx], 'is_history': True, 'traded': 0}))
            self.sell_book[tick.ask_price[idx]] = q

    def place_order(self, order: OrderData):
        global order_fill_list
        if order.volume == 0:
            return
        if order.order_type == OrderType.LIMIT:
            # 限價單 : 只在 <= order.price 的價格下單
            if order.direction == Direction.LONG and order.offset == Offset.OPEN or order.direction == Direction.SHORT and order.offset == Offset.CLOSE:
                # BUY : open LONG posotion or close SHORT position
                sell_prices = list(self.sell_book.keys())
                for sp in sell_prices:
                    if sp > order.price:
                        break
                    if not order.is_history: # completed Algo Order, no need to match against order book (can't either)
                        order.callback() if hasattr(order, 'callback') else None
                        order_fill_list.append(TradeData(order.order_id, sp, order.volume))
                        order.volume = 0
                        break
                    order.volume = self.sell_book[sp].match_order(order.volume) # Hist Order match against order book
                    if self.sell_book[sp].history_amount() <= 0:
                        del self.sell_book[sp]  # remove empty price levels, because only hist order will affect future orderbook
                    else:
                        break
                if order.volume > 0: # if order is not completed, add to order book
                    if order.price not in self.buy_book:
                        self.buy_book[order.price] = OrderQueue(order.price)
                    self.buy_book[order.price].add_order(order)
            elif order.direction == Direction.SHORT and order.offset == Offset.OPEN or order.direction == Direction.LONG and order.offset == Offset.CLOSE:
                # SELL : open SHORT position or close LONG position
                buy_prices = list(reversed(self.buy_book.keys()))
                for bp in buy_prices:
                    if bp < order.price:
                        break
                    if not order.is_history: 
                        order.callback() if hasattr(order, 'callback') else None
                        order_fill_list.append(TradeData(order.order_id, bp, order.volume))
                        order.volume = 0
                        break
                    order.volume = self.buy_book[bp].match_order(order.volume) 
                    if self.buy_book[bp].history_amount() <= 0:
                        del self.buy_book[bp]
                    else:
                        break
                if order.volume > 0:
                    if order.price not in self.sell_book:
                        self.sell_book[order.price] = OrderQueue(order.price)
                    self.sell_book[order.price].add_order(order)
        elif order.order_type == OrderType.MARKET:
            if order.is_history:
                # not possible
                return
            if order.direction == Direction.LONG and order.offset == Offset.OPEN or order.direction == Direction.SHORT and order.offset == Offset.CLOSE:
                sell_prices = list(self.sell_book.keys())
                order.callback() if hasattr(order, 'callback') else None
                order_fill_list.append(TradeData(order.order_id, sell_prices[0], order.volume))
                order.volume = 0
            elif order.direction == Direction.SHORT and order.offset == Offset.OPEN or order.direction == Direction.LONG and order.offset == Offset.CLOSE:
                buy_prices = list(reversed(self.buy_book.keys()))
                order.callback() if hasattr(order, 'callback') else None
                order_fill_list.append(TradeData(order.order_id, buy_prices[0], order.volume))
                order.volume = 0
        else:
            pass

    def cancel_data_order(self, price: float, volume: float):
        # 在sell_book和buy_book中找到price，並取消volume的訂單,如果訂單取消後，history_amount為0，則刪除該price的訂單
        # 在 historical orders 中，order_id 並不重要，只要將相對應的 volume 減去即可
        if price in self.sell_book:
            self.sell_book[price].cancel_data_order(volume)
            if self.sell_book[price].history_amount() == 0:
                del self.sell_book[price]
        if price in self.buy_book:
            self.buy_book[price].cancel_data_order(volume)
            if self.buy_book[price].history_amount() == 0:
                del self.buy_book[price]

    def cancel_order(self, order_id: int):
        order = OrderData.get_order(order_id)
        if order.price in self.sell_book:
            self.sell_book[order.price].cancel_algo_order(order_id)
            if self.sell_book[order.price].history_amount() == 0:
                del self.sell_book[order.price]
        if order.price in self.buy_book:
            self.buy_book[order.price].cancel_algo_order(order_id)
            if self.buy_book[order.price].history_amount() == 0:
                del self.buy_book[order.price]

    def snapshot(self) -> TickData:
        sps = list(self.sell_book.keys())[:5]
        bps = list(reversed(self.buy_book.keys()))[:5]
        depth = min(len(sps), len(bps), self.max_depth)
        tick = TickData({'symbol': self.symbol})
        tick.set_data_depth(depth)
        for i in range(depth):
            tick.bid_price[i] = bps[i]
            tick.bid_volume[i] = self.buy_book[bps[i]].total_amount()
            tick.ask_price[i] = sps[i]
            tick.ask_volume[i] = self.sell_book[sps[i]].total_amount()
        return tick


class Exchange:
    accounts: Dict[str, Account]
    order_account: Dict[int, str]
    futures: Dict[str, Future]

    def __init__(self, snapshot: Snapshot, max_depth: int):
        self.futures = {}
        for k in snapshot.keys():
            self.futures[k] = Future(k, snapshot[k], max_depth)
        self.accounts = {}
        self.order_account = {}
        self.cur_price = {}
        self.prev_non_zero_price = {}
        self.trade_history = {}

    def add_account(self, name: str, balance: float = 0):
        self.accounts[name] = Account(name, balance, self.futures.keys())
        self.trade_history[name] = []
    
    def get_accounts(self):
        return self.accounts
    
    def get_account(self, name):
        return self.accounts[name]

    def place_order(self, d, account_name = None) -> OrderData:
        if 'is_history' not in d:
            d['is_history'] = False

        order = OrderData(d)
        # simulate latency
        order.traded = 0
        order.status = Status.SUBMITTING
        symbol = order.symbol

        if symbol in self.futures:
            self.futures[symbol].place_order(order)
        else:
            print(f'future {symbol} not exist!')
            return

        if account_name is not None:
            if account_name not in self.accounts:
                print(f'account {account_name} not exist!')
            else:
                self.order_account[order.order_id] = account_name

        price = self.update_cur_price(symbol)
        self.process_trade_data(price, order.timestamp)
        return order

    def cancel_data_order(self, future: str, price: float, volume: float):
        self.futures[future].cancel_data_order(price, volume)

    def snapshot(self) -> Snapshot:
        ss = {}
        for symbol in self.futures:
            ss[symbol] = self.futures[symbol].snapshot()
        return ss

    def update_cur_price(self, symbol: str) -> float:
        # cur_price[symobl] is the mean of the lowest ask price and the highest bid price
        if len(self.futures[symbol].sell_book.keys()) > 0 and len(self.futures[symbol].buy_book.keys()) > 0:
            best_ask = float(list(self.futures[symbol].sell_book.keys())[0])
            best_bid = float(list(self.futures[symbol].buy_book.keys())[-1])
            self.cur_price[symbol] = float((best_ask + best_bid) / 2)
            self.prev_non_zero_price[symbol] = self.cur_price[symbol]
        else:
            self.cur_price[symbol] = self.prev_non_zero_price[symbol]
        return self.cur_price[symbol]

    def process_trade_data(self, price: float, timestamp: int): # position management
        global order_fill_list
        for fill in order_fill_list:
            order_id = fill.order_id
            if order_id in self.order_account:
                account = self.accounts[self.order_account[order_id]] # get account from order id
                order = OrderData.get_order(order_id)
                # print(f"----------timestamp: {timestamp} ----------")
                if order.direction == Direction.LONG and order.offset == Offset.OPEN:
                    # print(f'long open, balance - {fill.fill_amount * fill.price}')
                    account.balance -= fill.fill_amount * fill.price
                    account.position[order.symbol]['long'] += fill.fill_amount
                    # account.position[order.symbol]['long'] = round(account.position[order.symbol]['long'], 10)
                elif order.direction == Direction.LONG and order.offset == Offset.CLOSE:
                    # print(f'long close, balance + {fill.fill_amount * fill.price}')
                    account.balance += fill.fill_amount * fill.price
                    account.position[order.symbol]['long'] -= fill.fill_amount
                    # account.position[order.symbol]['long'] = round(account.position[order.symbol]['long'], 10)
                elif order.direction == Direction.SHORT and order.offset == Offset.OPEN:
                    # print(f'short open, balance + {fill.fill_amount * fill.price}')
                    account.balance += fill.fill_amount * fill.price
                    account.position[order.symbol]['short'] += fill.fill_amount
                    # account.position[order.symbol]['short'] = round(account.position[order.symbol]['short'], 10)
                elif order.direction == Direction.SHORT and order.offset == Offset.CLOSE:
                    # print(f'short close, balance - {fill.fill_amount * fill.price}')
                    account.balance -= fill.fill_amount * fill.price
                    account.position[order.symbol]['short'] -= fill.fill_amount
                    # account.position[order.symbol]['short'] = round(account.position[order.symbol]['short'], 10)

                account_value = account.balance + (account.position[order.symbol]['long'] - account.position[order.symbol]['short']) * price
                # print(f"account balance: {account.balance}")
                # print(f"long: {account.position[order.symbol]['long']}, short: {account.position[order.symbol]['short']}")
                # print(f"account value: {account_value}")
                # print(f"mid price: {price}")
                # print('--------------------------------')
                # [timestamp, symbol, balance, long, short, account_value, price]
                self.trade_history[account.name].append([timestamp, order.symbol, account.balance, account.position[order.symbol]['long'], account.position[order.symbol]['short'], account_value, price])
        order_fill_list = []

    def save_trade_history(self, filename: str):
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'symbol', 'balance', 'long', 'short', 'account_value', 'price'])
            for account in self.trade_history:
                writer.writerows(self.trade_history[account])
        self.trade_history = {}
    
if __name__ == '__main__':
    """
    1.an example of how to use the OrderQueue
    order_queue = OrderQueue(100)
    order_queue.add_order(OrderData({'volume': 98, 'is_history': False, 'traded': 0}))
    order_queue.add_order(OrderData({'volume': 100, 'is_history': True, 'traded': 0}))
    order_queue.match_order(30)
    order_queue.match_order(50)
    print(order_fill_list[0].fill_amount)
    print(order_fill_list[1].fill_amount)
    print(order_queue.total_amount())
    print(order_queue.history_amount())
    """

    
    """
    2.an example of how to use the Future
    tick_data = TickData({
        'symbol': 'AAPL',
        'bid_price': [148.9, 148.8, 148.7, 148.6, 148.5],
        'bid_volume': [100, 200, 300, 400, 500],
        'ask_price': [150.0, 150.1, 150.2, 150.3, 150.4],
        'ask_volume': [100, 200, 300, 400, 500],
        'data_depth': 5
    })
    
    future = Future('AAPL', tick_data, 5)
    
    order = OrderData({
        'symbol': 'AAPL', 
        'order_type': OrderType.LIMIT, 
        'direction': Direction.LONG, 
        'offset': Offset.OPEN, 
        'price': 150.0, #if you change the price to 149.5, this order will be shown in the order book snapshot
        'volume': 100,
        'is_history': False,
        'callback': lambda: print('successfully placed order'),
        'traded': 0
    })
    
    # place order
    future.place_order(order)

    tick = future.snapshot()
    
    for i in range(future.max_depth):
        print(f'ask_price: {tick.ask_price[future.max_depth - i - 1]}, ask_volume: {tick.ask_volume[future.max_depth - i - 1]}')
    print('--------------------------------')
    for i in range(future.max_depth):
        print(f'bid_price: {tick.bid_price[i]}, bid_volume: {tick.bid_volume[i]}')
    
    # traded amount
    if len(order_fill_list) > 0:
        print(f"Traded amount: {order_fill_list[0].fill_amount}")

    """

    # 3. an example of match order
    order_queue = OrderQueue(price=100)

    # Add two algo orders
    algo_order1 = OrderData({
        'volume': 300, 
        'is_history': False, 
        'traded': 0,
        'callback': lambda: print("Algo order 1 filled!")
    })
    algo_order2 = OrderData({
        'volume': 400, 
        'is_history': False, 
        'traded': 0,
        'callback': lambda: print("Algo order 2 filled!")
    })
    order_queue.add_order(algo_order1)
    order_queue.add_order(algo_order2)

    # Add the historical order
    hist_order = OrderData({'volume': 1000, 'is_history': True, 'traded': 0})
    order_queue.add_order(hist_order)

    # Now let's match 800 shares
    remaining = order_queue.match_order(800)
    if len(order_fill_list) > 0:
        for trade in order_fill_list:
            print(f"Traded price: {trade.price}, traded amount: {trade.fill_amount}")
    