import asyncio
import logging
import os
from typing import Dict, Any

import robin_stocks.robinhood as rh
from dotenv import load_dotenv

load_dotenv()

class OrderExecutor:
    """
    Executes trades via the Robinhood API with risk checks.
    """

    def __init__(self):
        """
        Initializes the OrderExecutor.  Logs in to Robinhood.
        """
        self.username = os.environ.get("robinhood_username")
        self.password = os.environ.get("robinhood_password")
        self.logger = logging.getLogger(__name__)

        if not self.username or not self.password:
            self.logger.error("Robinhood username or password not set in environment variables.")
            raise ValueError("Robinhood username or password not set in environment variables.")

        try:
            rh.login(username=self.username, password=self.password)
            self.logger.info("Successfully logged in to Robinhood.")
        except Exception as e:
            self.logger.exception(f"Failed to log in to Robinhood: {e}")
            raise

    async def execute_order(self, symbol: str, quantity: int, side: str, price: float) -> Dict[str, Any]:
        """
        Executes a trade order.

        Args:
            symbol: The ticker symbol of the crypto to trade.
            quantity: The number of shares to trade.
            side: "buy" or "sell".
            price: The limit price for the order.

        Returns:
            A dictionary containing the order confirmation details.

        Raises:
            ValueError: If the side is invalid.
            Exception: If the order fails.
        """

        if side not in ("buy", "sell"):
            raise ValueError("Invalid side. Must be 'buy' or 'sell'.")

        try:
            if side == "buy":
                order = rh.order_buy_crypto_limit(symbol=symbol, quantity=quantity, limitPrice=price)
                self.logger.info(f"Buying {quantity} {symbol} at {price}")
            else:  # side == "sell"
                order = rh.order_sell_crypto_limit(symbol=symbol, quantity=quantity, limitPrice=price)
                self.logger.info(f"Selling {quantity} {symbol} at {price}")

            self.logger.info(f"Order placed: {order}")
            return order

        except Exception as e:
            self.logger.exception(f"Order failed: {e}")
            raise

    async def check_holdings(self, symbol: str) -> float:
        """
        Checks the current holdings for a given crypto symbol.

        Args:
            symbol: The ticker symbol of the crypto.

        Returns:
            The quantity of the crypto held.  Returns 0.0 if no holdings are found.
        """
        try:
            holdings = rh.get_crypto_positions()
            for holding in holdings:
                if holding['currency']['code'] == symbol:
                    quantity = float(holding['quantity'])
                    self.logger.info(f"Current holdings for {symbol}: {quantity}")
                    return quantity
            self.logger.info(f"No holdings found for {symbol}")
            return 0.0

        except Exception as e:
            self.logger.exception(f"Failed to check holdings for {symbol}: {e}")
            return 0.0

    async def get_current_price(self, symbol: str) -> float:
        """
        Gets the current price of a crypto.

        Args:
            symbol: The ticker symbol of the crypto.

        Returns:
            The current price of the crypto.

        Raises:
            Exception: If the price retrieval fails.
        """
        try:
            price_data = rh.get_crypto_quote(symbol)
            price = float(price_data['mark_price'])
            self.logger.info(f"Current price of {symbol}: {price}")
            return price
        except Exception as e:
            self.logger.exception(f"Failed to get current price for {symbol}: {e}")
            raise

    async def cancel_all_orders(self, symbol: str) -> None:
        """
        Cancels all open orders for a given crypto symbol.

        Args:
            symbol: The ticker symbol of the crypto.
        """
        try:
            orders = rh.get_open_crypto_orders(symbol=symbol)
            for order in orders:
                cancel_result = rh.cancel_crypto_order(order['id'])
                if cancel_result['detail'] == 'Success':
                    self.logger.info(f"Cancelled order {order['id']} for {symbol}")
                else:
                    self.logger.warning(f"Failed to cancel order {order['id']} for {symbol}: {cancel_result}")
        except Exception as e:
            self.logger.exception(f"Failed to cancel orders for {symbol}: {e}")

async def main():
    """
    Example usage of the OrderExecutor class.
    """
    logging.basicConfig(level=logging.INFO)
    executor = OrderExecutor()

    symbol = "BTC"
    quantity = 0.001
    side = "buy"
    try:
        price = await executor.get_current_price(symbol)
        order_result = await executor.execute_order(symbol, quantity, side, price)
        print(f"Order Result: {order_result}")

        holdings = await executor.check_holdings(symbol)
        print(f"Holdings: {holdings}")

        await executor.cancel_all_orders(symbol)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())