import os
from typing import Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """
    Configuration settings for the trading bot.
    """

    robinhood_username: str
    robinhood_password: str
    robinhood_api_key: str
    crypto_symbol: str = "BTCUSD"
    trading_amount: float = 10.0
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    database_url: str = "sqlite:///./trading_bot.db"  # Default SQLite URL
    log_level: str = "INFO"  # Default log level

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("trading_amount")
    def trading_amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Trading amount must be positive")
        return v

    @validator("log_level")
    def log_level_must_be_valid(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()


settings = Settings()

if __name__ == "__main__":
    # Example usage:
    print(f"Crypto Symbol: {settings.crypto_symbol}")
    print(f"Trading Amount: {settings.trading_amount}")
    print(f"Database URL: {settings.database_url}")
    print(f"Log Level: {settings.log_level}")