import os
import unittest
from unittest.mock import patch, MagicMock
import pytest
from src.robinhood.client import RobinhoodClient
from dotenv import load_dotenv

load_dotenv()

class TestRobinhoodClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize RobinhoodClient with dummy values.  Real credentials should never be stored in tests.
        cls.rh_client = RobinhoodClient(
            username=os.environ.get("ROBINHOOD_USERNAME", "test_user"),
            password=os.environ.get("ROBINHOOD_PASSWORD", "test_password"),
            api_key=os.environ.get("ROBINHOOD_API_KEY", "test_api_key")
        )

    @patch('robinhood_client.RobinhoodClient.rh.login')
    def test_login_success(self, mock_login):
        mock_login.return_value = True
        self.rh_client.login()
        mock_login.assert_called_once()
        self.assertTrue(self.rh_client.is_logged_in)

    @patch('robinhood_client.RobinhoodClient.rh.login')
    def test_login_failure(self, mock_login):
        mock_login.side_effect = Exception("Login failed")
        with self.assertRaises(Exception):
            self.rh_client.login()
        self.assertFalse(self.rh_client.is_logged_in)

    @patch('robinhood_client.RobinhoodClient.rh.get_crypto_quote')
    def test_get_crypto_quote_success(self, mock_get_crypto_quote):
        mock_get_crypto_quote.return_value = {'mark_price': '100.00'}
        price = self.rh_client.get_crypto_quote('BTC')
        self.assertEqual(float(price), 100.00)
        mock_get_crypto_quote.assert_called_once_with('BTC')

    @patch('robinhood_client.RobinhoodClient.rh.get_crypto_quote')
    def test_get_crypto_quote_failure(self, mock_get_crypto_quote):
        mock_get_crypto_quote.side_effect = Exception("Failed to get quote")
        with self.assertRaises(Exception):
            self.rh_client.get_crypto_quote('BTC')

    @patch('robinhood_client.RobinhoodClient.rh.order_buy_crypto_by_price')
    def test_buy_crypto_success(self, mock_order_buy_crypto_by_price):
        mock_order_buy_crypto_by_price.return_value = {'id': 'test_order_id'}
        order_result = self.rh_client.buy_crypto('BTC', 100)
        self.assertEqual(order_result, {'id': 'test_order_id'})
        mock_order_buy_crypto_by_price.assert_called_once_with('BTC', 100)

    @patch('robinhood_client.RobinhoodClient.rh.order_buy_crypto_by_price')
    def test_buy_crypto_failure(self, mock_order_buy_crypto_by_price):
        mock_order_buy_crypto_by_price.side_effect = Exception("Failed to buy")
        with self.assertRaises(Exception):
            self.rh_client.buy_crypto('BTC', 100)

    @patch('robinhood_client.RobinhoodClient.rh.order_sell_crypto_by_quantity')
    def test_sell_crypto_success(self, mock_order_sell_crypto_by_quantity):
        mock_order_sell_crypto_by_quantity.return_value = {'id': 'test_order_id'}
        order_result = self.rh_client.sell_crypto('BTC', 1)
        self.assertEqual(order_result, {'id': 'test_order_id'})
        mock_order_sell_crypto_by_quantity.assert_called_once_with('BTC', 1)

    @patch('robinhood_client.RobinhoodClient.rh.order_sell_crypto_by_quantity')
    def test_sell_crypto_failure(self, mock_order_sell_crypto_by_quantity):
        mock_order_sell_crypto_by_quantity.side_effect = Exception("Failed to sell")
        with self.assertRaises(Exception):
            self.rh_client.sell_crypto('BTC', 1)

    @patch('robinhood_client.RobinhoodClient.rh.get_crypto_positions')
    def test_get_crypto_positions_success(self, mock_get_crypto_positions):
        mock_get_crypto_positions.return_value = [{'currency': {'code': 'BTC'}, 'quantity': '1.0'}]
        positions = self.rh_client.get_crypto_positions()
        self.assertEqual(positions, [{'currency': {'code': 'BTC'}, 'quantity': '1.0'}])
        mock_get_crypto_positions.assert_called_once()

    @patch('robinhood_client.RobinhoodClient.rh.get_crypto_positions')
    def test_get_crypto_positions_failure(self, mock_get_crypto_positions):
        mock_get_crypto_positions.side_effect = Exception("Failed to get positions")
        with self.assertRaises(Exception):
            self.rh_client.get_crypto_positions()

    @patch('robinhood_client.RobinhoodClient.rh.cancel_order')
    def test_cancel_order_success(self, mock_cancel_order):
        mock_cancel_order.return_value = {'status': 'success'}
        result = self.rh_client.cancel_order('test_order_id')
        self.assertEqual(result, {'status': 'success'})
        mock_cancel_order.assert_called_once_with('test_order_id')

    @patch('robinhood_client.RobinhoodClient.rh.cancel_order')
    def test_cancel_order_failure(self, mock_cancel_order):
        mock_cancel_order.side_effect = Exception("Failed to cancel order")
        with self.assertRaises(Exception):
            self.rh_client.cancel_order('test_order_id')

    def test_is_market_open(self):
        # This test is difficult to mock effectively without significant overhead.
        # Consider mocking the market hours endpoint if precise control is needed.
        # For now, a simple assertion that it returns a boolean is sufficient.
        self.assertIsInstance(self.rh_client.is_market_open(), bool)

if __name__ == '__main__':
    unittest.main()