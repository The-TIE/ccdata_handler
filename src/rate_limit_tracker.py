import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from src.data_api.utilities_api_client import CcdataUtilitiesApiClient
from src.db.connection import DbConnectionManager
from src.db.utils import to_mysql_datetime
from src.logger_config import setup_logger

load_dotenv()
logger = setup_logger(__name__)
CCDATA_API_KEY = os.getenv("CCDATA_API_KEY")


def record_rate_limit_status(use_case: str, record_timing: str):
    """
    Fetches and records the current API rate limit status.

    Args:
        use_case (str): A string identifying the script or use case making the API call.
        record_timing (str): 'pre' or 'post' indicating when the record was made relative to an API call.
    """
    if not CCDATA_API_KEY:
        logger.warning("CCDATA_API_KEY is not set. Cannot record rate limit status.")
        return

    utilities_client = CcdataUtilitiesApiClient(api_key=CCDATA_API_KEY)
    db_manager = None
    try:
        rate_limit_data = utilities_client.get_rate_limit_status()
        if not rate_limit_data or "Data" not in rate_limit_data:
            logger.warning("Failed to retrieve rate limit status data.")
            return

        data = rate_limit_data["Data"]
        now = datetime.now(timezone.utc)

        record = {
            "timestamp": to_mysql_datetime(now),
            "use_case": use_case,
            "record_timing": record_timing,
            "api_key_used_second": data.get("API_KEY", {})
            .get("USED", {})
            .get("SECOND"),
            "api_key_used_minute": data.get("API_KEY", {})
            .get("USED", {})
            .get("MINUTE"),
            "api_key_used_hour": data.get("API_KEY", {}).get("USED", {}).get("HOUR"),
            "api_key_used_day": data.get("API_KEY", {}).get("USED", {}).get("DAY"),
            "api_key_used_month": data.get("API_KEY", {}).get("USED", {}).get("MONTH"),
            "api_key_max_second": data.get("API_KEY", {}).get("MAX", {}).get("SECOND"),
            "api_key_max_minute": data.get("API_KEY", {}).get("MAX", {}).get("MINUTE"),
            "api_key_max_hour": data.get("API_KEY", {}).get("MAX", {}).get("HOUR"),
            "api_key_max_day": data.get("API_KEY", {}).get("MAX", {}).get("DAY"),
            "api_key_max_month": data.get("API_KEY", {}).get("MAX", {}).get("MONTH"),
            "api_key_remaining_second": data.get("API_KEY", {})
            .get("REMAINING", {})
            .get("SECOND"),
            "api_key_remaining_minute": data.get("API_KEY", {})
            .get("REMAINING", {})
            .get("MINUTE"),
            "api_key_remaining_hour": data.get("API_KEY", {})
            .get("REMAINING", {})
            .get("HOUR"),
            "api_key_remaining_day": data.get("API_KEY", {})
            .get("REMAINING", {})
            .get("DAY"),
            "api_key_remaining_month": data.get("API_KEY", {})
            .get("REMAINING", {})
            .get("MONTH"),
            "auth_key_used_second": data.get("AUTH_KEY", {})
            .get("USED", {})
            .get("SECOND"),
            "auth_key_used_minute": data.get("AUTH_KEY", {})
            .get("USED", {})
            .get("MINUTE"),
            "auth_key_used_hour": data.get("AUTH_KEY", {}).get("USED", {}).get("HOUR"),
            "auth_key_used_day": data.get("AUTH_KEY", {}).get("USED", {}).get("DAY"),
            "auth_key_used_month": data.get("AUTH_KEY", {})
            .get("USED", {})
            .get("MONTH"),
            "auth_key_max_second": data.get("AUTH_KEY", {})
            .get("MAX", {})
            .get("SECOND"),
            "auth_key_max_minute": data.get("AUTH_KEY", {})
            .get("MAX", {})
            .get("MINUTE"),
            "auth_key_max_hour": data.get("AUTH_KEY", {}).get("MAX", {}).get("HOUR"),
            "auth_key_max_day": data.get("AUTH_KEY", {}).get("MAX", {}).get("DAY"),
            "auth_key_max_month": data.get("AUTH_KEY", {}).get("MAX", {}).get("MONTH"),
            "auth_key_remaining_second": data.get("AUTH_KEY", {})
            .get("REMAINING", {})
            .get("SECOND"),
            "auth_key_remaining_minute": data.get("AUTH_KEY", {})
            .get("REMAINING", {})
            .get("MINUTE"),
            "auth_key_remaining_hour": data.get("AUTH_KEY", {})
            .get("REMAINING", {})
            .get("HOUR"),
            "auth_key_remaining_day": data.get("AUTH_KEY", {})
            .get("REMAINING", {})
            .get("DAY"),
            "auth_key_remaining_month": data.get("AUTH_KEY", {})
            .get("REMAINING", {})
            .get("MONTH"),
        }

        db_manager = DbConnectionManager()
        db_manager.insert_dataframe(
            [record], "market.cc_rate_limit_status", replace=False
        )
        logger.info(
            f"Rate limit status recorded for use case '{use_case}' ({record_timing})."
        )

    except Exception as e:
        logger.error(
            f"Error recording rate limit status for use case '{use_case}': {e}"
        )
    finally:
        if db_manager:
            db_manager.close_connection()


if __name__ == "__main__":
    # Example usage:
    record_rate_limit_status("test_script", "pre")
    # Simulate some API calls
    # record_rate_limit_status("test_script", "post")
