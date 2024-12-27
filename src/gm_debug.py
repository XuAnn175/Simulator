from item import TickData
from basic_strategy import BasicStrategy
import sys, os, logging
from engine import Engine
from simulator import Exchange
import numpy as np

class GMStrategy(BasicStrategy):
    def __init__(self, symbol: str, history_length: int, mu: float, trading_options: list, 
                 min_balance: float, short_ma_period: int = 5, long_ma_period: int = 20):
        """
        Initialize the GMStrategy.
        
        Parameters:
        - symbol: Trading symbol
        - history_length: Length of price history for GM(1,1)
        - mu: Weight coefficient for objective function (0 < mu < 1)
        - trading_options: List of possible trading amounts
        - min_balance: Minimum balance required
        - short_ma_period: Period for short-term moving average
        - long_ma_period: Period for long-term moving average
        """
        super().__init__()
        self.symbol = symbol
        self.history_length = history_length
        self.mu = mu
        self.trading_options = trading_options
        self.min_balance = min_balance
        
        # MA parameters
        self.short_ma_period = short_ma_period
        self.long_ma_period = long_ma_period
        
        # Price history for both GM(1,1) and MA calculations
        self.price_history = []
        
        # MA signals
        self.prev_short_ma = None
        self.prev_long_ma = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"GMStrategy-{self.symbol}")

    def predict_gm11(self, data: list) -> float:
        """
        Predict the next price using GM(1,1) model.
        """
        n = len(data)
        if n < 4:  # Need at least 4 points for reliable prediction
            return data[-1]

        # Step 1: Accumulated Generating Operation (AGO)
        x1 = np.cumsum(data)

        # Step 2: Adjacent Mean Sequence
        z1 = 0.5 * (x1[:-1] + x1[1:])

        # Step 3: Build matrices for least squares estimation
        B = np.column_stack((-z1, np.ones(n-1)))
        Y = data[1:]

        # Step 4: Parameter estimation
        try:
            theta = np.linalg.inv(B.T @ B) @ B.T @ Y
            a, b = theta
        except np.linalg.LinAlgError:
            self.logger.error("Matrix inversion failed in GM(1,1)")
            return data[-1]

        # Step 5: Predict next value
        def f(k):
            return (data[0] - b/a) * np.exp(-a * k) + b/a

        # Predict x1(n+1)
        x1_pred = f(n)

        # Step 6: Inverse AGO to get final prediction
        x0_pred = x1_pred - x1[-1]

        return x0_pred

    def calculate_ma_signals(self, prices: list) -> tuple:
        """
        Calculate short-term and long-term moving averages and generate signals.
        
        Returns:
        - tuple: (short_ma, long_ma, ma_signal)
        where ma_signal is:
            1: bullish (short MA crosses above long MA)
            -1: bearish (short MA crosses below long MA)
            0: no signal
        """
        if len(prices) < self.long_ma_period:
            return None, None, 0

        # Calculate current MAs
        short_ma = np.mean(prices[-self.short_ma_period:])
        long_ma = np.mean(prices[-self.long_ma_period:])

        # Generate MA signal
        ma_signal = 0
        if self.prev_short_ma is not None and self.prev_long_ma is not None:
            # Bullish crossover
            if self.prev_short_ma <= self.prev_long_ma and short_ma > long_ma:
                ma_signal = 1
            # Bearish crossover
            elif self.prev_short_ma >= self.prev_long_ma and short_ma < long_ma:
                ma_signal = -1

        # Update previous MAs
        self.prev_short_ma = short_ma
        self.prev_long_ma = long_ma

        return short_ma, long_ma, ma_signal

    def calculate_risk(self) -> float:
        """
        Calculate risk based on historical price volatility.
        """
        if len(self.price_history) < 2:
            return 0.0
            
        returns = np.diff(self.price_history) / self.price_history[:-1]
        return np.std(returns)

    def calculate_objective(self, action: str, amount: float, current_price: float, 
                          predicted_price: float) -> float:
        """
        Calculate objective function value for a given action and amount.
        """
        # Calculate expected return
        if action == 'buy':
            expected_return = (predicted_price - current_price) / current_price * amount
        else:  # sell
            expected_return = (current_price - predicted_price) / current_price * amount

        # Calculate risk
        risk = self.calculate_risk() * amount

        # Calculate objective function value
        objective_value = self.mu * expected_return - (1 - self.mu) * risk

        return objective_value

    def find_best_buy_option(self, current_price: float, predicted_price: float, 
                            available_balance: float) -> dict:
        """
        Find the optimal buying amount when MA signal is bullish.
        """
        best_option = None
        max_objective = float('-inf')

        for amount in self.trading_options:
            # Check if we have enough balance to buy this amount
            if available_balance >= amount * current_price:
                objective_value = self.calculate_objective(
                    'buy', amount, current_price, predicted_price
                )
                if objective_value > max_objective:
                    max_objective = objective_value
                    best_option = {
                        'action': 'buy',
                        'amount': amount,
                        'objective_value': objective_value
                    }

        return best_option

    def find_best_sell_option(self, current_price: float, predicted_price: float, 
                             available_holdings: float) -> dict:
        """
        Find the optimal selling amount when MA signal is bearish.
        """
        best_option = None
        max_objective = float('-inf')

        for amount in self.trading_options:
            # Check if we have enough holdings to sell this amount
            if available_holdings >= amount: # 可能不用check
                objective_value = self.calculate_objective(
                    'sell', amount, current_price, predicted_price
                )
                if objective_value > max_objective:
                    max_objective = objective_value
                    best_option = {
                        'action': 'sell',
                        'amount': amount,
                        'objective_value': objective_value
                    }

        return best_option

    def execute_trade(self, trade_option: dict, current_price: float, timestamp: int):
        """
        Execute the selected trading option.
        """
        if trade_option['action'] == 'buy':
            self.buy(
                self.symbol,
                current_price,
                trade_option['amount'],
                timestamp,
                lambda: self.logger.info(f"Buy order completed: {trade_option}")
            )
            self.logger.info(f"Placed buy order: {trade_option}")
            
        elif trade_option['action'] == 'sell':
            self.sell(
                self.symbol,
                current_price,
                trade_option['amount'],
                timestamp,
                lambda: self.logger.info(f"Sell order completed: {trade_option}")
            )
            self.logger.info(f"Placed sell order: {trade_option}")

    def on_tick(self, snapshot: dict, cur_price: float, timestamp: int):
        """
        Process new market data and make trading decisions.
        """
        # Update price history
        self.price_history.append(cur_price)
        if len(self.price_history) > max(self.history_length, self.long_ma_period):
            self.price_history.pop(0)

        # Wait for enough price history
        if len(self.price_history) < max(self.history_length, self.long_ma_period):
            return

        # Get account information
        account = self.get_account()
        if not account or account.balance < self.min_balance:
            return

        # 1. First determine market direction using MA crossover
        _, _, ma_signal = self.calculate_ma_signals(self.price_history)
        
        # If no clear signal, hold position
        if ma_signal == 0:
            self.logger.info("No clear MA signal - holding position")
            return

        # 2. Get predicted price using GM(1,1)
        predicted_price = self.predict_gm11(self.price_history[-self.history_length:])

        # 3. Find best trading amount based on MA signal direction
        if ma_signal == 1:  # Bullish signal - optimize buying
            best_option = self.find_best_buy_option(
                cur_price,
                predicted_price,
                account.balance 
            )
        else:  # Bearish signal - optimize selling
            best_option = self.find_best_sell_option(
                cur_price,
                predicted_price,
                account.holdings.get(self.symbol, 0) 
            )

        # Execute the best trading option if found
        if best_option:
            self.execute_trade(best_option, cur_price, timestamp)

def main():
    """
    Main function to set up and run the trading strategy
    """
    # Initialize trading engine
    engine = Engine()
    engine.init_exchange()
    engine.exchange.add_account('test', 1000000)  # Initial balance of 1,000,000

    # Load historical data
    engine.load_data('../data/BTCUSDT2024-11-27.csv', 'BTCUSDT', opts={'head_num': 200000})

    # Define possible trading options (amounts)
    trading_options = [0.1, 0.2, 0.3, 0.4, 0.5]  # Example trading amounts

    # Initialize GMStrategy
    gm_strategy = GMStrategy(
        symbol='BTCUSDT',
        history_length=10,
        mu=0.6,  # 60% weight on return, 40% on risk
        trading_options=trading_options,
        min_balance=200,
        short_ma_period=5,   # 5-period short-term MA
        long_ma_period=20    # 20-period long-term MA
    )
    
    # Set up and start the strategy
    gm_strategy.set_engine(engine)
    engine.set_strategy(gm_strategy)
    engine.start()

if __name__ == '__main__':
    main()