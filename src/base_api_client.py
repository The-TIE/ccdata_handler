import requests
import os
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
    RetryCallState,
)
from .logger_config import setup_logger

# Load environment variables from .env file
load_dotenv()

# Configure logging using the centralized setup
logger = setup_logger(__name__)


# Helper function for tenacity to decide if an HTTPError is retryable
def _should_retry_http_exception(exception: BaseException) -> bool:
    if isinstance(exception, requests.exceptions.HTTPError):
        # Retry on 429 (Too Many Requests) and 5xx server errors
        return exception.response.status_code in [429, 500, 502, 503, 504]
    return False


class CcdataBaseApiClient:
    """
    A base client for interacting with CryptoCompare (ccdata) APIs.
    Provides common functionality like session management, retry logic, and error handling.
    """

    def __init__(self, api_key: str, base_url: str):
        """
        Initializes the base API client.

        Args:
            api_key (str): The API key for authentication.
            base_url (str): The base URL for the specific API (e.g., Min API, Data API).
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()

        if not self.api_key:
            logger.warning(
                f"API Key for {self.base_url} is not set. Some API calls may fail."
            )
        if not self.base_url:
            logger.error("API base URL is not configured.")
            raise ValueError("API base URL is not configured.")

        self.session.headers.update({"Authorization": f"Apikey {self.api_key}"})

    @staticmethod
    def _log_retry_attempt(retry_state: RetryCallState):
        """Logs information about a retry attempt. Static as it doesn't rely on instance state."""
        if retry_state.outcome.failed:
            exception = retry_state.outcome.exception()
            called_func_name = retry_state.fn.__name__
            endpoint_info = "unknown endpoint"
            if called_func_name == "_request" and len(retry_state.args) >= 3:
                endpoint_info = (
                    f"{retry_state.args[1]} {retry_state.args[2]}"  # method endpoint
                )

            logger.warning(
                f"Retrying API call ({endpoint_info}) "
                f"due to {type(exception).__name__}: {exception}. "
                f"This is attempt {retry_state.attempt_number} of {retry_state.retry_object.stop.max_attempt_number}."
            )

    @retry(
        wait=wait_exponential(
            multiplier=1, min=2, max=30
        ),  # wait 2^x * 1 seconds, min 2s, max 30s
        stop=stop_after_attempt(5),  # stop after 5 attempts (1 initial + 4 retries)
        retry=(
            retry_if_exception_type(requests.exceptions.Timeout)
            | retry_if_exception_type(requests.exceptions.ConnectionError)
            | retry_if_exception_type(requests.exceptions.ChunkedEncodingError)
            | retry_if_exception(
                _should_retry_http_exception
            )  # Use the helper function
        ),
        before_sleep=_log_retry_attempt,  # Reference the static method directly
    )
    def _request(
        self, method: str, endpoint: str, params: dict = None, data: dict = None
    ) -> dict:
        """
        Makes an HTTP request to the specified endpoint with retry logic.

        Args:
            method (str): HTTP method (e.g., "GET", "POST").
            endpoint (str): API endpoint path (e.g., "/price").
            params (dict, optional): URL parameters for GET requests.
            data (dict, optional): Payload for POST requests.

        Returns:
            dict: The JSON response from the API.

        Raises:
            requests.exceptions.HTTPError: If an HTTP error occurs.
            requests.exceptions.RequestException: For other request-related errors.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method, url, params=params, json=data, timeout=10
            )
            response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(
                f"HTTP error occurred: {http_err} - {response.text}", exc_info=True
            )
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request exception occurred: {req_err}", exc_info=True)
            raise
        except ValueError as json_err:  # Includes JSONDecodeError
            logger.error(
                f"Failed to decode JSON response: {json_err} - Response: {response.text}",
                exc_info=True,
            )
            raise

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """
        Helper method for making GET requests.
        """
        return self._request("GET", endpoint, params=params)

    def _post(self, endpoint: str, data: dict = None) -> dict:
        """
        Helper method for making POST requests.
        """
        return self._request("POST", endpoint, data=data)
