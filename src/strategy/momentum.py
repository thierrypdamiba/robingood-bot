import logging
import numpy as np
import pandas as pd
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MomentumStrategy:
    """
    Implements a volatility-adjusted momentum strategy with mean reversion entry.
    """

    def __init__(self, lookback_window: int = 20, volatility_window: int = 20, mean_reversion_window: int = 5,
                 momentum_threshold: float = 0.005, mean_reversion_threshold: float = 0.005):
        """
        Initializes the MomentumStrategy.

        Args:
            lookback_window: Lookback period for momentum calculation.
            volatility_window: Lookback period for volatility calculation.
            mean_reversion_window: Lookback period for mean reversion calculation.
            momentum_threshold: Threshold for momentum signal.
            mean_reversion_threshold: Threshold for mean reversion signal.
        """
        self.lookback_window = lookback_window
        self.volatility_window = volatility_window
        self.mean_reversion_window = mean_reversion_window
        self.momentum_threshold = momentum_threshold
        self.mean_reversion_threshold = mean_reversion_threshold
        self.logger = logging.getLogger(__name__)

    def calculate_momentum(self, prices: pd.Series) -> Optional[float]:
        """
        Calculates the momentum of the price series.

        Args:
            prices: Pandas Series of prices.

        Returns:
            Momentum value, or None if insufficient data.
        """
        if len(prices) < self.lookback_window:
            self.logger.warning(f"Insufficient data for momentum calculation.  Required: {self.lookback_window}, Available: {len(prices)}")
            return None

        try:
            returns = np.log(prices).diff(self.lookback_window).dropna()
            momentum = returns.iloc[-1]
            return momentum
        except Exception as e:
            self.logger.error(f"Error calculating momentum: {e}")
            return None

    def calculate_volatility(self, prices: pd.Series) -> Optional[float]:
        """
        Calculates the volatility of the price series.

        Args:
            prices: Pandas Series of prices.

        Returns:
            Volatility value, or None if insufficient data.
        """
        if len(prices) < self.volatility_window:
            self.logger.warning(f"Insufficient data for volatility calculation. Required: {self.volatility_window}, Available: {len(prices)}")
            return None

        try:
            returns = np.log(prices).diff().dropna()
            volatility = returns[-self.volatility_window:].std()
            return volatility
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {e}")
            return None

    def calculate_mean_reversion(self, prices: pd.Series) -> Optional[float]:
        """
        Calculates the mean reversion signal.

        Args:
            prices: Pandas Series of prices.

        Returns:
            Mean reversion signal, or None if insufficient data.
        """
        if len(prices) < self.mean_reversion_window:
            self.logger.warning(f"Insufficient data for mean reversion calculation. Required: {self.mean_reversion_window}, Available: {len(prices)}")
            return None

        try:
            # Calculate the moving average
            moving_average = prices.rolling(window=self.mean_reversion_window).mean().iloc[-1]

            # Calculate the deviation from the moving average
            deviation = prices.iloc[-1] - moving_average

            return deviation
        except Exception as e:
            self.logger.error(f"Error calculating mean reversion: {e}")
            return None

    def generate_signal(self, prices: pd.Series) -> int:
        """
        Generates a trading signal based on momentum and mean reversion.

        Args:
            prices: Pandas Series of prices.

        Returns:
            1 for buy, -1 for sell, 0 for hold.
        """
        momentum = self.calculate_momentum(prices)
        volatility = self.calculate_volatility(prices)
        mean_reversion = self.calculate_mean_reversion(prices)

        if momentum is None or volatility is None or mean_reversion is None:
            return 0

        # Volatility-adjusted momentum
        adjusted_momentum = momentum / volatility if volatility > 0 else 0

        if adjusted_momentum > self.momentum_threshold and mean_reversion < -self.mean_reversion_threshold:
            self.logger.info(f"Buy signal: Adjusted Momentum = {adjusted_momentum}, Mean Reversion = {mean_reversion}")
            return 1  # Buy signal
        elif adjusted_momentum < -self.momentum_threshold and mean_reversion > self.mean_reversion_threshold:
            self.logger.info(f"Sell signal: Adjusted Momentum = {adjusted_momentum}, Mean Reversion = {mean_reversion}")
            return -1  # Sell signal
        else:
            return 0  # Hold signal

if __name__ == '__main__':
    # Example usage
    prices = pd.Series(np.random.randn(100) + 100)  # Simulate price data
    strategy = MomentumStrategy()
    signal = strategy.generate_signal(prices)
    print(f"Generated signal: {signal}")