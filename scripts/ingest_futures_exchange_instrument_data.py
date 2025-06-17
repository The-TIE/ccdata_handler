import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from src.data_api.futures_api_client import CcdataFuturesApiClient
from src.db.connection import DbConnectionManager
from src.logger_config import setup_logger
from src.db.utils import to_mysql_datetime, deduplicate_table
from src.rate_limit_tracker import record_rate_limit_status
import polars as pl

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


def fetch_futures_exchange_instrument_data(futures_client):
    """Fetch all futures market instrument data from the API."""
    logger.info("Fetching futures market instrument data.")
    response = futures_client.get_futures_markets_instruments()
    if not response or response.get("Response") == "Error":
        logger.error(
            f"Failed to retrieve futures market instrument data: {response.get('Message', 'Unknown error')}"
        )
        return None
    logger.info("Successfully fetched futures market instrument data.")
    return response.get("Data", {})


def transform_futures_exchange_instrument_data(raw_data):
    """
    Transforms raw futures exchange and instrument data into structured formats
    for `market.cc_exchanges_futures_details` and `market.cc_instruments_futures` tables.
    """
    now_utc = datetime.now(timezone.utc)
    exchange_details_to_insert = []
    instruments_to_insert = []

    for exchange_internal_name, exchange_info in raw_data.items():
        # Data for market.cc_exchanges_futures_details
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
                "total_trades_exchange_level": exchange_info.get("TOTAL_TRADES_FUTURES"),
                "total_open_interest_updates": exchange_info.get("TOTAL_OPEN_INTEREST_UPDATES"),
                "total_funding_rate_updates": exchange_info.get("TOTAL_FUNDING_RATE_UPDATES"),
                "has_orderbook_l2_snapshots": exchange_info.get(
                    "HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED"
                ),
                "api_data_retrieved_datetime": now_utc.isoformat(),
                "created_at": now_utc.isoformat(),
                "updated_at": now_utc.isoformat(),
            }
        )

        # Data for market.cc_instruments_futures
        for mapped_instrument_symbol, instrument_info in exchange_info.get(
            "instruments", {}
        ).items():
            instrument_mapping = instrument_info.get("INSTRUMENT_MAPPING", {})

            first_trade_ts = instrument_info.get("FIRST_TRADE_FUTURES_TIMESTAMP")
            last_trade_ts = instrument_info.get("LAST_TRADE_FUTURES_TIMESTAMP")
            mapping_created_ts = instrument_mapping.get("CREATED_ON")
            first_funding_rate_ts = instrument_info.get("FIRST_FUNDING_RATE_UPDATE_TIMESTAMP")
            last_funding_rate_ts = instrument_info.get("LAST_FUNDING_RATE_UPDATE_TIMESTAMP")
            first_open_interest_ts = instrument_info.get("FIRST_OPEN_INTEREST_UPDATE_TIMESTAMP")
            last_open_interest_ts = instrument_info.get("LAST_OPEN_INTEREST_UPDATE_TIMESTAMP")
            contract_expiration_ts = instrument_info.get("CONTRACT_EXPIRATION_TS")

            instruments_to_insert.append(
                {
                    "exchange_internal_name": exchange_internal_name,
                    "mapped_instrument_symbol": mapped_instrument_symbol,
                    "api_instrument_type": instrument_info.get("TYPE"),
                    "instrument_status_on_exchange": instrument_info.get(
                        "INSTRUMENT_STATUS"
                    ),
                    "exchange_instrument_symbol_raw": instrument_info.get("INSTRUMENT"),
                    "index_underlying_symbol": instrument_mapping.get("INDEX_UNDERLYING"),
                    "index_underlying_id": instrument_mapping.get("INDEX_UNDERLYING_ID"),
                    "quote_currency_symbol": instrument_mapping.get("QUOTE_CURRENCY"),
                    "quote_currency_id": instrument_mapping.get("QUOTE_CURRENCY_ID"),
                    "settlement_currency_symbol": instrument_mapping.get("SETTLEMENT_CURRENCY"),
                    "settlement_currency_id": instrument_mapping.get("SETTLEMENT_CURRENCY_ID"),
                    "contract_currency_symbol": instrument_mapping.get("CONTRACT_CURRENCY"),
                    "contract_currency_id": instrument_mapping.get("CONTRACT_CURRENCY_ID"),
                    "denomination_type": instrument_mapping.get("DENOMINATION_TYPE"),
                    "transform_function": instrument_mapping.get("TRANSFORM_FUNCTION"),
                    "instrument_mapping_created_datetime": (
                        (datetime.fromtimestamp(mapping_created_ts, tz=timezone.utc).isoformat() if mapping_created_ts else None)
                    ),
                    "has_trades": instrument_info.get("HAS_TRADES_FUTURES"),
                    "first_trade_datetime": (
                        (datetime.fromtimestamp(first_trade_ts, tz=timezone.utc).isoformat() if first_trade_ts else None)
                    ),
                    "last_trade_datetime": (
                        (datetime.fromtimestamp(last_trade_ts, tz=timezone.utc).isoformat() if last_trade_ts else None)
                    ),
                    "total_trades_instrument_level": instrument_info.get(
                        "TOTAL_TRADES_FUTURES"
                    ),
                    "has_funding_rate_updates": instrument_info.get("HAS_FUNDING_RATE_UPDATES"),
                    "first_funding_rate_update_datetime": (
                        (datetime.fromtimestamp(first_funding_rate_ts, tz=timezone.utc).isoformat() if first_funding_rate_ts else None)
                    ),
                    "last_funding_rate_update_datetime": (
                        (datetime.fromtimestamp(last_funding_rate_ts, tz=timezone.utc).isoformat() if last_funding_rate_ts else None)
                    ),
                    "total_funding_rate_updates": instrument_info.get("TOTAL_FUNDING_RATE_UPDATES"),
                     "has_open_interest_updates": instrument_info.get("HAS_OPEN_INTEREST_UPDATES"),
                    "first_open_interest_update_datetime": (
                        (datetime.fromtimestamp(first_open_interest_ts, tz=timezone.utc).isoformat() if first_open_interest_ts else None)
                    ),
                    "last_open_interest_update_datetime": (
                        (datetime.fromtimestamp(last_open_interest_ts, tz=timezone.utc).isoformat() if last_open_interest_ts else None)
                    ),
                    "total_open_interest_updates": instrument_info.get("TOTAL_OPEN_INTEREST_UPDATES"),
                    "contract_expiration_datetime": (
                        (datetime.fromtimestamp(contract_expiration_ts, tz=timezone.utc).isoformat() if contract_expiration_ts else None)
                    ),
                    "created_at": now_utc.isoformat(),
                    "updated_at": now_utc.isoformat(),
                }
            )
    return {
        "exchange_details": exchange_details_to_insert,
        "instruments": instruments_to_insert,
    }


def insert_futures_exchange_instrument_data(db_manager, transformed_data):
    """Inserts transformed futures exchange and instrument data into the database."""
    # Define schema for futures exchange details
    exchange_details_schema = {
        "exchange_internal_name": pl.Utf8,
        "api_exchange_type": pl.Utf8,
        "exchange_status": pl.Utf8,
        "mapped_instruments_total": pl.Int64,
        "unmapped_instruments_total": pl.Int64,
        "instruments_active_count": pl.Int64,
        "instruments_ignored_count": pl.Int64,
        "instruments_retired_count": pl.Int64,
        "instruments_expired_count": pl.Int64,
        "instruments_retired_unmapped_count": pl.Int64,
        "total_trades_exchange_level": pl.Int64,
        "total_open_interest_updates": pl.Int64,
        "total_funding_rate_updates": pl.Int64,
        "has_orderbook_l2_snapshots": pl.Boolean,
        "api_data_retrieved_datetime": pl.Utf8, # Changed to Utf8 as we are storing ISO strings
        "created_at": pl.Utf8, # Changed to Utf8 as we are storing ISO strings
        "updated_at": pl.Utf8, # Changed to Utf8 as we are storing ISO strings
    }

    if transformed_data["exchange_details"]:
        db_manager.insert_dataframe(
            transformed_data["exchange_details"],
            "market.cc_exchanges_futures_details",
            replace=True,
            schema=exchange_details_schema,
        )
        logger.info(
            f"Successfully ingested {len(transformed_data['exchange_details'])} exchange futures details records."
        )
    else:
        logger.info("No exchange futures details data to ingest.")

    # Define schema for futures instruments
    instruments_schema = {
        "exchange_internal_name": pl.Utf8,
        "mapped_instrument_symbol": pl.Utf8,
        "api_instrument_type": pl.Utf8,
        "instrument_status_on_exchange": pl.Utf8,
        "exchange_instrument_symbol_raw": pl.Utf8,
        "index_underlying_symbol": pl.Utf8,
        "index_underlying_id": pl.Int64,
        "quote_currency_symbol": pl.Utf8,
        "quote_currency_id": pl.Int64,
        "settlement_currency_symbol": pl.Utf8,
        "settlement_currency_id": pl.Int64,
        "contract_currency_symbol": pl.Utf8,
        "contract_currency_id": pl.Int64,
        "denomination_type": pl.Utf8,
        "transform_function": pl.Utf8,
        "instrument_mapping_created_datetime": pl.Utf8, # Changed to Utf8
        "has_trades": pl.Boolean,
        "first_trade_datetime": pl.Utf8, # Changed to Utf8
        "last_trade_datetime": pl.Utf8, # Changed to Utf8
        "total_trades_instrument_level": pl.Int64,
        "has_funding_rate_updates": pl.Boolean,
        "first_funding_rate_update_datetime": pl.Utf8, # Changed to Utf8
        "last_funding_rate_update_datetime": pl.Utf8, # Changed to Utf8
        "total_funding_rate_updates": pl.Int64,
        "has_open_interest_updates": pl.Boolean,
        "first_open_interest_update_datetime": pl.Utf8, # Changed to Utf8
        "last_open_interest_update_datetime": pl.Utf8, # Changed to Utf8
        "total_open_interest_updates": pl.Int64,
        "contract_expiration_datetime": pl.Utf8, # Changed to Utf8
        "created_at": pl.Utf8, # Changed to Utf8
        "updated_at": pl.Utf8, # Changed to Utf8
    }

    if transformed_data["instruments"]:
        db_manager.insert_dataframe(
            transformed_data["instruments"],
            "market.cc_instruments_futures",
            replace=True,
            schema=instruments_schema,
        )
        logger.info(
            f"Successfully ingested {len(transformed_data['instruments'])} futures instrument records."
        )
    else:
        logger.info("No futures instrument data to ingest.")


def deduplicate_futures_exchange_instrument_tables(db_manager):
    """Deduplicate relevant tables after ingestion."""
    deduplicate_table(
        db_manager,
        "market.cc_exchanges_futures_details",
        ["exchange_internal_name"],
        "updated_at",
    )
    deduplicate_table(
        db_manager,
        "market.cc_instruments_futures",
        ["exchange_internal_name", "mapped_instrument_symbol"],
        "updated_at",
    )


def ingest_futures_exchange_instrument_data():
    """Orchestrates the futures exchange and instrument data ingestion pipeline."""
    logger.info("Starting futures exchange and instrument data ingestion process.")
    record_rate_limit_status("ingest_futures_exchange_instrument_data", "pre")

    api_key = os.getenv("CCDATA_API_KEY")
    if not api_key:
        logger.error("CCDATA_API_KEY environment variable not set. Exiting.")
        return

    futures_client = CcdataFuturesApiClient(api_key=api_key)
    db_manager = None

    try:
        db_manager = DbConnectionManager()
        raw_data = fetch_futures_exchange_instrument_data(futures_client)
        if raw_data:
            transformed_data = transform_futures_exchange_instrument_data(raw_data)
            insert_futures_exchange_instrument_data(db_manager, transformed_data)
        else:
            logger.info("No raw data fetched for futures exchange and instruments.")
    except Exception as e:
        logger.exception(
            f"An error occurred during futures exchange and instrument data ingestion: {e}"
        )
    finally:
        if db_manager:
            deduplicate_futures_exchange_instrument_tables(db_manager)
            db_manager.close_connection()
        logger.info("Futures exchange and instrument data ingestion process finished.")
    record_rate_limit_status("ingest_futures_exchange_instrument_data", "post")


if __name__ == "__main__":
    ingest_futures_exchange_instrument_data()