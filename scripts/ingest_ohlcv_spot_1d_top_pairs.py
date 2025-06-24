import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from typing import List, Optional
import argparse
import time

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.db.utils import deduplicate_table, to_mysql_datetime
from src.data_api.spot_api_client import CcdataSpotApiClient
from src.data_api.asset_api_client import CcdataAssetApiClient
from src.min_api.general_info_api_client import MinApiGeneralInfoApiClient
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


def get_top_assets(db: DbConnectionManager, limit: int = 50) -> List[str]:
    """
    Fetches the top assets by 30-day spot quote volume in USD from the database using a SQL script.
    Returns a list of asset symbols.
    """
    try:
        query = db._load_sql("get_top_assets.sql")
        logger.info(
            f"Fetching top {limit} assets by SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD from database..."
        )
        # Pass limit as a parameter to the SQL query
        results = db._execute_query(query, params=(limit,), fetch=True)
        if results:
            assets = [row[0] for row in results]
            logger.info(f"Found {len(assets)} top assets in database.")
            return assets
        else:
            logger.warning("No top assets found in database.")
            return []
    except FileNotFoundError:
        logger.error("SQL script 'get_top_assets.sql' not found.")
        return []
    except Exception as e:
        logger.error(f"Error fetching top assets from database: {e}")
        return []


def get_qualified_exchanges_from_db(db: DbConnectionManager) -> List[str]:
    """
    Fetches exchanges rated 'BB' or better from the database using a SQL script.
    Returns a list of exchange internal names.
    """
    try:
        query = db._load_sql("get_qualified_exchanges.sql")
        logger.info("Fetching qualified exchanges from database...")
        results = db._execute_query(query, fetch=True)
        if results:
            exchanges = [row[0] for row in results]
            logger.info(f"Found {len(exchanges)} qualified exchanges in database.")
            return exchanges
        else:
            logger.warning("No qualified exchanges found in database.")
            return []
    except FileNotFoundError:
        logger.error("SQL script 'get_qualified_exchanges.sql' not found.")
        return []
    except Exception as e:
        logger.error(f"Error fetching qualified exchanges from database: {e}")
        return []


def get_trading_pairs_from_db(
    db: DbConnectionManager, assets: List[str], exchanges: List[str]
) -> List[tuple]:
    """
    Fetches trading pairs for the given assets on the specified exchanges from the database using a SQL script.
    Returns a list of (exchange, base_symbol, quote_symbol) tuples.
    """
    # Ensure the list of assets and exchanges is not empty for the query
    if not assets or not exchanges:
        logger.warning("Assets or exchanges list is empty, returning no trading pairs.")
        return []

    try:
        query = db._load_sql("get_trading_pairs.sql")
        # Pass exchanges and assets as a tuple for the IN clauses
        params = (exchanges, assets)

        logger.info(
            "Fetching trading pairs for top assets on qualified exchanges from database..."
        )
        results = db._execute_query(query, params=params, fetch=True)
        if results:
            # Results are already in the desired (exchange, base_symbol, quote_symbol) format
            trading_pairs = [(row[0], row[1], row[2]) for row in results]
            logger.info(f"Found {len(trading_pairs)} trading pairs in database.")
            return trading_pairs
        else:
            logger.warning("No trading pairs found in database for the given criteria.")
            return []
    except FileNotFoundError:
        logger.error("SQL script 'get_trading_pairs.sql' not found.")
        return []
    except Exception as e:
        logger.error(f"Error fetching trading pairs from database: {e}")
        return []


def get_last_ingested_datetime(
    db: DbConnectionManager, exchange: str, symbol_unmapped: str
) -> Optional[datetime]:
    """
    Retrieves the latest datetime for a given exchange and unmapped symbol from the database.
    """
    query = f"""
        SELECT MAX(datetime)
        FROM market.cc_ohlcv_spot_1d_raw
        WHERE exchange = %s AND symbol = %s;
    """
    try:
        result = db._execute_query(
            query, params=(exchange, symbol_unmapped), fetch=True
        )
        if result and result[0] and result[0][0]:
            # Ensure the datetime object is timezone-aware (UTC)
            return result[0][0].replace(tzinfo=timezone.utc)
        return None
    except Exception as e:
        logger.error(
            f"Error getting last ingested datetime for {exchange}-{symbol_unmapped}: {e}"
        )
        return None


def ingest_daily_ohlcv_data_for_pair(
    spot_api_client: CcdataSpotApiClient,
    db: DbConnectionManager,
    exchange: str,
    base_symbol: str,
    quote_symbol: str,
):
    """
    Fetches daily OHLCV data for a specific pair and ingests it into the database.
    Handles backfilling if no data exists.
    """
    instrument = f"{base_symbol}-{quote_symbol}"
    table_name = "market.cc_ohlcv_spot_1d_raw"

    last_datetime_in_db = get_last_ingested_datetime(db, exchange, instrument)

    today_utc_date = datetime.now(timezone.utc).date()
    yesterday_utc_date = today_utc_date - timedelta(days=1)
    to_ts = int(
        datetime.combine(
            yesterday_utc_date, datetime.max.time(), tzinfo=timezone.utc
        ).timestamp()
    )
    limit = None
    start_from_log_str = None

    if last_datetime_in_db:
        last_ingested_date = last_datetime_in_db.date()

        if last_ingested_date >= today_utc_date:
            logger.info(
                f"No new data needed for {instrument} on {exchange}. Last record is up to date (last ingested: {last_ingested_date})."
            )
            return

        if last_ingested_date == yesterday_utc_date:
            start_date_to_fetch = last_datetime_in_db
            limit = 1
        else:
            start_date_to_fetch = last_datetime_in_db + timedelta(days=1)
            delta = yesterday_utc_date - start_date_to_fetch.date()
            limit = delta.days + 1

        start_from_log_str = start_date_to_fetch.strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(
            f"Fetching daily OHLCV for {instrument} on {exchange} from {start_from_log_str} to {yesterday_utc_date.strftime('%Y-%m-%d')} (limit={limit})."
        )
    else:
        # Backfill 2 years if no data exists
        two_years_ago = datetime.now(timezone.utc) - timedelta(days=5000)
        limit = (yesterday_utc_date - two_years_ago.date()).days
        start_from_log_str = two_years_ago.strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(
            f"Backfilling 2 years of daily OHLCV for {instrument} on {exchange} from {start_from_log_str} to {yesterday_utc_date.strftime('%Y-%m-%d')} (limit={limit})."
        )

    try:
        data = spot_api_client.get_historical_ohlcv(
            interval="days",
            market=exchange,
            instrument=instrument,
            to_ts=to_ts,
            limit=limit,  # Limit is only used for backfill, otherwise it's None
        )

        if data and data.get("Data"):
            records = []
            for entry in data["Data"]:
                # Convert timestamp to UTC datetime object
                entry_datetime = datetime.fromtimestamp(
                    entry["TIMESTAMP"], tz=timezone.utc
                )

                # Only ingest data that is newer than the last_datetime_in_db
                if not last_datetime_in_db or entry_datetime > last_datetime_in_db:
                    records.append(
                        {
                            "datetime": entry_datetime,
                            "exchange": entry.get("MARKET"),
                            "symbol_unmapped": entry.get("INSTRUMENT"),
                            "symbol": entry.get("MAPPED_INSTRUMENT"),
                            "base": entry.get("BASE"),
                            "quote": entry.get("QUOTE"),
                            "base_id": entry.get("BASE_ID"),
                            "quote_id": entry.get("QUOTE_ID"),
                            "transform_function": entry.get("TRANSFORM_FUNCTION"),
                            "open": entry.get("OPEN"),
                            "high": entry.get("HIGH"),
                            "low": entry.get("LOW"),
                            "close": entry.get("CLOSE"),
                            "first_trade_timestamp": (
                                datetime.fromtimestamp(
                                    entry.get("FIRST_TRADE_TIMESTAMP"), tz=timezone.utc
                                )
                                if entry.get("FIRST_TRADE_TIMESTAMP") is not None
                                else None
                            ),  # Convert to DATETIME
                            "last_trade_timestamp": (
                                datetime.fromtimestamp(
                                    entry.get("LAST_TRADE_TIMESTAMP"), tz=timezone.utc
                                )
                                if entry.get("LAST_TRADE_TIMESTAMP") is not None
                                else None
                            ),  # Convert to DATETIME
                            "first_trade_price": entry.get("FIRST_TRADE_PRICE"),
                            "high_trade_price": entry.get("HIGH_TRADE_PRICE"),
                            "high_trade_timestamp": (
                                datetime.fromtimestamp(
                                    entry.get("HIGH_TRADE_TIMESTAMP"), tz=timezone.utc
                                )
                                if entry.get("HIGH_TRADE_TIMESTAMP") is not None
                                else None
                            ),  # Convert to DATETIME
                            "low_trade_price": entry.get("LOW_TRADE_PRICE"),
                            "low_trade_timestamp": (
                                datetime.fromtimestamp(
                                    entry.get("LOW_TRADE_TIMESTAMP"), tz=timezone.utc
                                )
                                if entry.get("LOW_TRADE_TIMESTAMP") is not None
                                else None
                            ),  # Convert to DATETIME
                            "last_trade_price": entry.get("LAST_TRADE_PRICE"),
                            "total_trades": entry.get("TOTAL_TRADES"),
                            "total_trades_buy": entry.get("TOTAL_TRADES_BUY"),
                            "total_trades_sell": entry.get("TOTAL_TRADES_SELL"),
                            "total_trades_unknown": entry.get("TOTAL_TRADES_UNKNOWN"),
                            "volume": entry.get("VOLUME"),
                            "quote_volume": entry.get("QUOTE_VOLUME"),
                            "volume_buy": entry.get("VOLUME_BUY"),
                            "quote_volume_buy": entry.get("QUOTE_VOLUME_BUY"),
                            "volume_sell": entry.get("VOLUME_SELL"),
                            "quote_volume_sell": entry.get("QUOTE_VOLUME_SELL"),
                            "volume_unknown": entry.get("VOLUME_UNKNOWN"),
                            "quote_volume_unknown": entry.get("QUOTE_VOLUME_UNKNOWN"),
                            "collected_at": datetime.now(timezone.utc),
                        }
                    )
            if records:
                db.insert_dataframe(records, table_name, replace=True)
                logger.info(
                    f"Successfully ingested {len(records)} daily OHLCV records for {instrument} on {exchange}."
                )
            else:
                logger.info(
                    f"No new daily OHLCV data to ingest for {instrument} on {exchange}."
                )
        else:
            logger.warning(f"No data received for {instrument} on {exchange}.")
    except Exception as e:
        logger.error(
            f"Error ingesting daily OHLCV data for {instrument} on {exchange}: {e}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Ingest daily OHLCV spot data for top assets on qualified exchanges."
    )
    parser.add_argument(
        "--asset_limit",
        type=int,
        default=50,
        help="Limit the number of top assets to process.",
    )
    parser.add_argument(
        "--exchange_limit",
        type=int,
        default=None,
        help="Limit the number of qualified exchanges to process for testing.",
    )
    parser.add_argument(
        "--pair_limit",
        type=int,
        default=None,
        help="Limit the number of trading pairs to process for testing.",
    )
    args = parser.parse_args()

    print(
        "Attempting to ingest daily OHLCV spot data for top assets on qualified exchanges..."
    )
    record_rate_limit_status("ingest_ohlcv_spot_1d_top_pairs", "pre")

    db_connection = DbConnectionManager()
    spot_api_client = CcdataSpotApiClient()

    # Pass db_connection to get_top_assets
    top_assets = get_top_assets(db_connection, limit=args.asset_limit)
    if not top_assets:
        logger.error("Failed to retrieve top assets from database. Aborting.")
        return

    # Fetch qualified exchanges from the database
    qualified_exchanges = get_qualified_exchanges_from_db(db_connection)
    logger.info(f"Qualified Exchanges from DB: {qualified_exchanges}")
    if not qualified_exchanges:
        logger.error("Failed to retrieve qualified exchanges from database. Aborting.")
        return

    # Apply exchange limit if specified
    if args.exchange_limit is not None:
        qualified_exchanges = qualified_exchanges[: args.exchange_limit]
        logger.info(
            f"Limiting ingestion to {len(qualified_exchanges)} exchanges for testing."
        )

    # Fetch trading pairs from the database
    trading_pairs = get_trading_pairs_from_db(
        db_connection, top_assets, qualified_exchanges
    )
    if not trading_pairs:
        logger.error(
            "No trading pairs found in database for the given criteria. Aborting."
        )
        return

    # Apply pair limit if specified
    if args.pair_limit is not None:
        trading_pairs = trading_pairs[: args.pair_limit]
        logger.info(
            f"Limiting ingestion to {len(trading_pairs)} trading pairs for testing."
        )

    for exchange, base_symbol, quote_symbol in trading_pairs:
        ingest_daily_ohlcv_data_for_pair(
            spot_api_client, db_connection, exchange, base_symbol, quote_symbol
        )
        time.sleep(0.1)  # Small delay to avoid hitting API rate limits too quickly

    # Add deduplication step after ingestion
    table_name = "market.cc_ohlcv_spot_1d_raw"
    key_cols = ["datetime", "exchange", "symbol_unmapped"]
    latest_col = "collected_at"
    # deduplicate_table(db_connection, table_name, key_cols, latest_col)

    db_connection.close_connection()
    logger.info(
        "Daily OHLCV spot data ingestion for top assets on qualified exchanges completed."
    )
    record_rate_limit_status("ingest_ohlcv_spot_1d_top_pairs", "post")


if __name__ == "__main__":
    main()
