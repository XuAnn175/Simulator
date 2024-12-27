# class Engine

![img](https://imgur.com/I11GNXy.png)

* Engine是集合DataLoader,Exchange,Strategy，主要執行回測的地方

```python
def load_data(self, filename: str, symbol: str, opts = {}):
```

* load_data() : 讀取Historical Trade Data，統一timestamp格式後存到self.orderdata : List中( Data Soure : [Bybit](https://www.bybit.com/derivatives/en/history-data) )

```python
def set_exchange(self, exchange):
```

* set_exchange() : 初始化self.exchange

```python
def step(self):
```

* step() : 依序讀取self.order_data，將所有Historical Orders對交易所下單，如下圖所示 :

```python
def step(self):
    #...existing code
  
    next_order = self.order_data[self.tick_idx]
    # Send order to exchange
    self.exchange.place_order({
        'symbol': next_order['symbol'],
        'price': next_order['price'],
        'volume': next_order['size'],
        'direction': Direction.LONG if next_order['side'] == 'Buy' else Direction.SHORT,
        'order_type': OrderType.LIMIT,
        'offset': Offset.OPEN,
        'is_history': True
    },'test')

    # Get current orderbook data snapshot
    tick = self.exchange.snapshot()
    cur_price = float(self.exchange.cur_price[self.symbol])
  
    # Pass the current orderbook data and price to the strategy
    self.strategy.on_tick(tick,cur_price)
  
    # Store Account Status
    self.track_account('test', tick, cur_price)
  
    return tick
```

* 訂單就會被放到Exchange去搓合(詳細過程請見 [class Exchange](./Exchange.md))，在這一步驟，我們就能達成millisecond等級的回測，Strategy 也可以以根據市場狀態，在這裡下 Algo Order
* step() function的回傳值為 : 下完該筆訂單後Exchange的snapshot
* 透過self.tick_idx來控制現在正在處理哪一筆訂單，遍歷所有 Historical Orders 後即完成回測

```python
def start(self):
```

* start() : 開始回測，直到所有訂單都處理完成
