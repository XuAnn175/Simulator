### class TickData

某一時間點，當下的最佳買價與最佳賣價與其相對應的Volume，可以想成自訂深度的OrderBook

Example Usage :

```python
tick_data = TickData({
        'symbol': 'APPL',
        'bid_price': [148.9, 148.8, 148.7, 148.6, 148.5],
        'bid_volume': [100, 200, 300, 400, 500],
        'ask_price': [150.0, 150.1, 150.2, 150.3, 150.4],
        'ask_volume': [100, 200, 300, 400, 500],
        'data_depth': 5
    })
```

![img](https://imgur.com/JXtYP9N.png)