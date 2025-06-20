import os
import argparse
from dotenv import load_dotenv

from src.logger_config import setup_logger
from src.ingestion.futures_ingestor import FuturesIngestor

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


def main():
    parser = argparse.ArgumentParser(
        description="Ingest various types of futures data (OHLCV, Funding Rate, Open Interest) for specified or all exchanges and instruments."
    )
    parser.add_argument(
        "--data-type",
        type=str,
        required=True,
        choices=["ohlcv", "funding-rate", "open-interest"],
        help="The type of futures data to ingest (e.g., ohlcv, funding-rate, open-interest).",
    )
    parser.add_argument(
        "--interval",
        type=str,
        required=True,
        choices=["1d", "1h", "1m"],
        help="The interval of the futures data (e.g., 1d, 1h, 1m).",
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

    try:
        exchanges_list = [e.strip() for e in args.exchanges.split(",")] if args.exchanges else None
        instruments_list = [i.strip() for i in args.instruments.split(",")] if args.instruments else None
        instrument_statuses_list = [s.strip() for s in args.instrument_status.split(",")]

        ingestor = FuturesIngestor(args.data_type, args.interval)
        ingestor.run_ingestion(exchanges_list, instruments_list, instrument_statuses_list)

    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during ingestion: {e}")


if __name__ == "__main__":
    main()