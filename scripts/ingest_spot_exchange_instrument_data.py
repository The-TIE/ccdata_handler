import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from src.data_api.spot_api_client import CcdataSpotApiClient
from src.db.connection import DbConnectionManager
from src.logger_config import setup_logger
from src.db.utils import to_mysql_datetime, deduplicate_table

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


def fetch_spot_exchange_instrument_data(spot_client):
    """Fetch all spot market instrument data from the API."""
    logger.info("Fetching spot market instrument data.")
    response = spot_client.get_spot_market_instruments()
    if not response or response.get("Response") == "Error":
        logger.error(
            f"Failed to retrieve spot market instrument data: {response.get('Message', 'Unknown error')}"
        )
        return None
    logger.info("Successfully fetched spot market instrument data.")
    return response.get("Data", {})


def transform_spot_exchange_instrument_data(raw_data):
    """
    Transforms raw spot exchange and instrument data into structured formats
    for `market.cc_exchange_spot_details` and `market.cc_instruments_spot` tables.
    """
    now_utc = datetime.now(timezone.utc)
    exchange_details_to_insert = []
    instruments_to_insert = []

    for exchange_internal_name, exchange_info in raw_data.items():
        # Data for market.cc_exchange_spot_details
        exchange_details_to_insert.append(
            {
                "exchange_internal_name": exchange_internal_name,
                "api_exchange_type": exchange_info.get("TYPE"),
                "exchange_status": exchange_info.get("EXCHANGE_STATUS"),
                "mapped_instruments_total": exchange_info.get(
                    "MAPPED_INSTRUMENTS_TOTAL"
                ),
                "unmapped_instruments_total": exchange_info.get(
                    "UNMAPPED_INSTRUMENTS_TOTAL"
                ),
                "instruments_active_count": exchange_info.get(
                    "INSTRUMENT_STATUS", {}
                ).get("ACTIVE"),
                "instruments_ignored_count": exchange_info.get(
                    "INSTRUMENT_STATUS", {}
                ).get("IGNORED"),
                "instruments_retired_count": exchange_info.get(
                    "INSTRUMENT_STATUS", {}
                ).get("RETIRED"),
                "instruments_expired_count": exchange_info.get(
                    "INSTRUMENT_STATUS", {}
                ).get("EXPIRED"),
                "instruments_retired_unmapped_count": exchange_info.get(
                    "INSTRUMENT_STATUS", {}
                ).get("RETIRED_UNMAPPED"),
                "total_trades_exchange_level": exchange_info.get("TOTAL_TRADES_SPOT"),
                "has_orderbook_l2_snapshots": exchange_info.get(
                    "HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED"
                ),
                "api_data_retrieved_datetime": to_mysql_datetime(now_utc),
                "created_at": to_mysql_datetime(now_utc),
                "updated_at": to_mysql_datetime(now_utc),
            }
        )

        # Data for market.cc_instruments_spot
        for mapped_instrument_symbol, instrument_info in exchange_info.get(
            "instruments", {}
        ).items():
            instrument_mapping = instrument_info.get("INSTRUMENT_MAPPING", {})

            first_trade_ts = instrument_info.get("FIRST_TRADE_SPOT_TIMESTAMP")
            last_trade_ts = instrument_info.get("LAST_TRADE_SPOT_TIMESTAMP")
            mapping_created_ts = instrument_mapping.get("CREATED_ON")

            instruments_to_insert.append(
                {
                    "exchange_internal_name": exchange_internal_name,
                    "mapped_instrument_symbol": mapped_instrument_symbol,
                    "api_instrument_type": instrument_info.get("TYPE"),
                    "instrument_status_on_exchange": instrument_info.get(
                        "INSTRUMENT_STATUS"
                    ),
                    "exchange_instrument_symbol_raw": instrument_info.get("INSTRUMENT"),
                    "base_asset_symbol": instrument_mapping.get("BASE"),
                    "base_asset_id": instrument_mapping.get("BASE_ID"),
                    "quote_asset_symbol": instrument_mapping.get("QUOTE"),
                    "quote_asset_id": instrument_mapping.get("QUOTE_ID"),
                    "transform_function": instrument_mapping.get("TRANSFORM_FUNCTION"),
                    "instrument_mapping_created_datetime": (
                        to_mysql_datetime(
                            datetime.fromtimestamp(mapping_created_ts, tz=timezone.utc)
                        )
                        if mapping_created_ts
                        else None
                    ),
                    "has_trades": instrument_info.get("HAS_TRADES_SPOT"),
                    "first_trade_datetime": (
                        to_mysql_datetime(
                            datetime.fromtimestamp(first_trade_ts, tz=timezone.utc)
                        )
                        if first_trade_ts
                        else None
                    ),
                    "last_trade_datetime": (
                        to_mysql_datetime(
                            datetime.fromtimestamp(last_trade_ts, tz=timezone.utc)
                        )
                        if last_trade_ts
                        else None
                    ),
                    "total_trades_instrument_level": instrument_info.get(
                        "TOTAL_TRADES_SPOT"
                    ),
                    "created_at": to_mysql_datetime(now_utc),
                    "updated_at": to_mysql_datetime(now_utc),
                }
            )
    return {
        "exchange_details": exchange_details_to_insert,
        "instruments": instruments_to_insert,
    }


def insert_spot_exchange_instrument_data(db_manager, transformed_data):
    """Inserts transformed spot exchange and instrument data into the database."""
    if transformed_data["exchange_details"]:
        db_manager.insert_dataframe(
            transformed_data["exchange_details"],
            "market.cc_exchange_spot_details",
            replace=True,
        )
        logger.info(
            f"Successfully ingested {len(transformed_data['exchange_details'])} exchange spot details records."
        )
    else:
        logger.info("No exchange spot details data to ingest.")

    if transformed_data["instruments"]:
        db_manager.insert_dataframe(
            transformed_data["instruments"], "market.cc_instruments_spot", replace=True
        )
        logger.info(
            f"Successfully ingested {len(transformed_data['instruments'])} spot instrument records."
        )
    else:
        logger.info("No spot instrument data to ingest.")


def deduplicate_spot_exchange_instrument_tables(db_manager):
    """Deduplicate relevant tables after ingestion."""
    deduplicate_table(
        db_manager,
        "market.cc_exchange_spot_details",
        ["exchange_internal_name"],
        "updated_at",
    )
    deduplicate_table(
        db_manager,
        "market.cc_instruments_spot",
        ["exchange_internal_name", "mapped_instrument_symbol"],
        "updated_at",
    )


def ingest_spot_exchange_instrument_data():
    """Orchestrates the spot exchange and instrument data ingestion pipeline."""
    logger.info("Starting spot exchange and instrument data ingestion process.")

    api_key = os.getenv("CCDATA_API_KEY")
    if not api_key:
        logger.error("CCDATA_API_KEY environment variable not set. Exiting.")
        return

    spot_client = CcdataSpotApiClient(api_key=api_key)
    db_manager = None

    try:
        db_manager = DbConnectionManager()
        raw_data = fetch_spot_exchange_instrument_data(spot_client)
        if raw_data:
            transformed_data = transform_spot_exchange_instrument_data(raw_data)
            insert_spot_exchange_instrument_data(db_manager, transformed_data)
        else:
            logger.info("No raw data fetched for spot exchange and instruments.")
    except Exception as e:
        logger.exception(
            f"An error occurred during spot exchange and instrument data ingestion: {e}"
        )
    finally:
        if db_manager:
            deduplicate_spot_exchange_instrument_tables(db_manager)
            db_manager.close_connection()
        logger.info("Spot exchange and instrument data ingestion process finished.")


if __name__ == "__main__":
    ingest_spot_exchange_instrument_data()
