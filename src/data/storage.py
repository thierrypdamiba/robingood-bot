import sqlite3
import logging
from typing import List, Tuple, Optional
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PriceStorage:
    """
    A class for storing historical price data in a SQLite database.
    """

    def __init__(self, db_path: str = 'crypto_prices.db'):
        """
        Initializes the PriceStorage with a database connection.

        Args:
            db_path: The path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = None  # Initialize connection to None
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self._create_table()
            logging.info(f"Connected to SQLite database: {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Error connecting to SQLite database: {e}")
            # Consider raising the exception or exiting if the database connection is critical
            raise

    def _create_table(self) -> None:
        """
        Creates the price data table if it doesn't exist.
        """
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    timestamp INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL
                )
            """)
            self.conn.commit()
            logging.info("Price table created (if it didn't exist).")
        except sqlite3.Error as e:
            logging.error(f"Error creating table: {e}")
            # Consider raising the exception or exiting if table creation is critical
            raise

    def store_price(self, timestamp: int, symbol: str, price: float) -> None:
        """
        Stores a single price data point in the database.

        Args:
            timestamp: The timestamp of the price data (Unix timestamp).
            symbol: The trading symbol (e.g., 'BTCUSD').
            price: The price of the asset.
        """
        try:
            self.cursor.execute("""
                INSERT INTO prices (timestamp, symbol, price) VALUES (?, ?, ?)
            """, (timestamp, symbol, price))
            self.conn.commit()
            logging.debug(f"Stored price: {timestamp}, {symbol}, {price}")
        except sqlite3.Error as e:
            logging.error(f"Error storing price: {e}")

    def store_prices(self, prices: List[Tuple[int, str, float]]) -> None:
        """
        Stores multiple price data points in the database using batch insert.

        Args:
            prices: A list of tuples, where each tuple contains (timestamp, symbol, price).
        """
        try:
            self.cursor.executemany("""
                INSERT INTO prices (timestamp, symbol, price) VALUES (?, ?, ?)
            """, prices)
            self.conn.commit()
            logging.debug(f"Stored {len(prices)} prices.")
        except sqlite3.Error as e:
            logging.error(f"Error storing prices: {e}")

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Retrieves the latest price for a given symbol from the database.

        Args:
            symbol: The trading symbol.

        Returns:
            The latest price, or None if no price is found.
        """
        try:
            self.cursor.execute("""
                SELECT price FROM prices WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1
            """, (symbol,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
        except sqlite3.Error as e:
            logging.error(f"Error retrieving latest price: {e}")
            return None

    def get_prices_in_range(self, symbol: str, start_timestamp: int, end_timestamp: int) -> List[Tuple[int, float]]:
        """
        Retrieves prices for a given symbol within a specified timestamp range.

        Args:
            symbol: The trading symbol.
            start_timestamp: The starting timestamp (inclusive).
            end_timestamp: The ending timestamp (inclusive).

        Returns:
            A list of tuples, where each tuple contains (timestamp, price).
        """
        try:
            self.cursor.execute("""
                SELECT timestamp, price FROM prices 
                WHERE symbol = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (symbol, start_timestamp, end_timestamp))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error retrieving prices in range: {e}")
            return []

    def close(self) -> None:
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")

    def __enter__(self):
        """
        Allows the PriceStorage to be used as a context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Closes the database connection when exiting the context.
        """
        self.close()

if __name__ == '__main__':
    # Example usage
    try:
        with PriceStorage('test_prices.db') as storage:
            # Store some sample data
            storage.store_price(1678886400, 'BTCUSD', 27000.0)
            storage.store_prices([
                (1678886460, 'BTCUSD', 27050.0),
                (1678886520, 'BTCUSD', 27100.0)
            ])

            # Retrieve the latest price
            latest_price = storage.get_latest_price('BTCUSD')
            print(f"Latest BTCUSD price: {latest_price}")

            # Retrieve prices in a range
            prices_in_range = storage.get_prices_in_range('BTCUSD', 1678886400, 1678886520)
            print(f"Prices in range: {prices_in_range}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")