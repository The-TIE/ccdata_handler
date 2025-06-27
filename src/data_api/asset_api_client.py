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


class CcdataAssetApiClient(CcdataBaseApiClient):
    """
    A client for interacting with the CryptoCompare (ccdata) "Asset API".
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initializes the Asset API client.

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
            logger.warning("CCDATA_API_KEY is not set. Some Asset API calls may fail.")

    def get_top_list_general(
        self,
        page: int = 1,
        page_size: int = 100,
        sort_by: str = "CIRCULATING_MKT_CAP_USD",
        sort_direction: str = "DESC",
        groups: list = None,
        toplist_quote_asset: str = "USD",
        asset_type: str = None,
        asset_industry: str = None,
    ) -> dict:
        """
        Provides ranked overviews of digital assets and industries based on critical financial metrics.

        Args:
            page (int, optional): The page number for the request. Defaults to 1.
            page_size (int, optional): The number of items returned per page. Defaults to 100.
            sort_by (str, optional): Field to sort by. Defaults to "CIRCULATING_MKT_CAP_USD".
            sort_direction (str, optional): Sort direction ("DESC" or "ASC"). Defaults to "DESC".
            groups (list, optional): Filter by specific groups of interest. Defaults to None.
            toplist_quote_asset (str, optional): Digital asset for the quote values. Defaults to "USD".
            asset_type (str, optional): Filter assets by type. Defaults to None.
            asset_industry (str, optional): Filter assets by industry. Defaults to None.

        Returns:
            dict: A dictionary containing the top list data.
        """
        endpoint = "/asset/v1/top/list"
        params = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_direction": sort_direction,
            "groups": ",".join(groups) if groups else None,
            "toplist_quote_asset": toplist_quote_asset,
            "asset_type": asset_type,
            "asset_industry": asset_industry,
        }
        params = {k: v for k, v in params.items() if v is not None}
        logger.info(f"Fetching top list general with params: {params}")
        return self._request("GET", endpoint, params=params)


if __name__ == "__main__":
    print("Attempting to initialize CcdataAssetApiClient...")
    print(f"API Key from env: {'Set' if CCDATA_API_KEY else 'Not Set'}")
    print(f"Base URL: {DATA_API_BASE_URL}")

    if not CCDATA_API_KEY:
        print("\nWARNING: CCDATA_API_KEY is not set in your .env file.")
        print("Please add it to your .env file in the project root.")
        print("Example: CCDATA_API_KEY=your_actual_api_key_here\n")

    try:
        client = CcdataAssetApiClient()
        print("CcdataAssetApiClient initialized successfully.")

        # Example usage: Get top 5 assets by 24-hour volume
        print("\nFetching top 5 assets by 24-hour volume...")
        top_assets = client.get_top_list_general(
            page_size=5, sort_by="SPOT_MOVING_24_HOUR_QUOTE_VOLUME_USD"
        )
        print("Top Assets:", top_assets)

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
