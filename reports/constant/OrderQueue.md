### class OrderQueue

* 每一個價位都會用一個OrderQueue 來儲存該價位的所有訂單 i.e. 在相同OrderQueue裡面的訂單為相同價位的 [Order](./OrderData.md)
* 且OrderQueue的資料結構如下

```python
queue: List[Tuple[OrderData, List[OrderData]]]
```

* **Why like this?**

  1. 用List 模擬Queue 的 FIFO 行為 : 相同價格的訂單，到達時間越快，越優先搓合
  2. Tuple(Hist Order ,list(Algo Order)) :
     * 這個Tuple 的意義為 :與某一 Hist Order 相同時間抵達 or 比該 Hist Order 早抵達的所有 Algo Order
     * 所以我們可以想成 : 有兩個平行的simlator ，一個在搓合歷史資料(Hist Order)，一個在拿歷史資料搓合Algo Order，只有Hist Order 會影響 Algo Order 的搓合狀況，Algo Order **不能**影響 Hist Order 的搓合狀況，Hist Order 的搓合是完全獨立的，Algo Order 只是參考歷史訂單來"虛擬"搓合而已。
     * 根據上述，list[Algo Orders] 的 total volume 不能比 Hist Order 的 volume 大，不然會影響後面OrderBook 的走勢 (拿往後的歷史資料來回測也就沒意義了)
     * 以程式邏輯來看，我們不用寫兩個simulator(也寫不出來?)，只要在搓合某筆 Hist Order 時，同時去檢查那些跟他同時or比他早的那些 Algo Order 能不能搓合成功，這樣就可以達到回測的目的了
     * 若某筆 Algo Order 搓合成功，可以直接pop 掉，否則就加到下一個 Tuple 的 list(Algo Order) 裡面，因為該筆訂單還沒成交，這樣一直下去直到queue 為空
     * Example (simulator.py line 320 ~ line 346):

  ```python
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

      # Match volume 800 
      remaining = order_queue.match_order(800)
      if len(order_fill_list) > 0:
          for trade in order_fill_list:
              print(f"Traded price: {trade.price}, traded amount: {trade.fill_amount}")

  ```

  ```
  Execution Result : 
  Algo order 1 filled!
  Algo order 2 filled!
  Traded price: 100, traded amount: 300
  Traded price: 100, traded amount: 400
  ```
