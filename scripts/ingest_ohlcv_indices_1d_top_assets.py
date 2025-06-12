import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from typing import List, Optional
import argparse
import time

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.data_api.indices_ref_rates_api_client import CcdataIndicesRefRatesApiClient
from src.data_api.asset_api_client import CcdataAssetApiClient
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


def get_top_assets(limit: int = 50) -> List[str]:
    """
    Fetches the top assets by 30-day spot quote volume in USD.
    Returns a list of asset symbols.
    """
    asset_client = CcdataAssetApiClient()
    logger.info(
        f"Fetching top {limit} assets by SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD..."
    )
    try:
        response = asset_client.get_top_list_general(
            page_size=limit,
            sort_by="SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD",
            toplist_quote_asset="USD",
        )
        if response and response.get("Data") and response["Data"].get("LIST"):
            assets = [entry["SYMBOL"] for entry in response["Data"]["LIST"]]
            logger.info(f"Found {len(assets)} top assets.")
            return assets
        else:
            logger.warning("No top assets found or API response was empty.")
            return []
    except Exception as e:
        logger.error(f"Error fetching top assets: {e}")
        return []


def get_last_ingested_datetime(
    db: DbConnectionManager, market: str, asset: str
) -> Optional[datetime]:
    """
    Retrieves the latest datetime for a given market and asset from the database.
    """
    query = f"""
        SELECT MAX(datetime)
        FROM market.cc_ohlcv_spot_indices_1d_raw
        WHERE market = %s AND asset = %s;
    """
    try:
        result = db._execute_query(query, params=(market, asset), fetch=True)
        if result and result[0] and result[0][0]:
            # Ensure the datetime object is timezone-aware (UTC)
            return result[0][0].replace(tzinfo=timezone.utc)
        return None
    except Exception as e:
        logger.error(f"Error getting last ingested datetime for {market}-{asset}: {e}")
        return None


def ingest_daily_ohlcv_data_for_asset(
    indices_api_client: CcdataIndicesRefRatesApiClient,
    db: DbConnectionManager,
    market: str,
    asset_symbol: str,
    quote_symbol: str = "USD",
):
    """
    Fetches daily OHLCV data for a specific asset and ingests it into the database.
    Handles backfilling if no data exists.
    """
    instrument = f"{asset_symbol}-{quote_symbol}"
    table_name = "market.cc_ohlcv_spot_indices_1d_raw"

    last_datetime_in_db = get_last_ingested_datetime(db, market, asset_symbol)

    to_ts = int(datetime.now(timezone.utc).timestamp())
    limit = None
    start_from_log_str = None

    if last_datetime_in_db:
        # Get today's date in UTC
        today_utc = datetime.now(timezone.utc).date()
        # Get the date of the last ingested record
        last_ingested_date = last_datetime_in_db.date()

        # If the last ingested date is today or later, no new data is needed
        if last_ingested_date >= today_utc:
            logger.info(
                f"No new data needed for {instrument} on {market}. Last record is up to date (last ingested: {last_ingested_date})."
            )
            return

        # Fetch data from the day after the last ingested data
        start_date_to_fetch = last_datetime_in_db + timedelta(days=1)

        # Calculate the number of days between start_date_to_fetch and now
        delta = datetime.now(timezone.utc) - start_date_to_fetch
        limit = delta.days + 1  # +1 to include the current partial day if applicable

        start_from_log_str = start_date_to_fetch.strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(
            f"Fetching daily OHLCV for {instrument} on {market} from {start_from_log_str} onwards (limit={limit})."
        )
    else:
        # Backfill 2 years if no data exists
        two_years_ago = datetime.now(timezone.utc) - timedelta(days=2 * 365)
        limit = 730  # Approximately 2 years of daily data
        start_from_log_str = two_years_ago.strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(
            f"Backfilling 2 years of daily OHLCV for {instrument} on {market} from {start_from_log_str} onwards (limit={limit})."
        )

    try:
        data = indices_api_client.get_historical_ohlcv(
            time_period="days",
            market=market,
            instrument=instrument,
            to_ts=to_ts,
            limit=limit,
        )

        if data and data.get("Data"):
            records = []
            for entry in data["Data"]:
                # Convert timestamp to UTC datetime object
                entry_datetime = datetime.fromtimestamp(
                    entry["TIMESTAMP"], tz=timezone.utc
                )

                # Only ingest data that is newer than the last_datetime_in_db
                # or if it's the current day (to allow updates for incomplete daily data)
                is_current_day = (
                    entry_datetime.date() == datetime.now(timezone.utc).date()
                )
                if (
                    not last_datetime_in_db
                    or entry_datetime > last_datetime_in_db
                    or is_current_day
                ):
                    records.append(
                        {
                            "unit": entry.get("UNIT"),
                            "datetime": entry_datetime,
                            "type": entry.get("TYPE"),
                            "market": entry.get("MARKET"),
                            "asset": asset_symbol,  # Use the original asset symbol
                            "quote": quote_symbol,  # Use the original quote symbol
                            "open": entry.get("OPEN"),
                            "high": entry.get("HIGH"),
                            "low": entry.get("LOW"),
                            "close": entry.get("CLOSE"),
                            "first_message_timestamp": entry.get(
                                "FIRST_MESSAGE_TIMESTAMP"
                            ),
                            "last_message_timestamp": entry.get(
                                "LAST_MESSAGE_TIMESTAMP"
                            ),
                            "first_message_value": entry.get("FIRST_MESSAGE_VALUE"),
                            "high_message_value": entry.get("HIGH_MESSAGE_VALUE"),
                            "high_message_timestamp": entry.get(
                                "HIGH_MESSAGE_TIMESTAMP"
                            ),
                            "low_message_value": entry.get("LOW_MESSAGE_VALUE"),
                            "low_message_timestamp": entry.get("LOW_MESSAGE_TIMESTAMP"),
                            "last_message_value": entry.get("LAST_MESSAGE_VALUE"),
                            "total_index_updates": entry.get("TOTAL_INDEX_UPDATES"),
                            "volume": entry.get("VOLUME"),
                            "quote_volume": entry.get("QUOTE_VOLUME"),
                            "volume_top_tier": entry.get("VOLUME_TOP_TIER"),
                            "quote_volume_top_tier": entry.get("QUOTE_VOLUME_TOP_TIER"),
                            "volume_direct": entry.get("VOLUME_DIRECT"),
                            "quote_volume_direct": entry.get("QUOTE_VOLUME_DIRECT"),
                            "volume_top_tier_direct": entry.get(
                                "VOLUME_TOP_TIER_DIRECT"
                            ),
                            "quote_volume_top_tier_direct": entry.get(
                                "QUOTE_VOLUME_TOP_TIER_DIRECT"
                            ),
                            "collected_at": datetime.now(timezone.utc),
                        }
                    )
            if records:
                db.insert_dataframe(records, table_name, replace=True)
                logger.info(
                    f"Successfully ingested {len(records)} daily OHLCV records for {instrument} on {market}."
                )
            else:
                logger.info(
                    f"No new daily OHLCV data to ingest for {instrument} on {market}."
                )
        else:
            logger.warning(f"No data received for {instrument} on {market}.")
    except Exception as e:
        logger.error(
            f"Error ingesting daily OHLCV data for {instrument} on {market}: {e}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Ingest daily OHLCV indices data for top assets."
    )
    parser.add_argument(
        "--asset_limit",
        type=int,
        default=50,
        help="Limit the number of top assets to process.",
    )
    parser.add_argument(
        "--market",
        type=str,
        default="cadli",
        help="The index family to obtain data from (e.g., 'cadli').",
    )
    args = parser.parse_args()

    print("Attempting to ingest daily OHLCV indices data for top assets...")
    record_rate_limit_status("ingest_ohlcv_indices_1d_top_assets", "pre")

    db_connection = DbConnectionManager()
    indices_api_client = CcdataIndicesRefRatesApiClient()

    top_assets = get_top_assets(limit=args.asset_limit)
    if not top_assets:
        logger.error("Failed to retrieve top assets. Aborting.")
        return

    # For indices, we use a single market (e.g., 'cadli') and construct instruments like 'BTC-USD'
    market_to_ingest = args.market
    quote_currency = "USD"

    for asset_symbol in top_assets:
        ingest_daily_ohlcv_data_for_asset(
            indices_api_client,
            db_connection,
            market_to_ingest,
            asset_symbol,
            quote_currency,
        )
        time.sleep(0.1)  # Small delay to avoid hitting API rate limits too quickly

    db_connection.close_connection()
    logger.info("Daily OHLCV indices data ingestion for top assets completed.")
    record_rate_limit_status("ingest_ohlcv_indices_1d_top_assets", "post")


if __name__ == "__main__":
    main()
