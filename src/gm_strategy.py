import numpy as np

class GMPositionSizer:
    def __init__(self, symbol: str, history_length: int, mu: float, trading_options: list, min_balance: float):
        """
        Initialize the Position Sizer using GM(1,1) model.
        
        Parameters:
        - symbol: Trading symbol
        - history_length: Length of price history for GM(1,1)
        - mu: Weight coefficient for objective function (0 < mu < 1)
        - trading_options: List of possible trading amounts
        - min_balance: Minimum balance required
        """
        self.symbol = symbol
        self.history_length = history_length
        self.mu = mu
        self.trading_options = trading_options
        self.min_balance = min_balance
        self.price_history = []

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

    def calculate_risk(self) -> float:
        """Calculate risk based on historical price volatility."""
        if len(self.price_history) < 2:
            return 0.0
        returns = np.diff(self.price_history) / self.price_history[:-1]
        return np.std(returns)

    def calculate_objective(self, action: str, amount: float, current_price: float, 
                          predicted_price: float) -> float:
        """Calculate objective function value for a given action and amount."""
        # Expected return calculation
        if action == 'buy':
            expected_return = (predicted_price - current_price) / current_price * amount
        else:  # sell
            expected_return = (current_price - predicted_price) / current_price * amount

        # Risk calculation
        risk = self.calculate_risk() * amount
        
        # Objective function
        return self.mu * expected_return - (1 - self.mu) * risk

    def get_optimal_position_size(self, signal: str, current_price: float, 
                                available_balance: float, available_holdings: float) -> dict:
        """
        Determine optimal position size based on the given signal.
        
        Parameters:
        - signal: "buy" or "sell" signal from the strategy
        - current_price: Current market price
        - available_balance: Available balance for buying
        - available_holdings: Available holdings for selling
        """
        if len(self.price_history) < self.history_length:
            return None

        # Update price history
        self.price_history.append(current_price)
        if len(self.price_history) > self.history_length:
            self.price_history.pop(0)

        # Get price prediction
        predicted_price = self.predict_gm11(self.price_history)

        # Find optimal position size based on signal
        if signal == "buy":
            best_option = self._find_best_buy_option(current_price, predicted_price, available_balance)
        elif signal == "sell":
            best_option = self._find_best_sell_option(current_price, predicted_price, available_holdings)
        else:
            return None

        return best_option

    def _find_best_buy_option(self, current_price: float, predicted_price: float, 
                           available_balance: float) -> dict:
        """Find the optimal buying amount."""
        best_option = None
        max_objective = float('-inf')

        for amount in self.trading_options:
            if available_balance >= amount * current_price:
                objective_value = self.calculate_objective('buy', amount, current_price, predicted_price)
                if objective_value > max_objective:
                    max_objective = objective_value
                    best_option = {
                        'action': 'buy',
                        'amount': amount,
                        'objective_value': objective_value
                    }

        return best_option

    def _find_best_sell_option(self, current_price: float, predicted_price: float, 
                            available_holdings: float) -> dict:
        """Find the optimal selling amount."""
        best_option = None
        max_objective = float('-inf')

        for amount in self.trading_options:
            if available_holdings >= amount:
                objective_value = self.calculate_objective('sell', amount, current_price, predicted_price)
                if objective_value > max_objective:
                    max_objective = objective_value
                    best_option = {
                        'action': 'sell',
                        'amount': amount,
                        'objective_value': objective_value
                    }

        return best_option