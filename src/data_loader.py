import json
import datetime as dt
from typing import List, Dict
from item import TickData
import pandas as pd

class DataLoader:   
    def process_order_book(self, file_path: str) -> List[TickData]:
        # Initialize lists to store all bid/ask prices and volumes
        bid_prices: Dict[float, float] = {}  # price -> volume
        ask_prices: Dict[float, float] = {}  # price -> volume
        tick_list = []
        
        with open(file_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                timestamp = data['ts']
                
                if data['type'] == 'snapshot':
                    bid_prices.clear()
                    ask_prices.clear()
                    
                    for price_str, volume_str in data['data']['b']:
                        bid_prices[float(price_str)] = float(volume_str)
                    for price_str, volume_str in data['data']['a']:
                        ask_prices[float(price_str)] = float(volume_str)
                        
                elif data['type'] == 'delta':
                    # Update based on delta rules
                    for price_str, volume_str in data['data']['b']:
                        price, volume = float(price_str), float(volume_str)
                        if volume == 0:  # Delete if volume is 0
                            bid_prices.pop(price, None)
                        else:  # Insert new or update existing
                            bid_prices[price] = volume
                            
                    for price_str, volume_str in data['data']['a']:
                        price, volume = float(price_str), float(volume_str)
                        if volume == 0:  # Delete if volume is 0
                            ask_prices.pop(price, None)
                        else:  # Insert new or update existing
                            ask_prices[price] = volume
                
                tick = TickData({'data_depth': 5})
                tick.timestamp = timestamp
                
                # Sort and get top 5 bids (highest prices)
                sorted_bids = sorted(bid_prices.items(), reverse=True)  
                for i in range(min(5, len(sorted_bids))):
                    tick.bid_price[i] = sorted_bids[i][0]
                    tick.bid_volume[i] = sorted_bids[i][1]
                
                # Sort and get top 5 asks (lowest prices)
                sorted_asks = sorted(ask_prices.items()) 
                for i in range(min(5, len(sorted_asks))):
                    tick.ask_price[i] = sorted_asks[i][0]
                    tick.ask_volume[i] = sorted_asks[i][1]
                
                tick_list.append(tick)
                    
        return tick_list
    
    def load_data(self, filename: str, symbol: str, opts = {}):
        """
        Load trade data from CSV file
        Expected CSV columns: datetime, price, volume, direction
        """
        #read only the first 10 rows
        if 'head_num' in opts:
            head_num = opts['head_num']
        else:
            head_num = 10
        df = pd.read_csv(filename).head(head_num) #chagne this to see different orderbook depth
        
        # Convert datetime by * 1000 and the round to int
        df['timestamp'] = (round(df['timestamp'] * 1000)).astype(int)

        # Apply date filters if provided
        if 'start_timestamp' in opts:
            df = df[df['timestamp'] > opts['start_timestamp']]
        if 'end_timestamp' in opts:
            df = df[df['timestamp'] < opts['end_timestamp']]
        
        # Store as list of dictionaries for easier processing
        self.order_data = df.to_dict('records')
        self.tick_idx = 0
        
        return df
    
if __name__ == "__main__":
    file_path = "../data/2024-11-27_BTCUSDT_ob500_truncated.data"
    tick_data_list = DataLoader().process_order_book(file_path)
    indx = 1
    print(f'timestamp: {tick_data_list[indx].timestamp}')
    for i in range(len(tick_data_list[indx].ask_price)):
        print(f'ask_price: {tick_data_list[indx].ask_price[len(tick_data_list[indx].ask_price) - i - 1]}, ask_volume: {tick_data_list[indx].ask_volume[len(tick_data_list[indx].ask_volume) - i - 1]}')
    print('--------------------------------')
    for i in range(len(tick_data_list[indx].bid_price)):
        print(f'bid_price: {tick_data_list[indx].bid_price[i]}, bid_volume: {tick_data_list[indx].bid_volume[i]}')
