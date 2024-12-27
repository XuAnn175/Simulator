# Simulator 
## System Architecture
![img](https://imgur.com/JQJ3F6r.png)

## Overall Introduction
系統架構大致如上圖  
* class Strategy : 主要是在負責策略的執行
* class Exchange : 主要是在模擬交易所搓合的邏輯與訂單管理
* class DataLoader : 主要是將歷史資料載入Engine (TODO)
* class Visualizer : 主要是將策略的結果視覺化 (TODO)
* class Engine : 則是將上述功能聚集起來，是主要執行回測的地方

## Respective Detailed Introduction
[class Engine](../reports/Engine.md)
[class Exchange](../reports/Exchange.md)
[class Strategy(TODO)](../reports/Strategy.md)
[class DataLoader(TODO)](../reports/DataLoader.md)
[class Visualizer(TODO)](../reports/Visualizer.md)  

 Basic Data Types
 * [class OrderData](./OrderData.md)
 * [class TickData](./TickData.md)
 * [class Account](./Account.md) 
 * [Other Constant](./Constant.md)
