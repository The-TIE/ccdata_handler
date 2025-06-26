import os
import argparse
import polars as pl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import glob
from dotenv import load_dotenv

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager

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


def get_date_range_from_source_table() -> tuple[datetime, datetime]:
    """Get the min and max datetime from the source table."""
    logger.info("Getting date range from source table...")

    with DbConnectionManager() as db:
        query = """
        SELECT 
            MIN(datetime) as min_date,
            MAX(datetime) as max_date,
            COUNT(*) as total_rows
        FROM market.cc_futures_ohlcv_1m
        """
        result = db._execute_query(query, fetch=True)

        if result and len(result) > 0:
            min_date = result[0][0]
            max_date = result[0][1]
            total_rows = result[0][2]

            logger.info(f"Source table date range: {min_date} to {max_date}")
            logger.info(f"Total rows in source table: {total_rows:,}")

            return min_date, max_date
        else:
            raise ValueError("Could not retrieve date range from source table")


def create_target_table_if_not_exists():
    """Create the target table with proper primary and sort keys."""
    logger.info("Creating target table if it doesn't exist...")

    create_table_query = """
    CREATE TABLE IF NOT EXISTS market.cc_futures_ohlcv_1m_new (
        datetime DATETIME NOT NULL,
        market VARCHAR(255) NOT NULL,
        instrument VARCHAR(255) NOT NULL,
        mapped_instrument VARCHAR(255),
        type VARCHAR(255),
        index_underlying VARCHAR(255),
        quote_currency VARCHAR(255),
        settlement_currency VARCHAR(255),
        contract_currency VARCHAR(255),
        denomination_type VARCHAR(255),
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        number_of_contracts BIGINT,
        volume DOUBLE,
        quote_volume DOUBLE,
        volume_buy DOUBLE,
        quote_volume_buy DOUBLE,
        volume_sell DOUBLE,
        quote_volume_sell DOUBLE,
        volume_unknown DOUBLE,
        quote_volume_unknown DOUBLE,
        total_trades BIGINT,
        total_trades_buy BIGINT,
        total_trades_sell BIGINT,
        total_trades_unknown BIGINT,
        first_trade_timestamp DATETIME,
        last_trade_timestamp DATETIME,
        first_trade_price DOUBLE,
        high_trade_price DOUBLE,
        high_trade_timestamp DATETIME,
        low_trade_price DOUBLE,
        low_trade_timestamp DATETIME,
        last_trade_price DOUBLE,
        collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (datetime, market, mapped_instrument),
        SORT KEY (datetime, market, mapped_instrument)
    );
    """

    with DbConnectionManager() as db:
        db._execute_query(create_table_query, commit=True)
        logger.info("Target table created successfully or already exists")


def export_chunk_to_parquet(
    start_dt: datetime, end_dt: datetime, output_file: str, chunk_size_days: int = 30
) -> int:
    """
    Export a chunk of data from the source table to a Parquet file.

    Returns:
        Number of rows exported
    """
    logger.info(f"Exporting data from {start_dt} to {end_dt} to {output_file}...")

    query = f"""
    SELECT
        DATE_FORMAT(`datetime`, '%Y-%m-%dT%H:%i:%s') AS datetime_str,  -- Export as ISO 8601 string
        market,
        instrument,
        mapped_instrument,
        type,
        index_underlying,
        quote_currency,
        settlement_currency,
        contract_currency,
        denomination_type,
        open,
        high,
        low,
        close,
        number_of_contracts,
        volume,
        quote_volume,
        volume_buy,
        quote_volume_buy,
        volume_sell,
        quote_volume_sell,
        volume_unknown,
        quote_volume_unknown,
        total_trades,
        total_trades_buy,
        total_trades_sell,
        total_trades_unknown,
        CASE WHEN first_trade_timestamp = '0000-00-00 00:00:00' THEN NULL ELSE DATE_FORMAT(first_trade_timestamp, '%Y-%m-%dT%H:%i:%s') END AS first_trade_timestamp_str,
        CASE WHEN last_trade_timestamp = '0000-00-00 00:00:00' THEN NULL ELSE DATE_FORMAT(last_trade_timestamp, '%Y-%m-%dT%H:%i:%s') END AS last_trade_timestamp_str,
        first_trade_price,
        high_trade_price,
        CASE WHEN high_trade_timestamp = '0000-00-00 00:00:00' THEN NULL ELSE DATE_FORMAT(high_trade_timestamp, '%Y-%m-%dT%H:%i:%s') END AS high_trade_timestamp_str,
        low_trade_price,
        CASE WHEN low_trade_timestamp = '0000-00-00 00:00:00' THEN NULL ELSE DATE_FORMAT(low_trade_timestamp, '%Y-%m-%dT%H:%i:%s') END AS low_trade_timestamp_str,
        last_trade_price,
        DATE_FORMAT(collected_at, '%Y-%m-%dT%H:%i:%s') AS collected_at_str
    FROM market.cc_futures_ohlcv_1m
    WHERE `datetime` >= '{start_dt.strftime("%Y-%m-%d %H:%M:%S")}'
    AND `datetime` < '{end_dt.strftime("%Y-%m-%d %H:%M:%S")}'
    ORDER BY `datetime`, market, mapped_instrument
    """

    try:
        with DbConnectionManager() as db:
            # Log the query for debugging
            logger.debug(f"Export query:\n{query}")

            # Use Polars to read directly from the database and write to Parquet
            df = pl.read_database_uri(
                uri=db.connection_uri,
                query=query,
                engine="connectorx",
                schema_overrides={
                    "datetime_str": pl.Utf8,  # Read as string to avoid SingleStore bug
                    "collected_at_str": pl.Utf8,
                    "first_trade_timestamp_str": pl.Utf8,
                    "last_trade_timestamp_str": pl.Utf8,
                    "high_trade_timestamp_str": pl.Utf8,
                    "low_trade_timestamp_str": pl.Utf8,
                },
            )

            if not df.is_empty():
                # Log sample data for debugging timestamp conversion
                logger.info(f"Sample exported data (first 2 rows):")
                sample_data = df.head(2).to_dicts()
                for i, row in enumerate(sample_data):
                    logger.info(
                        f"Row {i+1}: datetime_str={row.get('datetime_str')}, market={row.get('market')}, mapped_instrument={row.get('mapped_instrument')}"
                    )

                # Validate datetime string values
                datetime_col = df["datetime_str"]
                min_dt = datetime_col.min()
                max_dt = datetime_col.max()
                logger.info(f"datetime_str range: {min_dt} to {max_dt}")

                # Check for any null values
                null_count = datetime_col.null_count()
                if null_count > 0:
                    logger.warning(f"Found {null_count} rows with null datetime_str")

                # Write to Parquet with compression
                df.write_parquet(
                    output_file,
                    compression="snappy",  # Good balance of speed and compression
                    use_pyarrow=True,
                )
                row_count = len(df)
                logger.info(f"Exported {row_count:,} rows to {output_file}")
                return row_count
            else:
                logger.info(f"No data found for period {start_dt} to {end_dt}")
                return 0

    except Exception as e:
        logger.error(f"Error exporting chunk from {start_dt} to {end_dt}: {e}")
        raise


def load_parquet_file_to_target(parquet_file: str) -> int:
    """
    Load a Parquet file into the target table using LOAD DATA LOCAL INFILE.

    Returns:
        Number of rows loaded
    """
    logger.info(f"Loading {parquet_file} into target table...")

    # Convert to absolute path for LOAD DATA LOCAL INFILE
    abs_parquet_file = os.path.abspath(parquet_file)

    # First, let's inspect the parquet file to understand its structure
    logger.info("Inspecting Parquet file structure...")
    try:
        df_inspect = pl.read_parquet(parquet_file)
        logger.info(f"Parquet file columns: {df_inspect.columns}")
        logger.info(f"Parquet file shape: {df_inspect.shape}")
        logger.info(f"First row sample: {df_inspect.head(1).to_dicts()}")

        # Check for any datetime string values that might be problematic
        if "datetime_str" in df_inspect.columns:
            sample_datetimes = df_inspect["datetime_str"].head(5).to_list()
            logger.info(f"Sample datetime_str values: {sample_datetimes}")
    except Exception as e:
        logger.error(f"Error inspecting Parquet file: {e}")

    # Define the column list explicitly for FORMAT PARQUET
    # These are the actual column names from the Parquet file.
    parquet_columns = [
        "datetime_str",
        "market",
        "instrument",
        "mapped_instrument",
        "type",
        "index_underlying",
        "quote_currency",
        "settlement_currency",
        "contract_currency",
        "denomination_type",
        "open",
        "high",
        "low",
        "close",
        "number_of_contracts",
        "volume",
        "quote_volume",
        "volume_buy",
        "quote_volume_buy",
        "volume_sell",
        "quote_volume_sell",
        "volume_unknown",
        "quote_volume_unknown",
        "total_trades",
        "total_trades_buy",
        "total_trades_sell",
        "total_trades_unknown",
        "first_trade_timestamp_str",
        "last_trade_timestamp_str",
        "first_trade_price",
        "high_trade_price",
        "high_trade_timestamp_str",
        "low_trade_price",
        "low_trade_timestamp_str",
        "last_trade_price",
        "collected_at_str",
    ]

    # Create the column mapping string for FORMAT PARQUET using <- syntax
    # Map string datetime columns directly - SingleStore should auto-convert ISO 8601 strings
    column_mappings = []
    for col in parquet_columns:
        if col.endswith("_str"):
            # Map string datetime columns to their corresponding table columns
            table_col = col.replace("_str", "")
            column_mappings.append(f"`{table_col}` <- `{col}`")
        else:
            # Direct mapping for non-datetime columns
            column_mappings.append(f"`{col}` <- `{col}`")

    column_mapping_str = ",\n    ".join(column_mappings)

    # Use the correct SingleStore syntax for LOAD DATA FORMAT PARQUET
    # SingleStore should auto-convert ISO 8601 strings to DATETIME
    load_query = f"""
    LOAD DATA LOCAL INFILE '{abs_parquet_file}'
    INTO TABLE market.cc_futures_ohlcv_1m_new
    ({column_mapping_str})
    FORMAT PARQUET;
    """

    logger.debug(f"Full LOAD DATA query:\n{load_query}")

    try:
        with DbConnectionManager() as db:
            # Execute the LOAD DATA query and get affected rows
            affected_rows = db._execute_query(load_query, commit=True)

            # If affected_rows is None, we'll estimate by counting rows in the file
            if affected_rows is None:
                # Read the parquet file to count rows as fallback
                df = pl.read_parquet(parquet_file)
                affected_rows = len(df)
                logger.info(
                    f"Loaded {parquet_file} (estimated {affected_rows:,} rows based on file content)"
                )
            else:
                logger.info(f"Loaded {affected_rows:,} rows from {parquet_file}")

            return affected_rows if affected_rows is not None else 0

    except Exception as e:
        logger.error(f"Error loading {parquet_file}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full error details: {str(e)}")

        # Let's try a simpler approach to understand SingleStore's requirements
        logger.info(
            "Attempting to understand SingleStore's LOAD DATA FORMAT PARQUET syntax..."
        )
        try:
            with DbConnectionManager() as db:
                # Try a minimal query to see what error we get
                test_query = f"""
                LOAD DATA LOCAL INFILE '{abs_parquet_file}'
                INTO TABLE market.cc_futures_ohlcv_1m_new
                FORMAT PARQUET;
                """
                logger.debug(f"Testing minimal query: {test_query}")
                db._execute_query(test_query, commit=True)
        except Exception as test_e:
            logger.error(f"Minimal query error: {test_e}")

        raise


def verify_transfer_completion():
    """Verify that the transfer completed successfully by comparing row counts."""
    logger.info("Verifying transfer completion...")

    with DbConnectionManager() as db:
        # Get source table count
        source_query = "SELECT COUNT(*) FROM market.cc_futures_ohlcv_1m"
        source_result = db._execute_query(source_query, fetch=True)
        source_count = source_result[0][0] if source_result else 0

        # Get target table count
        target_query = "SELECT COUNT(*) FROM market.cc_futures_ohlcv_1m_new"
        target_result = db._execute_query(target_query, fetch=True)
        target_count = target_result[0][0] if target_result else 0

        logger.info(f"Source table rows: {source_count:,}")
        logger.info(f"Target table rows: {target_count:,}")

        if source_count == target_count:
            logger.info("✅ Transfer completed successfully! Row counts match.")
            return True
        else:
            logger.warning(
                f"⚠️ Row count mismatch! Missing {source_count - target_count:,} rows."
            )
            return False


def bulk_transfer_futures_ohlcv(
    output_dir: str = "/tmp/futures_ohlcv_parquet",
    chunk_days: int = 30,
    cleanup_files: bool = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """
    Main function to transfer data from source to target table using Parquet files.

    Args:
        output_dir: Directory to store temporary Parquet files
        chunk_days: Number of days per chunk (default 30)
        cleanup_files: Whether to delete Parquet files after loading (default True)
        start_date: Optional start date (YYYY-MM-DD format)
        end_date: Optional end date (YYYY-MM-DD format)
    """
    logger.info("Starting bulk transfer of futures OHLCV data using Parquet format...")

    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Using output directory: {output_dir}")

        # Create target table
        create_target_table_if_not_exists()

        # Get date range
        if start_date and end_date:
            min_date = datetime.strptime(start_date, "%Y-%m-%d")
            max_date = datetime.strptime(end_date, "%Y-%m-%d")
            logger.info(f"Using provided date range: {min_date} to {max_date}")
        else:
            min_date, max_date = get_date_range_from_source_table()

        # Process data in chunks
        current_dt = min_date
        total_exported_rows = 0
        total_loaded_rows = 0
        chunk_count = 0
        max_retries = 3  # Limit retries to prevent endless loops
        consecutive_failures = 0

        while current_dt <= max_date:
            chunk_count += 1
            chunk_end_dt = current_dt + timedelta(days=chunk_days)
            if chunk_end_dt > max_date:
                chunk_end_dt = max_date + timedelta(
                    seconds=1
                )  # Include the last second

            # Generate output filename
            output_file = os.path.join(
                output_dir,
                f"futures_ohlcv_{current_dt.strftime('%Y%m%d')}_to_{chunk_end_dt.strftime('%Y%m%d')}.parquet",
            )

            try:
                # Export chunk to Parquet
                exported_rows = export_chunk_to_parquet(
                    current_dt, chunk_end_dt, output_file
                )
                total_exported_rows += exported_rows

                if exported_rows > 0:
                    # Load Parquet file into target table
                    loaded_rows = load_parquet_file_to_target(output_file)
                    total_loaded_rows += loaded_rows

                    # Clean up file if requested
                    if cleanup_files:
                        os.remove(output_file)
                        logger.info(f"Cleaned up {output_file}")

                logger.info(
                    f"Chunk {chunk_count} completed. Progress: {current_dt} to {chunk_end_dt}"
                )
                logger.info(
                    f"Running totals - Exported: {total_exported_rows:,}, Loaded: {total_loaded_rows:,}"
                )

                # Reset failure counter on success
                consecutive_failures = 0

            except Exception as e:
                consecutive_failures += 1
                logger.error(
                    f"Error processing chunk {chunk_count} ({current_dt} to {chunk_end_dt}): {e}"
                )

                # If we've had too many consecutive failures, stop the endless loop
                if consecutive_failures >= max_retries:
                    logger.error(
                        f"Too many consecutive failures ({consecutive_failures}). Stopping to prevent endless loop."
                    )
                    break

                logger.info(
                    f"Continuing with next chunk (failure {consecutive_failures}/{max_retries})"
                )

            # Always advance the date to prevent infinite loops
            current_dt = chunk_end_dt

        logger.info(f"Transfer process completed!")
        logger.info(f"Total chunks processed: {chunk_count}")
        logger.info(f"Total rows exported: {total_exported_rows:,}")
        logger.info(f"Total rows loaded: {total_loaded_rows:,}")

        # Verify completion
        verify_transfer_completion()

    except Exception as e:
        logger.error(f"Fatal error during bulk transfer: {e}")
        raise


def cleanup_existing_parquet_files(output_dir: str):
    """Clean up any existing Parquet files in the output directory."""
    if os.path.exists(output_dir):
        parquet_files = glob.glob(os.path.join(output_dir, "*.parquet"))
        if parquet_files:
            logger.info(f"Cleaning up {len(parquet_files)} existing Parquet files...")
            for file in parquet_files:
                os.remove(file)
            logger.info("Cleanup completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bulk transfer futures OHLCV data using efficient Parquet format"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/tmp/futures_ohlcv_parquet",
        help="Directory to store temporary Parquet files (default: /tmp/futures_ohlcv_parquet)",
    )
    parser.add_argument(
        "--chunk-days",
        type=int,
        default=30,
        help="Number of days per chunk (default: 30)",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Keep Parquet files after loading (default: delete files)",
    )
    parser.add_argument(
        "--start-date", type=str, help="Start date in YYYY-MM-DD format (optional)"
    )
    parser.add_argument(
        "--end-date", type=str, help="End date in YYYY-MM-DD format (optional)"
    )
    parser.add_argument(
        "--cleanup-existing",
        action="store_true",
        help="Clean up existing Parquet files before starting",
    )

    args = parser.parse_args()

    # Clean up existing files if requested
    if args.cleanup_existing:
        cleanup_existing_parquet_files(args.output_dir)

    # Run the bulk transfer
    bulk_transfer_futures_ohlcv(
        output_dir=args.output_dir,
        chunk_days=args.chunk_days,
        cleanup_files=not args.no_cleanup,
        start_date=args.start_date,
        end_date=args.end_date,
    )
