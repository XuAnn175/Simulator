### **class OrderData**

* order_count : 作為 order的 id 計數器，是一個 class level 的變數，當該變數增加時，所有class 為 OrderData 的 Obejct 的 order_count 都會增加
* order_dict : 某個 order_id 所對應的 OrderData
* is_history : 該筆資料為歷史資料 (is_history=true) 或是 Algo Order (is_history = false)
* order_type : LIMIT/MARKET/STOP/FAK/FOK
* direction : LONG/SHORT
* offest : NONE/OPEN/CLOSE/CLOSETODAY
* volume : 該筆訂單的需求量
* traded : 該筆訂單的成交量
* status : SUBMITTING/NOTTRADED/PARTTRADED/ALLTRADED/CANCELLED/REJECTED
* callback : 可以在訂單成交時呼叫

![img](https://imgur.com/DzdhFh6.png)