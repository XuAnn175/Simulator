### class Exchange

![img](https://imgur.com/j0sOC8o.png)

* 把底層的搓合邏輯移到 [class Future](../constant/Future.md) 後，class Exchange 就能管理比較 high-level 的資料了，像是帳號、倉位管理、訂單管理
* accounts: Dict[str,Account]

```python=
acoounts: Dict[str,Account]
#加入一個帳號 主要是透過以下 function
def add_account(self, name: str, balance: float = 0):
        self.accounts[name] = Account(name, balance, self.futures.keys())
                                     #name, balance, postions
```

* order_acoount: Dict[int,str] => order_id : account_name

```python=
#紀錄某筆訂單屬於哪個帳號
self.order_account[order.order_id] = account_name
```

* futures: Dict[str,Future] => symbol : class Future

  該帳號的所有futures
* **place_order(self, d, account_name = None) -> OrderData:**
  &nbsp;&nbsp;&nbsp;&nbsp;**d** : Order 的資訊 (class OrderData)
  &nbsp;&nbsp;&nbsp;&nbsp;**account_name** : 帳號名稱
  Example Usage :

  ```python
    exchange = Exchange()

    order = OrderData({
        'symbol': 'AAPL', 
        'order_type': OrderType.LIMIT, 
        'direction': Direction.LONG, 
        'offset': Offset.OPEN, 
        'price': 150.0, 
        'volume': 100,
        'is_history': False,
        'callback': lambda: print('successfully placed order'),
        'traded': 0
    })

    exchange.place_order(order,'Adam')
                    #oder info,user name
  ```
  如此一來，Bot 就可以 High-level 的直接用 place_order 下單了
* **_process_trade_data():**
  透過已經完成的訂單，管理帳號倉位，我將帳號與倉位的關係定成 :

  ```python
  account.position[symbol] = {'long': 0, 'short': 0}
  ```
  所以根據不同操作，倉位的增減關係為 :

  * 做多開倉 :

  ```python
  account.position[symbol]['long'] += order.price * order.volume
  ```
  * 做多平倉 :

  ```python
  account.position[symbol]['long'] -= order.price * order.volume
  ```
  * 做空開倉 :

  ```python
  account.position[symbol]['short'] -= order.price * order.volume
  ```
  * 做空平倉 :

  ```python
  account.position[symbol]['short'] += order.price * order.volume
  ```
