# High Frequency Trading Backtesing Simulator

## System Architecture

![img](https://imgur.com/k9PTp3P.png)

## Overall Introduction

系統架構大致如上圖

* class Strategy : 主要是在負責策略的執行
* class Exchange : 主要是在模擬交易所搓合的邏輯與訂單管理
* class DataLoader : 主要是將歷史資料載入Engine
* class Visualizer : 主要是將策略的結果視覺化 (TODO)
* class Engine : 則是將上述功能聚集起來，是主要執行回測的地方，

## Respective Detailed Introduction

* [class Engine](./reports/simulator/Engine.md)
* [class Exchange](./reports/simulator/Exchange.md)
* [class Visualizer(TODO)](./reports/strategy/Visualizer.md)
* [class DataLoader](./reports/simulator/DataLoader.md)
* Basic Data Types
  * [class OrderData](./reports/constant/OrderData.md)
  * [class TickData](./reports/constant/TickData.md)
  * [class Account](./reports/constant/Account.md)
  * [Other Constant](./reports/constant/Constant.md)

## Strategy

* [class Basic Strategy](./reports/strategy/BasicStrategy.md)
* [class GridTrading](./reports/strategy/GridTrading.md)
