import sys, os, logging
from engine import Engine
from grid_trading import GridTrading
from simulator import Exchange

engine = Engine()
engine.init_exchange()
engine.exchange.add_account('test', 1000000)

engine.load_data('../data/BTCUSDT2024-11-27.csv', 'BTCUSDT', opts = {'head_num': 200000})
st = GridTrading('BTCUSDT', 91000, 93000, 10, 10, 0.1, 200)
st.set_engine(engine)
engine.set_strategy(st)
engine.start()
