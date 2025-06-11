import os
from dotenv import load_dotenv
from src.base_api_client import CcdataBaseApiClient
from src.logger_config import setup_logger

# Load environment variables from .env file
load_dotenv()

# Configure logging using the centralized setup
logger = setup_logger(__name__)

# Use the single API key from .env
CCDATA_API_KEY = os.getenv("CCDATA_API_KEY")

# Hardcode the base URL as per instructions
MIN_API_BASE_URL = "https://min-api.cryptocompare.com"


class MinApiIndexApiClient(CcdataBaseApiClient):
    """
    A client for interacting with the CryptoCompare (ccdata) 'Index' endpoints on min-api.
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initializes the Index API client.

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
            logger.warning("CCDATA_API_KEY is not set. Some Index API calls may fail.")
