import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.database.models import Trade
from src.robinhood.robinhood_client import RobinhoodClient  # Assuming this exists
from src.trading_logic.signals import TradingSignal  # Assuming this exists
from src.database.database import get_db, SessionLocal
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Robinhood client (ideally, this would be dependency injected)
robinhood_username = os.environ.get("ROBINHOOD_USERNAME")
robinhood_password = os.environ.get("ROBINHOOD_PASSWORD")

if not robinhood_username or not robinhood_password:
    logger.error("Robinhood credentials not found in environment variables.")
    robinhood_client = None  # Or raise an exception here if it's critical
else:
    try:
        robinhood_client = RobinhoodClient(username=robinhood_username, password=robinhood_password)
        robinhood_client.login()
    except Exception as e:
        logger.error(f"Failed to initialize Robinhood client: {e}")
        robinhood_client = None


@router.get("/status", response_model=Dict[str, Any], summary="Get bot status")
async def get_status() -> Dict[str, Any]:
    """
    Returns the current status of the trading bot.
    """
    # Placeholder - replace with actual bot status logic
    status_data = {
        "status": "running",
        "timestamp": "2024-10-27T12:00:00Z",
        "message": "Bot is active and monitoring market."
    }
    return status_data


@router.get("/portfolio", response_model=Dict[str, Any], summary="Get portfolio information")
async def get_portfolio() -> Dict[str, Any]:
    """
    Returns the current portfolio information from Robinhood.
    """
    if robinhood_client is None:
        raise HTTPException(status_code=500, detail="Robinhood client not initialized.")

    try:
        portfolio = robinhood_client.get_portfolio()
        return portfolio
    except Exception as e:
        logger.exception("Error fetching portfolio from Robinhood:")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve portfolio: {e}")


@router.get("/trades", response_model=List[Dict[str, Any]], summary="Get recent trades")
async def get_trades(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns a list of recent trades from the database.
    """
    try:
        trades = db.query(Trade).order_by(Trade.timestamp.desc()).limit(100).all()  # Fetch last 100 trades
        # Convert SQLAlchemy objects to dictionaries for JSON serialization
        trade_list = [trade.__dict__ for trade in trades]
        # Remove the SQLAlchemy internal state (_sa_instance_state) from each trade
        for trade in trade_list:
            trade.pop('_sa_instance_state', None)
        return trade_list
    except Exception as e:
        logger.exception("Error fetching trades from database:")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trades: {e}")


@router.post("/signals", summary="Receive trading signals")
async def receive_signal(signal: TradingSignal, db: Session = Depends(get_db)) -> JSONResponse:
    """
    Receives a trading signal and executes the trade.
    """
    if robinhood_client is None:
        raise HTTPException(status_code=500, detail="Robinhood client not initialized.")

    try:
        # Execute the trade based on the signal
        if signal.action == "buy":
            order_result = robinhood_client.place_order(
                symbol=signal.symbol,
                quantity=signal.quantity,
                side="buy",
                order_type="market"  # Or limit, etc.
            )
        elif signal.action == "sell":
            order_result = robinhood_client.place_order(
                symbol=signal.symbol,
                quantity=signal.quantity,
                side="sell",
                order_type="market"  # Or limit, etc.
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid signal action.")

        # Log the trade in the database
        new_trade = Trade(
            symbol=signal.symbol,
            action=signal.action,
            quantity=signal.quantity,
            price=order_result.get("average_price", 0.0),  # Assuming Robinhood returns this
            timestamp=order_result.get("timestamp")  # Assuming Robinhood returns this
        )
        db.add(new_trade)
        db.commit()
        db.refresh(new_trade)

        return JSONResponse(content={"message": "Trade executed successfully.", "order_result": order_result})

    except Exception as e:
        logger.exception(f"Error executing trade for signal: {signal}")
        db.rollback()  # Rollback changes in case of error
        raise HTTPException(status_code=500, detail=f"Failed to execute trade: {e}")