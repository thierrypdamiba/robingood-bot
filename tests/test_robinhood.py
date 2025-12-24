"""Tests for Robinhood client."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.robinhood.client import RobinhoodClient


class TestRobinhoodClient:
    """Test cases for RobinhoodClient."""
    
    def test_client_init(self):
        """Test client initialization."""
        client = RobinhoodClient()
        assert client is not None
        
    def test_get_account(self):
        """Test getting account info."""
        client = RobinhoodClient()
        account = client.get_account()
        assert account is not None
        assert "id" in account
        
    def test_get_quote(self):
        """Test getting a quote."""
        client = RobinhoodClient()
        quote = client.get_quote("BTC")
        assert quote is not None
        assert quote["symbol"] == "BTC"
        
    def test_place_order_invalid_side(self):
        """Test that invalid side raises error."""
        client = RobinhoodClient()
        with pytest.raises(ValueError):
            client.place_order("BTC", "invalid", 1.0)
            
    def test_place_order_buy(self):
        """Test placing a buy order."""
        client = RobinhoodClient()
        order = client.place_order("BTC", "buy", 0.01)
        assert order is not None
        assert order["side"] == "buy"
        
    def test_get_holdings(self):
        """Test getting holdings."""
        client = RobinhoodClient()
        holdings = client.get_holdings()
        assert isinstance(holdings, list)
