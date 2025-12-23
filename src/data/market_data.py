import os
import logging
import requests
import json
from typing import Optional, Dict
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CoinGeckoAPI:
    """
    A class to fetch market data from the CoinGecko API with caching.
    """

    def __init__(self, api_url: str = "https://api.coingecko.com/api/v3"):
        """
        Initializes the CoinGeckoAPI client.

        Args:
            api_url (str): The base URL for the CoinGecko API.
        """
        self.api_url = api_url
        self.cache_max_size = int(os.environ.get("COINGECKO_CACHE_SIZE", 128))  # Default cache size 128
        self.cache_ttl = int(os.environ.get("COINGECKO_CACHE_TTL", 60)) # Default TTL 60 seconds
        self._cached_get = lru_cache(maxsize=self.cache_max_size)(self._get)


    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Fetches data from the CoinGecko API.

        Args:
            endpoint (str): The API endpoint to call.
            params (Optional[Dict]): Query parameters for the request.

        Returns:
            Optional[Dict]: A dictionary containing the JSON response from the API, or None if an error occurred.
        """
        try:
            url = f"{self.api_url}{endpoint}"
            response = requests.get(url, params=params, timeout=10)  # Added timeout
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            return None

    def get_price(self, coin_id: str, vs_currencies: str = "usd") -> Optional[Dict]:
        """
        Fetches the current price of a cryptocurrency.

        Args:
            coin_id (str): The ID of the cryptocurrency (e.g., "bitcoin").
            vs_currencies (str): A comma-separated string of currencies to compare against (e.g., "usd,eur").

        Returns:
            Optional[Dict]: A dictionary containing the price data, or None if an error occurred.
        """
        endpoint = f"/simple/price"
        params = {"ids": coin_id, "vs_currencies": vs_currencies}
        return self._cached_get(endpoint, params)

    def clear_cache(self):
        """
        Clears the cache.  Useful for testing or when cache invalidation is needed.
        """
        self._cached_get.cache_clear()

    # Example usage (can be removed or commented out for production)
    def test(self):
        """
        Tests the API client.
        """
        price_data = self.get_price("bitcoin", "usd")
        if price_data:
            print(f"Price of Bitcoin in USD: {price_data}")
        else:
            print("Failed to fetch Bitcoin price.")


if __name__ == '__main__':
    # Example Usage
    api = CoinGeckoAPI()
    api.test()