import logging
import os
from typing import Optional

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RiskManager:
    """
    Manages risk by limiting position sizes, protecting against excessive drawdowns,
    and providing a kill switch to halt trading.
    """

    def __init__(self,
                 max_position_size: float = 0.1,  # 10% of account balance
                 max_drawdown: float = 0.05,  # 5% drawdown
                 initial_capital: float = 10000.0):
        """
        Initializes the RiskManager.

        Args:
            max_position_size (float): Maximum percentage of account balance to allocate to a single position.
            max_drawdown (float): Maximum percentage drawdown allowed before triggering the kill switch.
            initial_capital (float): Initial capital in the account.
        """
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.peak_balance = initial_capital
        self.is_kill_switch_active = False
        self.logger = logging.getLogger(__name__)

    def update_balance(self, current_balance: float) -> None:
        """
        Updates the current balance and peak balance.

        Args:
            current_balance (float): The current account balance.
        """
        self.current_balance = current_balance
        self.peak_balance = max(self.peak_balance, current_balance)

    def check_drawdown(self) -> bool:
        """
        Checks if the maximum drawdown has been exceeded.

        Returns:
            bool: True if the drawdown exceeds the limit, False otherwise.
        """
        drawdown = (self.peak_balance - self.current_balance) / self.initial_capital
        if drawdown > self.max_drawdown:
            self.logger.warning(f"Maximum drawdown exceeded: {drawdown:.2f} > {self.max_drawdown:.2f}")
            self.is_kill_switch_active = True
            return True
        return False

    def check_position_size(self, position_size: float) -> bool:
        """
        Checks if the requested position size exceeds the maximum allowed.

        Args:
            position_size (float): The requested position size (in quote currency).

        Returns:
            bool: True if the position size is within limits, False otherwise.
        """
        max_allowed_position = self.current_balance * self.max_position_size
        if position_size > max_allowed_position:
            self.logger.warning(
                f"Position size {position_size:.2f} exceeds maximum allowed: {max_allowed_position:.2f}")
            return False
        return True

    def is_trading_allowed(self) -> bool:
        """
        Checks if trading is allowed based on the kill switch status.

        Returns:
            bool: True if trading is allowed, False otherwise.
        """
        if self.is_kill_switch_active:
            self.logger.warning("Trading is disabled due to kill switch activation.")
            return False
        return True

    def activate_kill_switch(self) -> None:
        """
        Manually activates the kill switch.
        """
        self.is_kill_switch_active = True
        self.logger.warning("Kill switch manually activated.")

    def reset(self) -> None:
        """
        Resets the risk manager to its initial state.  Useful for backtesting.
        """
        self.current_balance = self.initial_capital
        self.peak_balance = self.initial_capital
        self.is_kill_switch_active = False
        self.logger.info("Risk manager reset to initial state.")


if __name__ == '__main__':
    # Example usage
    risk_manager = RiskManager(max_position_size=0.1, max_drawdown=0.05, initial_capital=10000)

    # Simulate a winning trade
    risk_manager.update_balance(11000)
    print(f"Current balance: {risk_manager.current_balance}, Peak balance: {risk_manager.peak_balance}")

    # Simulate a losing trade that triggers the drawdown
    risk_manager.update_balance(9000)
    if risk_manager.check_drawdown():
        print("Trading stopped due to drawdown.")

    # Check if trading is allowed
    if not risk_manager.is_trading_allowed():
        print("Trading is not allowed.")

    # Check position size
    position_size = 1500  # Example position size
    if risk_manager.check_position_size(position_size):
        print(f"Position size {position_size} is within limits.")
    else:
        print(f"Position size {position_size} exceeds limits.")

    # Manually activate kill switch
    # risk_manager.activate_kill_switch()
    # if not risk_manager.is_trading_allowed():
    #     print("Trading is not allowed.")

    risk_manager.reset()
    print(f"Current balance after reset: {risk_manager.current_balance}, Peak balance: {risk_manager.peak_balance}")
    print(f"Kill switch active after reset: {risk_manager.is_kill_switch_active}")