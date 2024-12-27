### class Future
![img](https://imgur.com/dMw2kQZ.png)

* 在同一個[OrderQueue](./OrderQueue.md) 內的訂單是相同的價位，所以在Future 這個 class 裡面，我們就可以根據不同的價格/買賣方，分別創建 OrderQueue，所以資料結構就定義成 **Dict[float,OrderQueue]** 代表在該價位(float)的所有訂單(OrderQueue)，在買賣方分別建立buy_book與sell_book，就可以視為在交易所中含有價格、數量、深度的OrderBook，結構如下圖所示


```python
.
.
.
ask_price1 : class OrderQueue(ask_price1)
ask_price0 : class OrderQueue(ask_price0)
------------------------------------------
bid_price0 : class OrderQueue(bid_price0)
bid_price1 : class OrderQueue(bid_price1)
.
.
.
```

* 完成了上述的資料結構，就可以開始根據訂單的類別(限/市價單,多/空,開/平)與價格進行買賣，主要寫在 **place_order(order: OrderData)** 這個函示中，大致邏輯如下
    * 限價單
        * 若訂單是 做多開倉 / 做空平倉，也就是買單(以下稱order)時
            ，去找到第一個價格 <= order.price 的 sell_book，呼叫該sell_book 的 match_order(order.volume)，找不到的話就把該筆買單加入到buy_book 裡面，等待後續搓合
        * 若訂單是 做空開倉 / 做多平倉，也就是賣單(以下稱order)時
            ，去找到第一個價格 >= order.price 的 buy_book，呼叫該buy_book 的 match_order(order.volume)，找不到的話就把該筆買單加入到 sell_book 裡面，等待後續搓合
    * 市價單
        * 跟上述邏輯一樣，只是價格變成 sell_book 的最低價或是 buy_book 的最高價，要特別注意的是，Hist Oder 都可以視為限價單，所以Hist Order 不會有市價單，因為該筆Hist Order 是根據過去市場價格決定的，所以一定會有一個價格