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


class CcdataUtilitiesApiClient(CcdataBaseApiClient):
    """
    A client for interacting with the CryptoCompare (ccdata) "Utilities API".
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initializes the Utilities API client.

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
                "CCDATA_API_KEY is not set. Some Utilities API calls may fail."
            )


if __name__ == "__main__":
    print("Attempting to initialize CcdataUtilitiesApiClient...")
    print(f"API Key from env: {'Set' if CCDATA_API_KEY else 'Not Set'}")
    print(f"Base URL: {DATA_API_BASE_URL}")

    if not CCDATA_API_KEY:
        print("\nWARNING: CCDATA_API_KEY is not set in your .env file.")
        print("Please add it to your .env file in the project root.")
        print("Example: CCDATA_API_KEY=your_actual_api_key_here\n")

    try:
        client = CcdataUtilitiesApiClient()
        print("CcdataUtilitiesApiClient initialized successfully.")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
