import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from typing import List, Optional
import argparse
import time

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.db.utils import deduplicate_table, ensure_utc_datetime
from src.data_api.futures_api_client import CcdataFuturesApiClient
from src.rate_limit_tracker import record_rate_limit_status
from src.utils import get_end_of_previous_period

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


def get_all_futures_exchanges(db: DbConnectionManager) -> List[str]:
    """
    Fetches all futures exchanges from the database using a SQL script.
    Returns a list of exchange internal names.
    """
    try:
        query = db._load_sql("get_all_futures_exchanges.sql")
        logger.info("Fetching all futures exchanges from database...")
        results = db._execute_query(query, fetch=True)
        if results:
            exchanges = [row[0] for row in results]
            logger.info(f"Found {len(exchanges)} futures exchanges in database.")
            return exchanges
        else:
            logger.warning("No futures exchanges found in database.")
            return []
    except FileNotFoundError:
        logger.error("SQL script 'get_all_futures_exchanges.sql' not found.")
        return []
    except Exception as e:
        logger.error(f"Error fetching all futures exchanges from database: {e}")
        return []


def get_futures_instruments_from_db(
    db: DbConnectionManager, exchanges: List[str], instrument_statuses: List[str]
) -> List[tuple]:
    """
    Fetches futures instruments for the given exchanges and statuses from the database.
    Returns a list of (exchange_internal_name, mapped_instrument_symbol, last_funding_rate_update_datetime) tuples.
    """
    if not exchanges:
        logger.warning("Exchanges list is empty, returning no futures instruments.")
        return []

    try:
        query = db._load_sql("get_futures_instruments_funding_rate.sql")
        # Convert lists to tuples for SQL IN clause
        params = (tuple(exchanges), tuple(instrument_statuses))

        logger.info(
            f"Fetching futures instruments for exchanges: {exchanges} with statuses: {instrument_statuses}..."
        )
        results = db._execute_query(query, params=params, fetch=True)
        if results:
            # Results are (exchange_internal_name, mapped_instrument_symbol, last_funding_rate_update_datetime, first_funding_rate_update_datetime)
            instruments = []
            for row in results:
                last_update_dt = ensure_utc_datetime(row[2])
                first_update_dt = ensure_utc_datetime(row[3])
                instrument_status = row[4]
                instruments.append((row[0], row[1], last_update_dt, first_update_dt, instrument_status))
            logger.info(f"Found {len(instruments)} futures instruments in database.")
            return instruments
        else:
            logger.warning(
                "No futures instruments found in database for the given criteria."
            )
            return []
    except FileNotFoundError:
        logger.error("SQL script 'get_futures_instruments_funding_rate.sql' not found.")
        return []
    except Exception as e:
        logger.error(f"Error fetching futures instruments from database: {e}")
        return []


def get_last_ingested_datetime(
    db: DbConnectionManager, market: str, mapped_instrument: str
) -> Optional[datetime]:
    """
    Retrieves the latest datetime for a given market and mapped instrument from the database.
    """
    query = f"""
        SELECT MAX(datetime)
        FROM market.cc_futures_funding_rate_ohlc_1h
        WHERE market = %s AND mapped_instrument = %s;
    """
    try:
        result = db._execute_query(
            query, params=(market, mapped_instrument), fetch=True
        )
        if result and result[0] and result[0][0]:
            # Ensure the datetime object is timezone-aware (UTC)
            return result[0][0].replace(tzinfo=timezone.utc)
        return None
    except Exception as e:
        logger.error(
            f"Error getting last ingested datetime for {market}-{mapped_instrument}: {e}"
        )
        return None


def ingest_hourly_funding_rate_data_for_instrument(
    futures_api_client: CcdataFuturesApiClient,
    db: DbConnectionManager,
    market: str,
    mapped_instrument: str,
    last_funding_rate_update_datetime: Optional[datetime],
    first_funding_rate_update_datetime: Optional[datetime],
    instrument_status: str,
):
    """
    Fetches hourly funding rate data for a specific futures instrument and ingests it into the database.
    Handles backfilling and live ingestion by paginating through available data.
    Adjusts to_ts based on last_funding_rate_update_datetime for expired/retired contracts.
    """
    table_name = "market.cc_futures_funding_rate_ohlc_1h"
    
    # API limits
    max_limit_per_call = 2000 # Max limit for hourly funding rate data (approx 83 days)

    last_datetime_in_db = get_last_ingested_datetime(db, market, mapped_instrument)

    now_utc = datetime.now(timezone.utc)
    end_of_previous_hour = get_end_of_previous_period(now_utc, "hours")
    
    # Determine the start datetime for fetching
    if last_datetime_in_db:
        start_datetime_to_fetch = last_datetime_in_db + timedelta(hours=1)
        logger.info(
            f"Continuing ingestion for {mapped_instrument} on {market} from {start_datetime_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')}."
        )
    else:
        # If no data exists, start backfill from the first funding rate update datetime
        if first_funding_rate_update_datetime:
            start_datetime_to_fetch = first_funding_rate_update_datetime
            logger.info(
                f"No existing data for {mapped_instrument} on {market}. Backfilling from first funding rate update datetime: {start_datetime_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            )
        else:
            # Fallback to max_limit_per_call hours ago if first_funding_rate_update_datetime is not available
            two_thousand_hours_ago = now_utc - timedelta(hours=max_limit_per_call)
            start_datetime_to_fetch = two_thousand_hours_ago.replace(minute=0, second=0, microsecond=0)
            logger.info(
                f"No existing data for {mapped_instrument} on {market} and no first funding rate update datetime. Backfilling from {start_datetime_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            )

    # Determine the effective end timestamp for fetching
    # If the instrument is active, use the end of the previous hour. Otherwise, use the last update datetime from the database.
    if instrument_status == "ACTIVE":
        effective_to_ts_datetime = end_of_previous_hour
    else:
        effective_to_ts_datetime = last_funding_rate_update_datetime if last_funding_rate_update_datetime else end_of_previous_hour

    current_to_ts = int(effective_to_ts_datetime.timestamp())
    
    # Loop to paginate and fetch all available data
    while True:
        # Calculate the number of hours between start_datetime_to_fetch and effective_to_ts_datetime
        delta_hours = int((effective_to_ts_datetime - start_datetime_to_fetch).total_seconds() / 3600)
        
        if delta_hours < 0:
            logger.info(f"No new data to fetch for {mapped_instrument} on {market}. Already up to date or future datetime requested.")
            break

        # Determine the limit for the current API call
        limit = min(delta_hours + 1, max_limit_per_call)
        
        # Adjust to_ts for the current batch to ensure we don't fetch beyond the effective_to_ts_datetime
        batch_to_ts = int((start_datetime_to_fetch + timedelta(hours=limit - 1)).timestamp())
        if batch_to_ts > current_to_ts:
            batch_to_ts = current_to_ts

        logger.info(
            f"Fetching batch for {mapped_instrument} on {market} from {start_datetime_to_fetch.strftime('%Y-%m-%d %H:%M:%S')} to {datetime.fromtimestamp(batch_to_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} (limit={limit})."
        )

        try:
            data = futures_api_client.get_futures_historical_funding_rate_ohlc(
                interval="hours",
                market=market,
                instrument=mapped_instrument,
                to_ts=batch_to_ts,
                limit=limit,
            )

            if data and data.get("Data"):
                records = []
                for entry in data["Data"]:
                    entry_datetime = datetime.fromtimestamp(
                        entry["TIMESTAMP"], tz=timezone.utc
                    )
                    
                    # Only ingest data that is newer than the last_datetime_in_db
                    if not last_datetime_in_db or entry_datetime > last_datetime_in_db:
                        records.append(
                            {
                                "datetime": entry_datetime,
                                "market": entry.get("MARKET"),
                                "instrument": entry.get("INSTRUMENT"),
                                "mapped_instrument": entry.get("MAPPED_INSTRUMENT"),
                                "type": entry.get("TYPE"),
                                "index_underlying": entry.get("INDEX_UNDERLYING"),
                                "quote_currency": entry.get("QUOTE_CURRENCY"),
                                "settlement_currency": entry.get("SETTLEMENT_CURRENCY"),
                                "contract_currency": entry.get("CONTRACT_CURRENCY"),
                                "denomination_type": entry.get("DENOMINATION_TYPE"),
                                "interval_ms": entry.get("INTERVAL_MS"),
                                "open_fr": entry.get("OPEN"),
                                "high_fr": entry.get("HIGH"),
                                "low_fr": entry.get("LOW"),
                                "close_fr": entry.get("CLOSE"),
                                "total_funding_rate_updates": entry.get("TOTAL_FUNDING_RATE_UPDATES"),
                                "collected_at": datetime.now(timezone.utc),
                            }
                        )
                if records:
                    db.insert_dataframe(records, table_name, replace=True)
                    logger.info(
                        f"Successfully ingested {len(records)} hourly funding rate records for {mapped_instrument} on {market}."
                    )
                    # Update last_datetime_in_db to the latest timestamp from the current batch
                    last_datetime_in_db = max(records, key=lambda x: x['datetime'])['datetime']
                else:
                    logger.info(
                        f"No new hourly funding rate data to ingest for {mapped_instrument} on {market} in this batch."
                    )
            else:
                logger.warning(f"No data received for {mapped_instrument} on {market} for this batch.")
        except Exception as e:
            logger.error(
                f"Error ingesting hourly funding rate data for {mapped_instrument} on {market}: {e}"
            )
            break # Exit loop on error

        # Prepare for the next batch
        start_datetime_to_fetch = datetime.fromtimestamp(batch_to_ts, tz=timezone.utc) + timedelta(hours=1)
        if start_datetime_to_fetch > now_utc:
            break # All data up to now has been fetched

        # If the last fetched timestamp is the same as the start_datetime_to_fetch, it means no new data was found
        # and we should break to avoid infinite loops.
        if last_datetime_in_db and start_datetime_to_fetch <= last_datetime_in_db:
            logger.info(f"Reached end of available new data for {mapped_instrument} on {market}.")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Ingest hourly funding rate futures data for specified or all exchanges and instruments."
    )
    parser.add_argument(
        "--exchanges",
        type=str,
        default=None,
        help="Comma-separated list of exchange internal names (e.g., binance,bybit). If not provided, all futures exchanges from the database will be used.",
    )
    parser.add_argument(
        "--instruments",
        type=str,
        default=None,
        help="Comma-separated list of mapped instrument symbols (e.g., BTC-USDT-VANILLA-PERPETUAL). If not provided, instruments will be fetched from the database.",
    )
    parser.add_argument(
        "--instrument_status",
        type=str,
        default="ACTIVE",
        help="Comma-separated list of instrument statuses to filter by (e.g., ACTIVE,EXPIRED). Defaults to ACTIVE.",
    )
    args = parser.parse_args()

    print(
        "Attempting to ingest hourly funding rate futures data..."
    )
    record_rate_limit_status("ingest_funding_rate_futures_1h", "pre")

    db_connection = DbConnectionManager()
    futures_api_client = CcdataFuturesApiClient()

    # Determine exchanges to process
    if args.exchanges:
        exchanges_to_process = [e.strip() for e in args.exchanges.split(",")]
        logger.info(f"Processing user-specified exchanges: {exchanges_to_process}")
    else:
        exchanges_to_process = get_all_futures_exchanges(db_connection)
        if not exchanges_to_process:
            logger.error("Failed to retrieve futures exchanges from database. Aborting.")
            return

    # Determine instrument statuses to filter by
    instrument_statuses = [s.strip() for s in args.instrument_status.split(",")]

    # Determine instruments to process
    if args.instruments:
        # If instruments are manually specified, fetch their details from the database,
        # respecting the provided instrument_status filter.
        user_specified_instruments = [instrument.strip() for instrument in args.instruments.split(",")]
        instruments_to_process = []
        for exchange in exchanges_to_process:
            fetched_instruments = get_futures_instruments_from_db(
                db_connection, [exchange], instrument_statuses
            )
            for inst in fetched_instruments:
                if inst[1] in user_specified_instruments:
                    instruments_to_process.append(inst)
        
        if not instruments_to_process:
            logger.error("No user-specified futures instruments found in the database for the given criteria. Aborting.")
            return
        logger.info(f"Processing user-specified instruments: {instruments_to_process}")
    else:
        instruments_to_process = get_futures_instruments_from_db(
            db_connection, exchanges_to_process, instrument_statuses
        )
        if not instruments_to_process:
            logger.error("No futures instruments found for the given criteria. Aborting.")
            return

    for market, mapped_instrument, last_funding_rate_update_datetime, first_funding_rate_update_datetime, instrument_status in instruments_to_process:
        ingest_hourly_funding_rate_data_for_instrument(
            futures_api_client, db_connection, market, mapped_instrument, last_funding_rate_update_datetime, first_funding_rate_update_datetime, instrument_status
        )
        time.sleep(0.1)  # Small delay to avoid hitting API rate limits too quickly

    # Add deduplication step after ingestion
    table_name = "market.cc_futures_funding_rate_ohlc_1h"
    key_cols = ["datetime", "market", "mapped_instrument"]
    latest_col = "collected_at" # Assuming 'collected_at' will be added to the funding rate table for deduplication
    logger.info(f"De-duplicating {table_name}...")
    deduplicate_table(db_connection, table_name, key_cols, latest_col)
    logger.info("De-duplication Complete")

    db_connection.close_connection()
    logger.info("Hourly funding rate futures data ingestion completed.")
    record_rate_limit_status("ingest_funding_rate_futures_1h", "post")


if __name__ == "__main__":
    main()