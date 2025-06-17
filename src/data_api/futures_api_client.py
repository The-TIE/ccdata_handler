import os
from dotenv import load_dotenv
from ..base_api_client import CcdataBaseApiClient
from ..logger_config import setup_logger

# Load environment variables from .env file
load_dotenv()

# Configure logging using the centralized setup
logger = setup_logger(__name__)

# Use the single API key from .env
CCDATA_API_KEY = os.getenv("CCDATA_API_KEY")

# Hardcode the base URL as per instructions
DATA_API_BASE_URL = "https://data-api.coindesk.com"


class CcdataFuturesApiClient(CcdataBaseApiClient):
    """
    A client for interacting with the CryptoCompare (ccdata) "Futures API".
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initializes the Futures API client.

        Args:
            api_key (str, optional): The API key for authentication.
                                     Defaults to CCDATA_API_KEY from environment.
            base_url (str, optional): The base URL for the Data API.
                                       Defaults to hardcoded DATA_API_BASE_URL.
        """
        super().__init__(
            api_key=api_key or CCDATA_API_KEY,
            base_url=base_url or DATA_API_BASE_URL,
        )
        if not self.api_key:
            logger.warning(
                "CCDATA_API_KEY is not set. Some Futures API calls may fail."
            )


    def get_futures_markets(self, market: str = None, groups: list = None):
        """
        Fetches comprehensive information about futures markets.

        Args:
            market (str, optional): The exchange to obtain data from. Defaults to None.
            groups (list, optional): Filter by specific groups of interest. Defaults to None.

        Returns:
            dict: The API response containing futures market data.
        """
        endpoint = "/futures/v1/markets"
        params = {}
        if market:
            params["market"] = market
        if groups:
            params["groups"] = groups
        return self._get(endpoint, params=params)

    def get_futures_markets_instruments(
        self,
        market: str = None,
        instruments: list = None,
        instrument_status: list = None,
        groups: list = None,
    ):
        """
        Retrieves a dictionary of mapped instruments across futures markets.

        Args:
            market (str, optional): The exchange to obtain data from. Defaults to None.
            instruments (list, optional): The mapped instruments to retrieve. Defaults to None.
            instrument_status (list, optional): Filter by instrument status. Defaults to None.
            groups (list, optional): Filter by specific groups of interest. Defaults to None.

        Returns:
            dict: The API response containing futures market instrument data.
        """
        endpoint = "/futures/v1/markets/instruments"
        params = {}
        if market:
            params["market"] = market
        if instruments:
            params["instruments"] = instruments
        if instrument_status:
            params["instrument_status"] = instrument_status
        if groups:
            params["groups"] = groups
        return self._get(endpoint, params=params)


if __name__ == "__main__":
    print("Attempting to initialize CcdataFuturesApiClient...")
    print(f"API Key from env: {'Set' if CCDATA_API_KEY else 'Not Set'}")
    print(f"Base URL: {DATA_API_BASE_URL}")

    if not CCDATA_API_KEY:
        print("\nWARNING: CCDATA_API_KEY is not set in your .env file.")
        print("Please add it to your .env file in the project root.")
        print("Example: CCDATA_API_KEY=your_actual_api_key_here\n")

    try:
        client = CcdataFuturesApiClient()
        print("CcdataFuturesApiClient initialized successfully.")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
