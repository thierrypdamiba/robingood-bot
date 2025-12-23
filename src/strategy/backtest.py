import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Backtester:
    """
    Vectorized backtesting engine for trading strategies.
    """

    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000.0, trading_fee: float = 0.001):
        """
        Initializes the Backtester.

        Args:
            data (pd.DataFrame): Historical price data with 'close' column.
            initial_capital (float): Initial capital for backtesting.
            trading_fee (float): Trading fee as a fraction (e.g., 0.001 for 0.1%).
        """
        self.data = data
        self.initial_capital = initial_capital
        self.trading_fee = trading_fee
        self.cash = initial_capital
        self.positions = 0  # Number of shares held
        self.equity = initial_capital
        self.history = []
        self.logger = logging.getLogger(__name__)

        if 'close' not in self.data.columns:
            raise ValueError("Data must contain a 'close' column.")

    def run(self, signals: pd.Series) -> None:
        """
        Runs the backtest based on the given signals.

        Args:
            signals (pd.Series): A pandas Series with trade signals (-1, 0, or 1)
                                  indexed by the same datetime index as the data.
        """

        if not isinstance(signals, pd.Series):
            raise TypeError("Signals must be a pandas Series.")

        if not self.data.index.equals(signals.index):
            raise ValueError("Data and signals must have the same index.")

        self.signals = signals
        self._backtest()

    def _backtest(self) -> None:
        """
        Core backtesting logic.
        """
        self.logger.info("Starting backtest...")

        for i in range(1, len(self.data)):
            price = self.data['close'][i]
            signal = self.signals[i]
            prev_price = self.data['close'][i-1]

            if signal == 1:  # Buy signal
                # Calculate the maximum number of shares we can buy
                shares_to_buy = int(self.cash / (price * (1 + self.trading_fee)))

                if shares_to_buy > 0:
                    cost = shares_to_buy * price * (1 + self.trading_fee)
                    self.cash -= cost
                    self.positions += shares_to_buy
                    self.logger.debug(f"Buy {shares_to_buy} shares at {price}")
                else:
                    self.logger.debug("Not enough cash to buy.")

            elif signal == -1:  # Sell signal
                if self.positions > 0:
                    # Sell all current positions
                    revenue = self.positions * price * (1 - self.trading_fee)
                    self.cash += revenue
                    self.logger.debug(f"Sell {self.positions} shares at {price}")
                    self.positions = 0
                else:
                    self.logger.debug("No positions to sell.")

            # Update equity
            self.equity = self.cash + self.positions * price

            # Store the history
            self.history.append({
                'timestamp': self.data.index[i],
                'price': price,
                'signal': signal,
                'cash': self.cash,
                'positions': self.positions,
                'equity': self.equity
            })

        self.logger.info("Backtest complete.")

    def get_results(self) -> pd.DataFrame:
        """
        Returns the backtesting results as a Pandas DataFrame.
        """
        if not self.history:
            self.logger.warning("No backtesting history found.  Run the backtest first.")
            return pd.DataFrame()

        results = pd.DataFrame(self.history)
        results = results.set_index('timestamp')
        return results

    def calculate_performance_metrics(self) -> Dict[str, float]:
        """
        Calculates and returns performance metrics.

        Returns:
            Dict[str, float]: A dictionary containing performance metrics.
        """
        if not self.history:
            self.logger.warning("No backtesting history found.  Run the backtest first.")
            return {}

        results = self.get_results()
        results['returns'] = results['equity'].pct_change()
        results = results.dropna()

        total_return = (results['equity'].iloc[-1] / self.initial_capital) - 1
        annualized_return = (1 + total_return)**(252/len(results)) - 1 # Assuming 252 trading days
        sharpe_ratio = np.sqrt(252) * (results['returns'].mean() / results['returns'].std()) if results['returns'].std() > 0 else np.nan
        max_drawdown = self._calculate_max_drawdown(results['equity'])

        metrics = {
            'initial_capital': self.initial_capital,
            'final_equity': results['equity'].iloc[-1],
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }

        return metrics

    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        """
        Calculates the maximum drawdown.

        Args:
            equity (pd.Series): A pandas Series representing the equity curve.

        Returns:
            float: The maximum drawdown.
        """
        peak = equity.iloc[0]
        max_drawdown = 0.0
        for value in equity:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        return max_drawdown