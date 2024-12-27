### 網格交易機器人 (Grid Trading)

#### 示意圖：

    Note : 這份Project 只有實做買低賣高網格交易機器人，反向的作為Future Work

![img](https://imgur.com/ZbAKQLz.png)

#### Class GridTrading

![img](https://imgur.com/R5I6ILC.png)

* low_price : 網格交易的最低價格
* high_price: 網格交易的最高價格
* step_price: 每個網格的價格區間
* profit: 每個網格預計賺取的價差
* min_balance : 當帳戶餘額低於這個min_balance時，結束交易
* grid（每個網格）:
  * buy_price : 買入價格
  * amount : 買入數量
  * state :
    * idle : 當市場價格不在這個grid的價格區間時，該grid狀態為idle
    * pending : 當價格一達到gird的買賣區間時，在buy_price下買單，在買單還沒完成前，state都設為pending
    * cover : 當買單成功交易後，bot會在sell_price下賣單，狀態設為cover，在賣單還沒完成前，state都設成cover，當賣單完成時，成功賺取價差，state 重新設為idle
    * 所以每一個網格都會在 idle -> pending -> cover -> idle ....這之間一直做循環，會這麼設計的原因是為了避免如果價格在某一個gird中劇烈震盪，我們不應該重複買/賣，一個網格只能先買後賣
  * sell_price : 售出價格
  * order_id : 訂單編號，目前還沒用到

```python
def on_tick(self, snapshot, cur_price,timestamp):
```

* **on_tick**()
* 這個function會在 [class Engine](./Engine.md) 的 step() 中被用到，當Engine在撮合某一筆歷史訂單時，會產生搓合後的OrderBook,Market Price，我們就可以回傳這個市場的資訊給 Strategy 做應用，讓Strategy可以根據市場的資訊做出決策
* 在class GridTrading 中就是在處理所有 grid 上述 State 的邏輯
* Future Works : 根據動態的市場資料做出決策

## How we deal with unrealizable profit (latency issue)?

```python
class Engine: 
    ...exsting code...
  
    def step(self):
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
    
        # Pass the current orderbook data and price to the strategy every 10 milliseconds
        if self.current_time - self.prev_time >= 10:
            self.strategy.on_tick(tick,cur_price,self.current_time)

        self.prev_time = self.current_time
        return tick

```

* 根據我們Simulator的回測方法，每當Class Engine 處理完一筆 Historical Data 後，Strategy都可以看到當前的Orderbook Data與 Market Price，這個在HFT其實是不合理的，因為我們沒有考慮中間的latency。
* 根據先前的測量，單趟的latency大約是5ms，我們保守一點抓10ms，代表如果某個Strategy持續聽在WebSocket，那他最快也要每10ms才能收到一次Market Data。
* 所以我們模擬latency的方式就是限制Strategy不能一直跟Simulator拿Market Data，只有每 >= 10ms過後，Starategy 才能拿 Market Data，並作出相對應的策略（如上面程式碼）

## Analysis of Grid Traiding

1. 我們將參數設定為 low_price=91000,high_price=93000,step_price=10,profit=10, amount=0.1 且拿2024/11/27 的 BTCUSDT 的前200000筆 Trade Data來做回測（約2hr的交易資料)
2. 以上參數的交易結果可以在 reports/account_history.csv 中看到，因為網格機器人只有用單純的price來決定買／賣，只要有漲就賺錢，剛好拿到的Trade Data有漲幅，所以有賺到錢（大約賺了300＄)
3. 這個網格交易機器人的demo 可以作為我們高頻回測系統的POC，也就是

   * 微秒等級的回測
   * 回測邏輯的正確性（如何拿歷史訂單來搓合）
   * 訂單與倉位管理
   * 定義資料的完整性（Future,OrderQueue,TickData,....)
4. Future Works : 用統計模型來設計交易策略
