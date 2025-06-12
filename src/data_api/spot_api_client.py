import os
from dotenv import load_dotenv
from typing import List, Optional
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


class CcdataSpotApiClient(CcdataBaseApiClient):
    """
    A client for interacting with the CryptoCompare (ccdata) "Spot API".
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initializes the Spot API client.

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
            logger.warning("CCDATA_API_KEY is not set. Some Spot API calls may fail.")

    def get_historical_ohlcv(
        self,
        interval: str,  # "days", "hours", or "minutes"
        market: str,
        instrument: str,
        groups: Optional[List[str]] = None,
        limit: Optional[int] = None,  # Set default based on interval in logic
        to_ts: Optional[int] = None,
        aggregate: int = 1,
        fill: bool = True,
        apply_mapping: bool = True,
        response_format: str = "JSON",
    ) -> dict:
        """
        Delivers historical aggregated candlestick data (daily, hourly, or minute)
        for specific cryptocurrency instruments across selected exchanges.

        Args:
            interval (str): The historical interval ("days", "hours", or "minutes").
            market (str): The market / exchange under consideration.
            instrument (str): A mapped and/or unmapped instrument to retrieve.
            groups (list, optional): Filter by specific groups of interest. Defaults to None.
            limit (int, optional): The number of data points to return. Defaults vary by interval.
            to_ts (int, optional): Returns historical data up to and including this Unix timestamp. Defaults to None.
            aggregate (int, optional): The number of points to aggregate for each returned value. Defaults to 1.
            fill (bool, optional): If false, will not return data points for periods with no trading activity. Defaults to True.
            apply_mapping (bool, optional): Determines if provided instrument values are converted. Defaults to True.
            response_format (str, optional): The format of the data response. Defaults to "JSON".

        Returns:
            dict: A dictionary containing historical OHLCV data.
        Raises:
            ValueError: If an invalid interval is provided.
        """
        if interval not in ["days", "hours", "minutes"]:
            raise ValueError("Invalid interval. Must be 'days', 'hours', or 'minutes'.")

        endpoint = f"/spot/v1/historical/{interval}"

        # Set default limit based on interval if not provided
        if limit is None:
            if interval == "days":
                limit = 30
            elif interval == "hours":
                limit = 168
            elif interval == "minutes":
                limit = 1440

        params = {
            "market": market,
            "instrument": instrument,
            "groups": ",".join(groups) if groups else None,
            "limit": limit,
            "to_ts": to_ts,
            "aggregate": aggregate,
            "fill": str(fill).lower(),
            "apply_mapping": str(apply_mapping).lower(),
            "response_format": response_format,
        }
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Fetching {interval} OHLCV for {instrument} on {market}")
        return self._request("GET", endpoint, params=params)

    def get_trades_full_hour(
        self,
        market: str,
        instrument: str,
        groups: Optional[List[str]] = None,
        hour_ts: Optional[int] = None,
        apply_mapping: bool = True,
        response_format: str = "JSON",
        return_404_on_empty_response: bool = False,
        skip_invalid_messages: bool = False,
    ) -> dict:
        """
        Provides detailed, standardized, and deduplicated tick-level trade data for a specified instrument on a chosen exchange, covering a specific hour.

        Args:
            market (str): The exchange to obtain data from.
            instrument (str): A mapped and/or unmapped instrument to retrieve.
            groups (list, optional): Filter by specific groups of interest. Defaults to None.
            hour_ts (int, optional): Unix timestamp in seconds for the hour containing the trades. Defaults to None.
            apply_mapping (bool, optional): Determines if provided instrument values are converted. Defaults to True.
            response_format (str, optional): The format of the data response. Defaults to "JSON".
            return_404_on_empty_response (bool, optional): If true, returns 404 on empty response. Defaults to False.
            skip_invalid_messages (bool, optional): If true, filters out invalid trades. Defaults to False.

        Returns:
            dict: A dictionary containing trade data for the full hour.
        """
        endpoint = "/spot/v2/historical/trades/hour"
        params = {
            "market": market,
            "instrument": instrument,
            "groups": ",".join(groups) if groups else None,
            "hour_ts": hour_ts,
            "apply_mapping": str(apply_mapping).lower(),
            "response_format": response_format,
            "return_404_on_empty_response": str(return_404_on_empty_response).lower(),
            "skip_invalid_messages": str(skip_invalid_messages).lower(),
        }
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Fetching trades for {instrument} on {market} for hour {hour_ts}")
        return self._request("GET", endpoint, params=params)

    def get_trades_by_timestamp(
        self,
        market: str,
        instrument: str,
        after_ts: int,
        groups: Optional[List[str]] = None,
        last_ccseq: Optional[int] = None,
        limit: Optional[int] = None,
        apply_mapping: bool = True,
        response_format: str = "JSON",
        skip_invalid_messages: bool = False,
    ) -> dict:
        """
        Provides detailed, standardized, and deduplicated trade data for a specified instrument on a chosen exchange, starting from a given timestamp.

        Args:
            market (str): The exchange to obtain data from.
            instrument (str): A mapped and/or unmapped instrument to retrieve.
            after_ts (int): Unix timestamp in seconds of the earliest trade in the response.
            groups (list, optional): Filter by specific groups of interest. Defaults to None.
            last_ccseq (int, optional): The CCSEQ parameter for pagination within the same second. Defaults to None.
            limit (int, optional): The maximum number of trades to return. Defaults to 100.
            apply_mapping (bool, optional): Determines if provided instrument values are converted. Defaults to True.
            response_format (str, optional): The format of the data response. Defaults to "JSON".
            skip_invalid_messages (bool, optional): If true, filters out invalid trades. Defaults to False.

        Returns:
            dict: A dictionary containing trade data by timestamp.
        """
        endpoint = "/spot/v2/historical/trades"
        params = {
            "market": market,
            "instrument": instrument,
            "after_ts": after_ts,
            "groups": ",".join(groups) if groups else None,
            "last_ccseq": last_ccseq,
            "limit": limit,
            "apply_mapping": str(apply_mapping).lower(),
            "response_format": response_format,
            "skip_invalid_messages": str(skip_invalid_messages).lower(),
        }
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(
            f"Fetching trades for {instrument} on {market} after timestamp {after_ts}"
        )
        return self._request("GET", endpoint, params=params)

    def get_spot_market_instruments(
        self,
        market: Optional[str] = None,
        instrument: Optional[str] = None,
        groups: Optional[List[str]] = None,
        extra_params: Optional[str] = None,
        sign: Optional[bool] = None,
    ) -> dict:
        """
        Returns all the spot market instruments for all exchanges that CryptoCompare has integrated with.
        You can filter by exchange and instrument.

        Args:
            market (str, optional): The exchange to obtain data from. Defaults to None.
            instrument (str, optional): A mapped and/or unmapped instrument to retrieve. Defaults to None.
            groups (list, optional): Filter by specific groups of interest. Defaults to None.
            extra_params (str, optional): The name of your application. Defaults to None.
            sign (bool, optional): If set to true, the server will sign the requests. Defaults to None.

        Returns:
            dict: A dictionary containing spot market instruments data.
        """
        endpoint = "/spot/v1/markets/instruments"
        params = {
            "market": market,
            "instrument": instrument,
            "groups": ",".join(groups) if groups else None,
            "extraParams": extra_params,
            "sign": str(sign).lower() if sign is not None else None,
        }
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Fetching spot market instruments with params: {params}")
        return self._request("GET", endpoint, params=params)


if __name__ == "__main__":
    print("Attempting to initialize CcdataSpotApiClient...")
    print(f"API Key from env: {'Set' if CCDATA_API_KEY else 'Not Set'}")
    print(f"Base URL: {DATA_API_BASE_URL}")

    if not CCDATA_API_KEY:
        print("\nWARNING: CCDATA_API_KEY is not set in your .env file.")
        print("Please add it to your .env file in the project root.")
        print("Example: CCDATA_API_KEY=your_actual_api_key_here\n")

    try:
        client = CcdataSpotApiClient()
        print("CcdataSpotApiClient initialized successfully.")

        # Example usage: Get daily OHLCV data for BTC-USD on Kraken
        print("\nFetching daily OHLCV for BTC-USD on Kraken...")
        daily_ohlcv_data = client.get_historical_ohlcv(
            interval="days", market="kraken", instrument="BTC-USD", limit=2
        )
        print("Daily OHLCV Data:", daily_ohlcv_data)

        # Example usage: Get hourly OHLCV data for ETH-EUR on Coinbase
        print("\nFetching hourly OHLCV for ETH-EUR on Coinbase...")
        hourly_ohlcv_data = client.get_historical_ohlcv(
            interval="hours", market="coinbase", instrument="ETH-EUR", limit=2
        )
        print("Hourly OHLCV Data:", hourly_ohlcv_data)

        # Example usage: Get minute OHLCV data for XRP-USD on Binance
        print("\nFetching minute OHLCV for XRP-USD on Binance...")
        minute_ohlcv_data = client.get_historical_ohlcv(
            interval="minutes", market="binance", instrument="XRP-USD", limit=2
        )
        print("Minute OHLCV Data:", minute_ohlcv_data)

        # Example usage: Get trades for a full hour
        import time

        current_hour_ts = int(time.time()) - (int(time.time()) % 3600)
        print(
            f"\nFetching trades for BTC-USD on Coinbase for the hour {current_hour_ts}..."
        )
        hourly_trades = client.get_trades_full_hour(
            market="coinbase", instrument="BTC-USD", hour_ts=current_hour_ts, limit=2
        )
        print("Hourly Trades:", hourly_trades)

        # Example usage: Get trades by timestamp
        print(
            f"\nFetching trades for BTC-USD on Coinbase after timestamp {current_hour_ts}..."
        )
        trades_by_ts = client.get_trades_by_timestamp(
            market="coinbase", instrument="BTC-USD", after_ts=current_hour_ts, limit=2
        )
        print("Trades by Timestamp:", trades_by_ts)

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
