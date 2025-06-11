import os
from dotenv import load_dotenv
from .base_api_client import CcdataBaseApiClient
from .logger_config import setup_logger

# Load environment variables from .env file
load_dotenv()

# Configure logging using the centralized setup
logger = setup_logger(__name__)

# Use the single API key from .env
CCDATA_API_KEY = os.getenv("CCDATA_API_KEY")

# Hardcode the base URL as per instructions
MIN_API_BASE_URL = "https://min-api.cryptocompare.com/data"


class CcdataMinApiClient(CcdataBaseApiClient):
    """
    A client for interacting with the CryptoCompare (ccdata) "Min API".
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initializes the API client.

        Args:
            api_key (str, optional): The API key for authentication.
                                     Defaults to CCDATA_API_KEY from environment.
            base_url (str, optional): The base URL for the Min API.
                                      Defaults to hardcoded MIN_API_BASE_URL.
        """
        super().__init__(
            api_key=api_key or CCDATA_API_KEY, base_url=base_url or MIN_API_BASE_URL
        )
        if not self.api_key:
            logger.warning("CCDATA_API_KEY is not set. Some Min API calls may fail.")
        # Base URL is now hardcoded, so no need to check self.base_url here,
        # as it will always be set by super().__init__

    def get_price(self, fsym: str, tsyms: str) -> dict:
        """
        Get the current price of any cryptocurrency in any other currency that you need.

        Args:
            fsym (str): The cryptocurrency symbol of interest. [Max character length: 10]
            tsyms (str): Comma separated cryptocurrency symbols to convert into. [Max character length: 500]

        Returns:
            dict: A dictionary containing the price data.
                  Example: {"BTC": {"USD": 60000.75, "EUR": 55000.20}}
        """
        endpoint = "/price"
        params = {"fsym": fsym, "tsyms": tsyms}
        logger.info(f"Fetching price for {fsym} in {tsyms}")
        return self._request("GET", endpoint, params=params)

    def get_multi_price(self, fsyms: str, tsyms: str) -> dict:
        """
        Get the current price of any cryptocurrency in any other currency that you need.

        Args:
            fsyms (str): Comma separated cryptocurrency symbols of interest. [Max character length: 300]
            tsyms (str): Comma separated cryptocurrency symbols to convert into. [Max character length: 100]

        Returns:
            dict: A dictionary containing the price data.
                  Example: {"BTC": {"USD": 60000.75}, "ETH": {"USD": 3000.50}}
        """
        endpoint = "/pricemulti"
        params = {"fsyms": fsyms, "tsyms": tsyms}
        logger.info(f"Fetching multiple prices for {fsyms} in {tsyms}")
        return self._request("GET", endpoint, params=params)

    def get_all_exchanges_general_info(
        self, tsym: str = "BTC", extra_params: str = "NotAvailable", sign: bool = False
    ) -> dict:
        """
        Returns general info and 24h volume for all the exchanges integrated with.

        Args:
            tsym (str, optional): The currency symbol to convert into. Defaults to "BTC".
            extra_params (str, optional): The name of your application. Defaults to "NotAvailable".
            sign (bool, optional): If true, the server will sign the requests. Defaults to False.

        Returns:
            dict: A dictionary containing general exchange information.
        """
        endpoint = "/exchanges/general"
        params = {
            "tsym": tsym,
            "extraParams": extra_params,
            "sign": str(sign).lower(),  # Convert boolean to lowercase string
        }
        # Filter out None values from params
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Fetching general info for all exchanges with tsym={tsym}")
        return self._request("GET", endpoint, params=params)

    def get_daily_ohlcv(
        self,
        fsym: str,
        tsym: str,
        try_conversion: bool = True,
        e: str = "CCCAGG",
        aggregate: int = 1,
        limit: int = 30,
        all_data: bool = False,
        to_ts: int = None,
        explain_path: bool = False,
        extra_params: str = None,
        sign: bool = False,
    ) -> dict:
        """
        Get open, high, low, close, volumeFrom and volumeTo from the daily historical data.

        Args:
            fsym (str): The cryptocurrency symbol of interest.
            tsym (str): The currency symbol to convert into.
            try_conversion (bool, optional): If set to false, it will try to get only direct trading values. Defaults to True.
            e (str, optional): The exchange to obtain data from. Defaults to "CCCAGG".
            aggregate (int, optional): Time period to aggregate the data over. Defaults to 1.
            limit (int, optional): The number of data points to return. Defaults to 30.
            all_data (bool, optional): Returns all data (only available on histo day). Defaults to False.
            to_ts (int, optional): Returns historical data before that timestamp. Defaults to None.
            explain_path (bool, optional): If set to true, each point calculated will return the available options. Defaults to False.
            extra_params (str, optional): The name of your application. Defaults to None.
            sign (bool, optional): If true, the server will sign the requests. Defaults to False.

        Returns:
            dict: A dictionary containing daily historical OHLCV data.
        """
        endpoint = "/v2/histoday"
        params = {
            "fsym": fsym,
            "tsym": tsym,
            "tryConversion": str(
                try_conversion
            ).lower(),  # Convert boolean to lowercase string
            "e": e,
            "aggregate": aggregate,
            "limit": limit,
            "allData": str(all_data).lower(),  # Convert boolean to lowercase string
            "toTs": to_ts,
            "explainPath": str(
                explain_path
            ).lower(),  # Convert boolean to lowercase string
            "extraParams": extra_params,
            "sign": str(sign).lower(),  # Convert boolean to lowercase string
        }
        # Filter out None values from params
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Fetching daily OHLCV for {fsym} to {tsym}")
        return self._request("GET", endpoint, params=params)

    def get_minute_ohlcv(
        self,
        fsym: str,
        tsym: str,
        try_conversion: bool = True,
        e: str = "CCCAGG",
        aggregate: int = 1,
        limit: int = 1440,
        to_ts: int = None,
        explain_path: bool = False,
        extra_params: str = None,
        sign: bool = False,
    ) -> dict:
        """
        Get open, high, low, close, volumeFrom and volumeTo from the each minute historical data.

        Args:
            fsym (str): The cryptocurrency symbol of interest.
            tsym (str): The currency symbol to convert into.
            try_conversion (bool, optional): If set to false, it will try to get only direct trading values. Defaults to True.
            e (str, optional): The exchange to obtain data from. Defaults to "CCCAGG".
            aggregate (int, optional): Time period to aggregate the data over. Defaults to 1.
            limit (int, optional): The number of data points to return. Defaults to 1440.
            to_ts (int, optional): Returns historical data before that timestamp. Defaults to None.
            explain_path (bool, optional): If set to true, each point calculated will return the available options. Defaults to False.
            extra_params (str, optional): The name of your application. Defaults to None.
            sign (bool, optional): If true, the server will sign the requests. Defaults to False.
        Returns:
            dict: A dictionary containing minute historical OHLCV data.
        """
        endpoint = "/v2/histominute"
        params = {
            "fsym": fsym,
            "tsym": tsym,
            "tryConversion": str(
                try_conversion
            ).lower(),  # Convert boolean to lowercase string
            "e": e,
            "aggregate": aggregate,
            "limit": limit,
            "toTs": to_ts,
            "explainPath": str(
                explain_path
            ).lower(),  # Convert boolean to lowercase string
            "extraParams": extra_params,
            "sign": str(sign).lower(),  # Convert boolean to lowercase string
        }
        # Filter out None values from params
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Fetching minute OHLCV for {fsym} to {tsym}")
        return self._request("GET", endpoint, params=params)


if __name__ == "__main__":
    # This is an example of how to use the client.
    # Make sure CCDATA_API_KEY is in your .env file.
    print("Attempting to initialize CcdataMinApiClient...")
    print(f"API Key from env: {'Set' if CCDATA_API_KEY else 'Not Set'}")
    print(f"Base URL: {MIN_API_BASE_URL}")

    if not CCDATA_API_KEY:
        print("\nWARNING: CCDATA_API_KEY is not set in your .env file.")
        print("Please create a .env file in the root of the project with:")
        print("CCDATA_API_KEY=your_actual_api_key_here\n")

    try:
        client = CcdataMinApiClient()

        # Example usage: Get BTC price in USD and EUR
        print("\nFetching BTC price in USD,EUR...")
        btc_price = client.get_price(fsym="BTC", tsyms="USD,EUR")
        print("BTC Price Data:", btc_price)

        # Example usage: Get multiple prices
        print("\nFetching BTC,ETH prices in USD...")
        multi_price = client.get_multi_price(fsyms="BTC,ETH", tsyms="USD")
        print("Multiple Price Data:", multi_price)

        # Example usage: Get all exchanges general info
        print("\nFetching all exchanges general info...")
        exchanges_info = client.get_all_exchanges_general_info(tsym="USD")
        print("All Exchanges Info (first 500 chars):", str(exchanges_info)[:500])

        # Example usage: Get daily OHLCV data for BTC to USD
        print("\nFetching daily OHLCV for BTC to USD...")
        daily_ohlcv = client.get_daily_ohlcv(fsym="BTC", tsym="USD", limit=2)
        print("Daily OHLCV Data:", daily_ohlcv)

        # Example usage: Get minute OHLCV data for ETH to EUR
        print("\nFetching minute OHLCV for ETH to EUR...")
        minute_ohlcv = client.get_minute_ohlcv(fsym="ETH", tsym="EUR", limit=2)
        print("Minute OHLCV Data:", minute_ohlcv)

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except requests.exceptions.HTTPError as he:
        print(f"API HTTP Error: {he}")
    except requests.exceptions.RequestException as re:
        print(f"API Request Error: {re}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    print(
        "\nNote: For actual use, ensure your API key has permissions for the 'Min API' endpoints."
    )
