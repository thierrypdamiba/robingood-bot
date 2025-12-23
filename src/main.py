import asyncio
import logging
import os
from typing import Dict, Any

import fastapi
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.robinhood_client import RobinhoodClient
from src.strategy import MomentumStrategy
from src.database import Database

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables (replace with your preferred method)
ROBINHOOD_USERNAME = os.environ.get("ROBINHOOD_USERNAME")
ROBINHOOD_PASSWORD = os.environ.get("ROBINHOOD_PASSWORD")
DATABASE_URL = os.environ.get("DATABASE_URL")

if not all([ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD, DATABASE_URL]):
    raise ValueError("Missing environment variables. Ensure ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD, and DATABASE_URL are set.")


# Initialize components
app = FastAPI()
robinhood_client = RobinhoodClient(username=ROBINHOOD_USERNAME, password=ROBINHOOD_PASSWORD)
strategy = MomentumStrategy()
database = Database(database_url=DATABASE_URL)


async def trading_loop():
    """
    Main trading loop that runs continuously.
    """
    try:
        await database.connect()
        await robinhood_client.login()

        while True:
            try:
                # 1. Fetch market data
                # Example: Fetch top 5 crypto currencies
                top_crypto = ["BTC", "ETH", "LTC", "DOGE", "SHIB"] # Example list, replace with dynamic fetching if needed
                market_data: Dict[str, Any] = await robinhood_client.get_crypto_quote(top_crypto)

                # 2. Analyze market data using the strategy
                signals: Dict[str, str] = strategy.generate_signals(market_data)  # {"BTC": "BUY", "ETH": "SELL", ...}

                # 3. Execute trades based on signals
                for ticker, signal in signals.items():
                    if signal == "BUY":
                        # Example: Buy $10 worth of the crypto
                        await robinhood_client.place_order(ticker, "buy", 10)
                        logger.info(f"BUY order placed for {ticker}")
                    elif signal == "SELL":
                        # Example: Sell all holdings of the crypto
                        # Need to fetch current holdings first
                        try:
                            holdings = await robinhood_client.get_crypto_holdings(ticker)
                            if holdings and holdings["quantity"] > 0:
                                await robinhood_client.place_order(ticker, "sell", holdings["quantity"])
                                logger.info(f"SELL order placed for {ticker}")
                            else:
                                logger.info(f"No holdings to sell for {ticker}")

                        except Exception as e:
                            logger.error(f"Error fetching holdings or placing sell order for {ticker}: {e}")


                # 4. Log trades and performance (store in database)
                await database.log_trades(signals)  # Store signals, actual trades are tracked by Robinhood

                # 5. Wait before the next iteration
                await asyncio.sleep(60)  # Check every 60 seconds

            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60) # Wait and retry

    except Exception as e:
        logger.exception(f"Critical error in main loop: {e}")
    finally:
        await robinhood_client.logout()
        await database.disconnect()
        logger.info("Trading loop finished.")


@app.on_event("startup")
async def startup_event():
    """
    Startup event to initialize the trading loop.
    """
    asyncio.create_task(trading_loop())
    logger.info("Trading bot started.")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)