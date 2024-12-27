
所有class Strategy 都繼承 BasicStrategy ,透過 BasicStrategy的Engine下買賣單,不用再去考率買賣的邏輯

* Set Engine

```python
def set_engine(self, eng):
```

* Buy

```python
def buy(self, symbol: str, price: float, volume: float, callback = None):
    self.eng.place_order({
        'symbol': symbol,
        'price': price,
        'volume': volume,
        'is_history': False,
        'order_type': OrderType.LIMIT,
        'direction': Direction.LONG,
        'offset': Offset.OPEN,
        'callback': callback,
    }, 'test')
```

* Sell

```python
def sell(self, symbol: str, price: float, volume: float, callback = None):
```

* Short

```python
def short(self, symbol: str, price: float, volume: float, callback = None):
```

* Long

```python
def long(self, symbol: str, price: float, volume: float, callback = None):
```

* Example Usage

```python
class GridTrading(BasicStrategy):
    def __init__:
    .
    . existing code
    .
  
def main():
    bot = GridTrading()
    bot.buy('BTCUSDT',95000,1,None)
```
