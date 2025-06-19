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
    Returns a list of (exchange_internal_name, mapped_instrument_symbol) tuples.
    """
    if not exchanges:
        logger.warning("Exchanges list is empty, returning no futures instruments.")
        return []

    try:
        query = db._load_sql("get_futures_instruments.sql")
        # Convert lists to tuples for SQL IN clause
        params = (tuple(exchanges), tuple(instrument_statuses))

        logger.info(
            f"Fetching futures instruments for exchanges: {exchanges} with statuses: {instrument_statuses}..."
        )
        results = db._execute_query(query, params=params, fetch=True)
        if results:
            # Results are (exchange_internal_name, mapped_instrument_symbol, last_trade_datetime, first_trade_datetime)
            instruments = []
            for row in results:
                last_trade_dt = ensure_utc_datetime(row[2])
                first_trade_dt = ensure_utc_datetime(row[3])
                instrument_status = row[4]
                instruments.append((row[0], row[1], last_trade_dt, first_trade_dt, instrument_status))
            logger.info(f"Found {len(instruments)} futures instruments in database.")
            return instruments
        else:
            logger.warning(
                "No futures instruments found in database for the given criteria."
            )
            return []
    except FileNotFoundError:
        logger.error("SQL script 'get_futures_instruments.sql' not found.")
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
        FROM market.cc_futures_ohlcv_1d
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


def ingest_daily_ohlcv_data_for_instrument(
    futures_api_client: CcdataFuturesApiClient,
    db: DbConnectionManager,
    market: str,
    mapped_instrument: str,
    last_trade_datetime: Optional[datetime],
    first_trade_datetime: Optional[datetime],
    instrument_status: str,
):
    """
    Fetches daily OHLCV data for a specific futures instrument and ingests it into the database.
    Handles backfilling and live ingestion by paginating through available data.
    Adjusts to_ts based on last_trade_datetime for retired/expired instruments.
    """
    table_name = "market.cc_futures_ohlcv_1d"
    
    # API limits
    max_limit_per_call = 5000 # Max limit for daily OHLCV data

    last_datetime_in_db = get_last_ingested_datetime(db, market, mapped_instrument)

    today_utc = datetime.now(timezone.utc)
    end_of_previous_day = get_end_of_previous_period(today_utc, "days").date()
    
    # Determine the start date for fetching
    if last_datetime_in_db:
        start_date_to_fetch = last_datetime_in_db + timedelta(days=1)
        logger.info(
            f"Continuing ingestion for {mapped_instrument} on {market} from {start_date_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')}."
        )
    else:
        # If no data exists, start backfill from the first trade datetime
        if first_trade_datetime:
            start_date_to_fetch = first_trade_datetime
            logger.info(
                f"No existing data for {mapped_instrument} on {market}. Backfilling from first trade datetime: {start_date_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            )
        else:
            # Fallback to 2 years ago if first_trade_datetime is not available
            two_years_ago = datetime.now(timezone.utc) - timedelta(days=max_limit_per_call)
            start_date_to_fetch = datetime.combine(two_years_ago.date(), datetime.min.time(), tzinfo=timezone.utc)
            logger.info(
                f"No existing data for {mapped_instrument} on {market} and no first trade datetime. Backfilling from {start_date_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            )

    # Determine the effective end timestamp for fetching
    # If the instrument is active, use the end of the previous day. Otherwise, use the last update datetime from the database.
    if instrument_status == "ACTIVE":
        effective_to_ts_date = end_of_previous_day
    else:
        effective_to_ts_date = last_trade_datetime.date() if last_trade_datetime else end_of_previous_day

    current_to_ts = int(datetime.combine(effective_to_ts_date, datetime.max.time(), tzinfo=timezone.utc).timestamp())
    
    # Loop to paginate and fetch all available data
    while True:
        # Calculate the number of days between start_date_to_fetch and effective_to_ts_date
        delta_days = (effective_to_ts_date - start_date_to_fetch.date()).days
        
        if delta_days < 0:
            logger.info(f"No new data to fetch for {mapped_instrument} on {market}. Already up to date or future date requested.")
            break

        # Determine the limit for the current API call
        limit = min(delta_days + 1, max_limit_per_call)
        
        # Adjust to_ts for the current batch to ensure we don't fetch beyond the effective_to_ts_date
        batch_to_ts = int((start_date_to_fetch + timedelta(days=limit - 1)).timestamp())
        if batch_to_ts > current_to_ts:
            batch_to_ts = current_to_ts

        logger.info(
            f"Fetching batch for {mapped_instrument} on {market} from {start_date_to_fetch.strftime('%Y-%m-%d')} to {datetime.fromtimestamp(batch_to_ts, tz=timezone.utc).strftime('%Y-%m-%d')} (limit={limit})."
        )

        try:
            data = futures_api_client.get_futures_historical_ohlcv(
                interval="days",
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
                    # This check is crucial for preventing re-ingestion of already existing data
                    # when the script is run for live updates, and for ensuring that
                    # backfill mode correctly overwrites or updates existing data.
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
                                "open": entry.get("OPEN"),
                                "high": entry.get("HIGH"),
                                "low": entry.get("LOW"),
                                "close": entry.get("CLOSE"),
                                "number_of_contracts": entry.get("NUMBER_OF_CONTRACTS"),
                                "volume": entry.get("VOLUME"),
                                "quote_volume": entry.get("QUOTE_VOLUME"),
                                "volume_buy": entry.get("VOLUME_BUY"),
                                "quote_volume_buy": entry.get("QUOTE_VOLUME_BUY"),
                                "volume_sell": entry.get("VOLUME_SELL"),
                                "quote_volume_sell": entry.get("QUOTE_VOLUME_SELL"),
                                "volume_unknown": entry.get("VOLUME_UNKNOWN"),
                                "quote_volume_unknown": entry.get("QUOTE_VOLUME_UNKNOWN"),
                                "total_trades": entry.get("TOTAL_TRADES"),
                                "total_trades_buy": entry.get("TOTAL_TRADES_BUY"),
                                "total_trades_sell": entry.get("TOTAL_TRADES_SELL"),
                                "total_trades_unknown": entry.get("TOTAL_TRADES_UNKNOWN"),
                                "first_trade_timestamp": datetime.fromtimestamp(entry.get("FIRST_TRADE_TIMESTAMP"), tz=timezone.utc) if entry.get("FIRST_TRADE_TIMESTAMP") is not None else None,
                                "last_trade_timestamp": datetime.fromtimestamp(entry.get("LAST_TRADE_TIMESTAMP"), tz=timezone.utc) if entry.get("LAST_TRADE_TIMESTAMP") is not None else None,
                                "first_trade_price": entry.get("FIRST_TRADE_PRICE"),
                                "high_trade_price": entry.get("HIGH_TRADE_PRICE"),
                                "high_trade_timestamp": datetime.fromtimestamp(entry.get("HIGH_TRADE_TIMESTAMP"), tz=timezone.utc) if entry.get("HIGH_TRADE_TIMESTAMP") is not None else None,
                                "low_trade_price": entry.get("LOW_TRADE_PRICE"),
                                "low_trade_timestamp": datetime.fromtimestamp(entry.get("LOW_TRADE_TIMESTAMP"), tz=timezone.utc) if entry.get("LOW_TRADE_TIMESTAMP") is not None else None,
                                "last_trade_price": entry.get("LAST_TRADE_PRICE"),
                                "collected_at": datetime.now(timezone.utc),
                            }
                        )
                if records:
                    db.insert_dataframe(records, table_name, replace=True)
                    logger.info(
                        f"Successfully ingested {len(records)} daily OHLCV records for {mapped_instrument} on {market}."
                    )
                    # Update last_datetime_in_db to the latest timestamp from the current batch
                    last_datetime_in_db = max(records, key=lambda x: x['datetime'])['datetime']
                else:
                    logger.info(
                        f"No new daily OHLCV data to ingest for {mapped_instrument} on {market} in this batch."
                    )
            else:
                logger.warning(f"No data received for {mapped_instrument} on {market} for this batch.")
        except Exception as e:
            logger.error(
                f"Error ingesting daily OHLCV data for {mapped_instrument} on {market}: {e}"
            )
            break # Exit loop on error

        # Prepare for the next batch
        start_date_to_fetch = datetime.fromtimestamp(batch_to_ts, tz=timezone.utc) + timedelta(days=1)
        if start_date_to_fetch > today_utc:
            break # All data up to today has been fetched

        # If the last fetched timestamp is the same as the start_date_to_fetch, it means no new data was found
        # and we should break to avoid infinite loops.
        if last_datetime_in_db and start_date_to_fetch.date() <= last_datetime_in_db.date():
            logger.info(f"Reached end of available new data for {mapped_instrument} on {market}.")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Ingest daily OHLCV futures data for specified or all exchanges and instruments."
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
        "Attempting to ingest daily OHLCV futures data..."
    )
    record_rate_limit_status("ingest_ohlcv_futures_1d", "pre")

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

    for market, mapped_instrument, last_trade_datetime, first_trade_datetime, instrument_status in instruments_to_process:
        ingest_daily_ohlcv_data_for_instrument(
            futures_api_client, db_connection, market, mapped_instrument, last_trade_datetime, first_trade_datetime, instrument_status
        )
        time.sleep(0.1)  # Small delay to avoid hitting API rate limits too quickly

    # Add deduplication step after ingestion
    table_name = "market.cc_futures_ohlcv_1d"
    key_cols = ["datetime", "market", "mapped_instrument"]
    # Assuming 'collected_at' will be added to the futures OHLCV table for deduplication
    latest_col = "collected_at"
    logger.info(f"De-duplicating {table_name}...")
    deduplicate_table(db_connection, table_name, key_cols, latest_col)
    logger.info("De-duplication Complete")

    db_connection.close_connection()
    logger.info("Daily OHLCV futures data ingestion completed.")
    record_rate_limit_status("ingest_ohlcv_futures_1d", "post")


if __name__ == "__main__":
    main()