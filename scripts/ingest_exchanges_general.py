import os
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from src.min_api.general_info_api_client import MinApiGeneralInfoApiClient
from src.db.connection import DbConnectionManager
from src.logger_config import setup_logger
from src.db.utils import to_mysql_datetime, deduplicate_table
from src.rate_limit_tracker import record_rate_limit_status

# Load environment variables from .env file
load_dotenv()

# Configure logging using the centralized setup
script_name = os.path.splitext(os.path.basename(__file__))[0]
log_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    f"{script_name}.log",
)
logger = setup_logger(__name__, log_to_console=True, log_file_path=log_file_path)


def fetch_exchanges_general_data(api_client):
    """Fetch general exchange data from the API."""
    logger.info("Fetching general exchange data.")
    response = api_client.get_exchanges_general_info()
    if not response or response.get("Response") == "Error":
        logger.error(
            f"Failed to retrieve general exchange data: {response.get('Message', 'Unknown error')}"
        )
        return None
    logger.info("Successfully fetched general exchange data.")
    return response.get("Data", {})


def transform_exchanges_general_data(raw_data):
    """Transform raw exchange data into a structured format for `market.cc_exchanges_general` table."""
    now_utc = datetime.now(timezone.utc)
    exchanges_to_insert = []

    for exchange_api_id, exchange_info in raw_data.items():
        exchanges_to_insert.append(
            {
                "exchange_api_id": exchange_api_id,
                "name": exchange_info.get("Name"),
                "internal_name": exchange_info.get("InternalName"),
                "api_url_path": exchange_info.get("Url"),
                "logo_url_path": exchange_info.get("LogoUrl"),
                "item_types": json.dumps(exchange_info.get("ItemType") or []),
                "centralization_type": exchange_info.get("CentralizationType"),
                "grade_points": exchange_info.get("GradePoints"),
                "grade": exchange_info.get("Grade"),
                "grade_points_legal": exchange_info.get("GradePointsSplit", {}).get(
                    "Legal"
                ),
                "grade_points_kyc_risk": exchange_info.get("GradePointsSplit", {}).get(
                    "KYCAndTransactionRisk"
                ),
                "grade_points_team": exchange_info.get("GradePointsSplit", {}).get(
                    "Team"
                ),
                "grade_points_data_provision": exchange_info.get(
                    "GradePointsSplit", {}
                ).get("DataProvision"),
                "grade_points_asset_quality": exchange_info.get(
                    "GradePointsSplit", {}
                ).get("AssetQualityAndDiversity"),
                "grade_points_market_quality": exchange_info.get(
                    "GradePointsSplit", {}
                ).get("MarketQuality"),
                "grade_points_security": exchange_info.get("GradePointsSplit", {}).get(
                    "Security"
                ),
                "grade_points_neg_reports_penalty": exchange_info.get(
                    "GradePointsSplit", {}
                ).get("NegativeReportsPenalty"),
                "affiliate_url": exchange_info.get("AffiliateURL"),
                "country": exchange_info.get("Country"),
                "has_orderbook": exchange_info.get("OrderBook"),
                "has_trades": exchange_info.get("Trades"),
                "description": exchange_info.get("Description"),
                "full_address": exchange_info.get("FullAddress"),
                "is_sponsored": exchange_info.get("Sponsored"),
                "is_recommended": exchange_info.get("Recommended"),
                "rating_avg": exchange_info.get("Rating", {}).get("Avg"),
                "rating_total_users": exchange_info.get("Rating", {}).get("TotalUsers"),
                "sort_order": exchange_info.get("SortOrder"),
                "total_volume_24h_usd": exchange_info.get("TOTALVOLUME24H", {}).get(
                    "USD"
                ),
                "created_at": to_mysql_datetime(now_utc),
                "updated_at": to_mysql_datetime(now_utc),
            }
        )
    return exchanges_to_insert


def insert_exchanges_general_data(db_manager, data):
    """Insert transformed general exchange data into the database."""
    if data:
        db_manager.insert_dataframe(data, "market.cc_exchanges_general", replace=True)
        logger.info(f"Successfully ingested {len(data)} general exchange records.")
    else:
        logger.info("No general exchange data to ingest.")


def deduplicate_exchanges_general_table(db_manager):
    """Deduplicate the `market.cc_exchanges_general` table after ingestion."""
    deduplicate_table(
        db_manager, "market.cc_exchanges_general", ["exchange_api_id"], "updated_at"
    )


def ingest_exchanges_general_data():
    """Orchestrates the general exchange data ingestion pipeline."""
    logger.info("Starting general exchange data ingestion process.")
    record_rate_limit_status("ingest_exchanges_general_data", "pre")

    api_key = os.getenv("CCDATA_API_KEY")
    if not api_key:
        logger.error("CCDATA_API_KEY environment variable not set. Exiting.")
        return

    api_client = MinApiGeneralInfoApiClient(api_key=api_key)
    db_manager = None

    try:
        db_manager = DbConnectionManager()
        raw_data = fetch_exchanges_general_data(api_client)
        if raw_data:
            transformed_data = transform_exchanges_general_data(raw_data)
            insert_exchanges_general_data(db_manager, transformed_data)
        else:
            logger.info("No raw data fetched for general exchanges.")
    except Exception as e:
        logger.exception(
            f"An error occurred during general exchange data ingestion: {e}"
        )
    finally:
        if db_manager:
            deduplicate_exchanges_general_table(db_manager)
            db_manager.close_connection()
        logger.info("General exchange data ingestion process finished.")
    record_rate_limit_status("ingest_exchanges_general_data", "post")


if __name__ == "__main__":
    ingest_exchanges_general_data()
