import os
from dotenv import load_dotenv
from src.base_api_client import CcdataBaseApiClient
from src.logger_config import setup_logger
from typing import Optional, Dict

# Load environment variables from .env file
load_dotenv()

# Configure logging using the centralized setup
logger = setup_logger(__name__)

# Use the single API key from .env
CCDATA_API_KEY = os.getenv("CCDATA_API_KEY")

# Hardcode the base URL as per instructions
MIN_API_BASE_URL = "https://min-api.cryptocompare.com"


class MinApiGeneralInfoApiClient(CcdataBaseApiClient):
    """
    A client for interacting with the CryptoCompare (ccdata) 'General Info' endpoints on min-api.
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initializes the General Info API client.

        Args:
            api_key (str, optional): The API key for authentication.
                                     Defaults to CCDATA_API_KEY from environment.
            base_url (str, optional): The base URL for the Min API.
                                      Defaults to hardcoded MIN_API_BASE_URL.
        """
        super().__init__(
            api_key=api_key or CCDATA_API_KEY,
            base_url=base_url or MIN_API_BASE_URL,
        )
        if not self.api_key:
            logger.warning(
                "CCDATA_API_KEY is not set. Some General Info API calls may fail."
            )

    def get_all_exchanges(
        self,
        fsym: Optional[str] = None,
        e: Optional[str] = None,
        topTier: Optional[bool] = None,
        extraParams: Optional[str] = None,
    ) -> Dict:
        """
        Returns all the exchanges that CryptoCompare has integrated with.
        You can filter by exchange and from symbol.

        Parameters:
            fsym (Optional[str], optional): The cryptocurrency symbol of interest (max length 30)
            e (Optional[str], optional): The exchange to obtain data from (max length 30)
            topTier (Optional[bool], optional): Set to true to return just the top tier exchanges
            extraParams (Optional[str], optional): The name of your application (recommended, min length 1, max length 2000, default: NotAvailable)

        Returns:
            Dict: API response
        """
        endpoint = "/data/v4/all/exchanges"
        params = {}
        if fsym is not None:
            params["fsym"] = fsym
        if e is not None:
            params["e"] = e
        if topTier is not None:
            params["topTier"] = str(topTier).lower()
        if extraParams is not None:
            params["extraParams"] = extraParams

        return self._get(endpoint, params=params)

    def get_exchanges_general_info(
        self,
        tsym: str = "USD",
        extraParams: str = "NotAvailable",
        sign: Optional[bool] = None,
    ) -> Dict:
        """
        Returns general info and 24h volume for all the exchanges integrated with.

        Parameters:
            tsym (str, optional): The currency symbol to convert into. Min length: 1, Max length: 30. Default: "BTC"
            extraParams (str, optional): The name of your application. Min length: 1, Max length: 2000. Default: "NotAvailable"
            sign (Optional[bool], optional): If set to true, the server will sign the requests (useful for smart contracts).

        Returns:
            Dict: API response
        """
        endpoint = "/data/exchanges/general"
        params = {
            "tsym": tsym,
            "extraParams": extraParams,
        }
        if sign is not None:
            params["sign"] = str(sign).lower()

        return self._get(endpoint, params=params)
