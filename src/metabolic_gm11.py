import numpy as np

class MetabolicGM11:
    def __init__(self, window_size=4):
        self.window_size = window_size
        self.price_window = []
        self.a = None  # Development coefficient
        self.b = None  # Grey input
        
    def fit(self, data):
        """Initial fit of the model with first window of data"""
        if len(data) >= self.window_size:
            self.price_window = list(data[-self.window_size:])
            self._update_parameters()
            
    def _create_accumulated_sequence(self, data):
        """Create accumulated generating operation (AGO) sequence"""
        return np.cumsum(data)
        
    def _create_background_values(self, ago_sequence):
        """Create background values (Z) from AGO sequence"""
        z = np.zeros(len(ago_sequence) - 1)
        for i in range(len(z)):
            z[i] = -0.5 * (ago_sequence[i] + ago_sequence[i + 1])
        return z
        
    def _update_parameters(self):
        """Update model parameters a and b"""
        # Create AGO sequence
        ago_sequence = self._create_accumulated_sequence(self.price_window)
        
        # Create background values
        z = self._create_background_values(ago_sequence)
        
        # Create B matrix and Y vector
        B = np.vstack([z, np.ones_like(z)]).T
        Y = np.array(self.price_window[1:])
        
        # Calculate parameters using least squares
        try:
            params = np.linalg.inv(B.T @ B) @ B.T @ Y
            self.a, self.b = params[0], params[1]
        except np.linalg.LinAlgError:
            print("Matrix inverse failed. Parameters unchanged.")
            
    def predict_next(self):
        """Predict the next value"""
        if self.a is None or self.b is None:
            return None
            
        k = len(self.price_window) + 1
        x0 = self.price_window[0]
        
        # Calculate x1(k+1)
        x1_next = (x0 - self.b/self.a) * np.exp(-self.a * k) + self.b/self.a
        
        # Calculate x1(k)
        x1_current = (x0 - self.b/self.a) * np.exp(-self.a * (k-1)) + self.b/self.a
        
        # Calculate x0(k+1) = x1(k+1) - x1(k)
        x0_next = x1_next - x1_current
        
        return x0_next
        
    def update(self, new_price):
        """Update model with new price data"""
        # Add new price and remove oldest if window is full
        self.price_window.append(new_price)
        if len(self.price_window) > self.window_size:
            self.price_window.pop(0)
            
        # Update model parameters
        self._update_parameters()
        
        return self.predict_next()

# Example usage
def simulate_market_feed():
    """Simulate real-time market price feed"""
    # Initial data
    initial_prices = [100, 105, 102, 108, 112, 115]
    # New incoming prices
    new_prices = [118, 122, 125, 121]
    
    # Initialize model
    model = MetabolicGM11(window_size=4)
    model.fit(initial_prices)
    
    print("Initial window:", model.price_window)
    print("Initial prediction:", model.predict_next())
    
    # Simulate receiving new prices
    print("\nProcessing new prices:")
    for price in new_prices:
        prediction = model.update(price)
        print(f"New price: {price}")
        print(f"Current window: {model.price_window}")
        print(f"Next prediction: {prediction:.2f}")
        print(f"Parameters - a: {model.a:.4f}, b: {model.b:.4f}")
        print("---")

# Run simulation
if __name__ == "__main__":
    simulate_market_feed()