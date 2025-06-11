import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from typing import List, Optional
import argparse
import time

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.data_api.spot_api_client import CcdataSpotApiClient
from src.data_api.asset_api_client import CcdataAssetApiClient
from src.min_api.general_info_api_client import MinApiGeneralInfoApiClient

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


def get_qualified_exchanges() -> List[str]:
    """
    Fetches exchanges rated 'BB' or better.
    Returns a list of exchange names.
    """
    min_api_client = MinApiGeneralInfoApiClient()
    logger.info("Fetching exchanges with 'BB' rating or better...")
    try:
        response = min_api_client.get_exchanges_general_info()
        if response and response.get("Data"):
            qualified_exchanges = []
            for exchange_id, details in response["Data"].items():
                grade = details.get("Grade")
                if grade in ["AAA", "AA", "A", "BBB", "BB"]:
                    qualified_exchanges.append(details.get("InternalName"))
            logger.info(f"Found {len(qualified_exchanges)} qualified exchanges.")
            return qualified_exchanges
        else:
            logger.warning("No exchange general info found or API response was empty.")
            return []
    except Exception as e:
        logger.error(f"Error fetching qualified exchanges: {e}")
        return []


def get_trading_pairs_for_assets_on_exchanges(
    assets: List[str], exchanges: List[str]
) -> List[tuple]:
    """
    Fetches all trading pairs for the given assets on the specified exchanges.
    Returns a list of (exchange, base_symbol, quote_symbol) tuples.
    """
    min_api_client = MinApiGeneralInfoApiClient()
    all_pairs = set()
    logger.info("Fetching all trading pairs for top assets on qualified exchanges...")

    for exchange_name in exchanges:
        logger.debug(f"Processing exchange: {exchange_name}")
        try:
            # The get_all_exchanges endpoint can filter by 'e' (exchange)
            response = min_api_client.get_all_exchanges(e=exchange_name)
            if response and response.get("Data") and response["Data"].get("exchanges"):
                exchange_data = response["Data"]["exchanges"].get(exchange_name)
                if exchange_data and exchange_data.get("pairs"):
                    for base_symbol, pair_data in exchange_data["pairs"].items():
                        if (
                            base_symbol in assets
                        ):  # Only consider pairs for our top assets
                            for quote_symbol, _ in pair_data.get("tsyms", {}).items():
                                all_pairs.add(
                                    (exchange_name, base_symbol, quote_symbol)
                                )
                else:
                    logger.warning(
                        f"No pairs data found for exchange: {exchange_name}. Response: {response}"
                    )
            else:
                logger.warning(
                    f"No trading pairs found for exchange: {exchange_name}. Full response: {response}"
                )
        except Exception as e:
            logger.error(f"Error fetching trading pairs for {exchange_name}: {e}")

    logger.info(f"Found {len(all_pairs)} unique trading pairs.")
    return list(all_pairs)


def get_last_ingested_datetime(
    db: DbConnectionManager, exchange: str, symbol_unmapped: str
) -> Optional[datetime]:
    """
    Retrieves the latest datetime for a given exchange and unmapped symbol from the database.
    """
    query = f"""
        SELECT MAX(datetime)
        FROM market.cc_ohlcv_spot_1d_raw
        WHERE exchange = %s AND symbol_unmapped = %s;
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
                f"No new data needed for {instrument} on {exchange}. Last record is up to date (last ingested: {last_ingested_date})."
            )
            return

        # Fetch data from the day after the last ingested data
        start_date_to_fetch = last_datetime_in_db + timedelta(days=1)

        # Calculate the number of days between start_date_to_fetch and now
        delta = datetime.now(timezone.utc) - start_date_to_fetch
        limit = delta.days + 1  # +1 to include the current partial day if applicable

        start_from_log_str = start_date_to_fetch.strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(
            f"Fetching daily OHLCV for {instrument} on {exchange} from {start_from_log_str} onwards (limit={limit})."
        )
    else:
        # Backfill 2 years if no data exists
        two_years_ago = datetime.now(timezone.utc) - timedelta(days=2 * 365)
        limit = 730  # Approximately 2 years of daily data
        start_from_log_str = two_years_ago.strftime("%Y-%m-%d %H:%M:%S UTC")
        logger.info(
            f"Backfilling 2 years of daily OHLCV for {instrument} on {exchange} from {start_from_log_str} onwards (limit={limit})."
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
                            "first_trade_timestamp": entry.get("FIRST_TRADE_TIMESTAMP"),
                            "last_trade_timestamp": entry.get("LAST_TRADE_TIMESTAMP"),
                            "first_trade_price": entry.get("FIRST_TRADE_PRICE"),
                            "high_trade_price": entry.get("HIGH_TRADE_PRICE"),
                            "high_trade_timestamp": entry.get("HIGH_TRADE_TIMESTAMP"),
                            "low_trade_price": entry.get("LOW_TRADE_PRICE"),
                            "low_trade_timestamp": entry.get("LOW_TRADE_TIMESTAMP"),
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

    db_connection = DbConnectionManager()
    spot_api_client = CcdataSpotApiClient()

    top_assets = get_top_assets(limit=args.asset_limit)
    if not top_assets:
        logger.error("Failed to retrieve top assets. Aborting.")
        return

    qualified_exchanges = get_qualified_exchanges()
    logger.info(f"Qualified Exchanges: {qualified_exchanges}")
    if not qualified_exchanges:
        logger.error("Failed to retrieve qualified exchanges. Aborting.")
        return

    # Apply exchange limit if specified
    if args.exchange_limit is not None:
        qualified_exchanges = qualified_exchanges[: args.exchange_limit]
        logger.info(
            f"Limiting ingestion to {len(qualified_exchanges)} exchanges for testing."
        )

    trading_pairs = get_trading_pairs_for_assets_on_exchanges(
        top_assets, qualified_exchanges
    )
    if not trading_pairs:
        logger.error("No trading pairs found. Aborting.")
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

    db_connection.close_connection()
    logger.info(
        "Daily OHLCV spot data ingestion for top assets on qualified exchanges completed."
    )


if __name__ == "__main__":
    main()
    # top_exchanges = get_qualified_exchanges()
    # print(top_exchanges)
