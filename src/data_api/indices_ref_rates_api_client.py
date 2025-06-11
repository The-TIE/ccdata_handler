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


class CcdataIndicesRefRatesApiClient(CcdataBaseApiClient):
    """
    A client for interacting with the CryptoCompare (ccdata) "Indices & Ref. Rates API".
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initializes the Indices & Ref. Rates API client.

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
                "CCDATA_API_KEY is not set. Some Indices & Ref. Rates API calls may fail."
            )

    def get_latest_tick(
        self,
        market: str,
        instruments: list,
        groups: list = None,
        apply_mapping: bool = True,
    ) -> dict:
        """
        Provides the latest tick data for selected index instruments across various indices.

        Args:
            market (str): The index family to obtain data from.
            instruments (list): A comma separated array of instruments to retrieve.
            groups (list, optional): Filter by specific groups of interest. Defaults to None.
            apply_mapping (bool, optional): Determines if provided instrument values are converted. Defaults to True.

        Returns:
            dict: A dictionary containing the latest tick data.
        """
        endpoint = "/index/cc/v1/latest/tick"
        params = {
            "market": market,
            "instruments": ",".join(instruments),
            "groups": ",".join(groups) if groups else None,
            "apply_mapping": str(apply_mapping).lower(),
        }
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Fetching latest tick for {instruments} on {market}")
        return self._request("GET", endpoint, params=params)

    def get_historical_ohlcv(
        self,
        time_period: str,
        market: str,
        instrument: str,
        groups: list = None,
        limit: int = 30,
        to_ts: int = None,
        fill: bool = True,
        apply_mapping: bool = True,
        response_format: str = "JSON",
        aggregate: int = 1,
    ) -> dict:
        """
        Provides historical OHLCV (Open, High, Low, Close, Volume) data for selected index instruments.

        Args:
            time_period (str): The time period for the OHLCV data ('daily', 'hourly', or 'minutes').
            market (str): The index family to obtain data from.
            instrument (str): An instrument to retrieve from a specific market.
            groups (list, optional): Filter by specific groups of interest. Defaults to None.
            limit (int, optional): The number of data points to return. Max limit is 5000 for daily, 2000 for hourly/minute.
            to_ts (int, optional): Returns historical data up to and including this Unix timestamp. Defaults to None.
            fill (bool, optional): If set to false, will not return data points for periods with no trading activity. Defaults to True.
            apply_mapping (bool, optional): Determines if provided instrument values are converted. Defaults to True.
            response_format (str, optional): The format of the data response ('JSON' or 'CSV'). Defaults to "JSON".
            aggregate (int, optional): The number of OHLCV data points to aggregate into one data point. Defaults to 1.

        Returns:
            dict: A dictionary containing the historical OHLCV data.

        Raises:
            ValueError: If an invalid time_period is provided or limit exceeds max for the time_period.
        """
        if time_period not in ["days", "hours", "minutes"]:
            raise ValueError("time_period must be 'days', 'hours', or 'minutes'.")

        max_limit = 5000 if time_period == "days" else 2000
        if limit > max_limit:
            raise ValueError(f"Limit for {time_period} data cannot exceed {max_limit}.")

        endpoint = f"/index/cc/v1/historical/{time_period}"
        params = {
            "market": market,
            "instrument": instrument,
            "groups": ",".join(groups) if groups else None,
            "limit": limit,
            "to_ts": to_ts,
            "fill": str(fill).lower(),
            "apply_mapping": str(apply_mapping).lower(),
            "response_format": response_format,
            "aggregate": aggregate,
        }
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(
            f"Fetching historical OHLCV ({time_period}) for {instrument} on {market}"
        )
        return self._request("GET", endpoint, params=params)


if __name__ == "__main__":
    print("Attempting to initialize CcdataIndicesRefRatesApiClient...")
    print(f"API Key from env: {'Set' if CCDATA_API_KEY else 'Not Set'}")
    print(f"Base URL: {DATA_API_BASE_URL}")

    if not CCDATA_API_KEY:
        print("\nWARNING: CCDATA_API_KEY is not set in your .env file.")
        print("Please add it to your .env file in the project root.")
        print("Example: CCDATA_API_KEY=your_actual_api_key_here\n")

    try:
        client = CcdataIndicesRefRatesApiClient()

        # Example usage: Get latest tick data for BTC-USD and ETH-USD on cadli
        print("\nFetching latest tick for BTC-USD and ETH-USD on cadli...")
        latest_tick_data = client.get_latest_tick(
            market="cadli", instruments=["BTC-USD", "ETH-USD"]
        )
        print("Latest Tick Data:", latest_tick_data)

        # Example usage: Get historical daily OHLCV+ data for BTC-USD on cadli
        print("\nFetching historical daily OHLCV+ for BTC-USD on cadli...")
        historical_daily_ohlcv_data = client.get_historical_ohlcv(
            time_period="daily", market="cadli", instrument="BTC-USD", limit=5
        )
        print("Historical Daily OHLCV+ Data:", historical_daily_ohlcv_data)

        # Example usage: Get historical hourly OHLCV+ data for ETH-USD on cadli
        print("\nFetching historical hourly OHLCV+ for ETH-USD on cadli...")
        historical_hourly_ohlcv_data = client.get_historical_ohlcv(
            time_period="hourly",
            market="cadli",
            instrument="ETH-USD",
            limit=5,
            aggregate=4,
        )
        print("Historical Hourly OHLCV+ Data:", historical_hourly_ohlcv_data)

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
