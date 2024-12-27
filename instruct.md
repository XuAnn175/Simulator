
**simulator.py**

* **What is this code doing?**

  1. 如何使用 class OderQueue
  2. 如何使用 class Future
  3. **單筆**訂單 Match 的例子
* **How to run the code?**

  * python simulator.py

  main 裡面有不同的example,可以自己註解掉跑看看

**engine.py**

* **What is this code doing?**

  * 演示交易所搓合歷史訂單的過程
* **How to run the code?**

  1. 先去[Bybit](https://www.bybit.com/derivatives/en/history-data)下載2024-11-27 的 historical trade data (有點大)
  2. 把檔案放到./data下
  3. in /data : python unzip.py
  4. pip install tqdm
  5. in /src : python engine.py

  Note : engine.py : line132 可以改變資料的讀取量,如果只是要看搓合過程,可以設小一點(opts = {'head_num': 20} ),要看到較深的OrderBook Depth,可以設成 opts = {'head_num': 400000}

**main.py**

* **What is this code doing?**

  * 集合Strategy,Engine : Engine會搓合歷史訂單與策略送出來的訂單
  * 模擬策略訂單的Latency (詳見 [GridTrading](./reports/strategy/GridTrading.md))
  * 策略可以根據市場狀況下買/賣的決定
  * 往後只要設計好Strategy後，就可以直接import到main.py 做回測，詳細回測的模擬方法請見 [Engine](./reports/simulator/Engine.md)
* **How to run the code?**

  1. 先去[Bybit](https://www.bybit.com/derivatives/en/history-data)下載2024-11-27 的 historical trade data (有點大)
  2. 把檔案放到./data下
  3. in /data : python unzip.py
  4. in /src : python main.py

### **What we have achieved ?**

1. 使用歷史Trade Data來做微秒等級的回測
2. 回測邏輯的正確性（如何拿歷史訂單來搓合，搓合後如何不影響歷史資料）
3. 交易訂單與倉位管理
4. 定義資料的完整性（Future,OrderQueue,TickData,....)
5. 簡單網格交易機器人能正確運行

**Author : 鄭栩安**
