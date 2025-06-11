import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import List, Optional
import argparse

# Adjusting import paths for script execution
from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.data_api.spot_api_client import CcdataSpotApiClient

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


def ingest_daily_ohlcv_data(
    market: str,
    instrument: str,
    to_ts: Optional[int] = None,
    limit: Optional[int] = None,
):
    """
    Fetches daily OHLCV data and ingests it into the database.

    Args:
        market (str): The market / exchange under consideration.
        instrument (str): A mapped and/or unmapped instrument to retrieve.
        to_ts (int, optional): Returns historical data up to and including this Unix timestamp. Defaults to None.
        limit (int, optional): The number of data points to return. Defaults to 30.
    """
    api_client = CcdataSpotApiClient()
    db = DbConnectionManager()
    table_name = "market.cc_ohlcv_spot_1d_raw"

    logger.info(f"Ingesting daily OHLCV data for {instrument} on {market}")
    try:
        data = api_client.get_historical_ohlcv(
            interval="days",
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
                    }
                )
            if records:
                db.insert_dataframe(records, table_name)
                logger.info(
                    f"Successfully ingested {len(records)} daily OHLCV records."
                )
            else:
                logger.info("No daily OHLCV data to ingest.")
        else:
            logger.warning(f"No data received for {instrument} on {market}.")
    except Exception as e:
        logger.error(f"Error ingesting daily OHLCV data: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest daily OHLCV spot data.")
    parser.add_argument(
        "--market",
        type=str,
        required=True,
        help="The market / exchange to retrieve data from.",
    )
    parser.add_argument(
        "--instrument",
        type=str,
        required=True,
        help="The instrument to retrieve data for.",
    )
    parser.add_argument(
        "--to_ts", type=int, help="Unix timestamp up to which to retrieve data."
    )
    parser.add_argument(
        "--limit", type=int, help="The number of data points to return."
    )

    args = parser.parse_args()

    print("Attempting to ingest daily OHLCV spot data...")
    # Ensure CCDATA_API_KEY and SINGLESTORE_CONNECTION_STRING are set in .env

    ingest_daily_ohlcv_data(
        market=args.market,
        instrument=args.instrument,
        to_ts=args.to_ts,
        limit=args.limit,
    )
