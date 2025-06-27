#!/usr/bin/env python3
"""
Unified CLI tool for all data ingestion operations.

This script provides a single entry point for all ingestion operations in the
unified data ingestion pipeline, supporting different data types, batch operations,
scheduling, and real-time status updates.

Key features:
- Single entry point for all ingestion types
- Support for spot, futures, indices, and metadata ingestion
- Batch operations and parallel processing
- Real-time progress tracking and status updates
- Comprehensive monitoring and alerting
- Caching and performance optimization
- Flexible scheduling and automation support
"""

import asyncio
import argparse
import sys
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Literal
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, "src")

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.data_api.spot_api_client import CcdataSpotApiClient
from src.data_api.futures_api_client import CcdataFuturesApiClient
from src.data_api.indices_ref_rates_api_client import CcdataIndicesRefRatesApiClient
from src.data_api.asset_api_client import CcdataAssetApiClient
from src.data_api.utilities_api_client import CcdataUtilitiesApiClient
from src.ingestion.config import get_config
from src.ingestion.ingestors.spot_ohlcv_ingestor import SpotOHLCVIngestor
from src.ingestion.ingestors.futures_data_ingestor import FuturesDataIngestor
from src.ingestion.ingestors.indices_ohlcv_ingestor import IndicesOHLCVIngestor
from src.ingestion.ingestors.asset_metadata_ingestor import AssetMetadataIngestor
from src.ingestion.ingestors.exchange_metadata_ingestor import ExchangeMetadataIngestor
from src.ingestion.ingestors.instrument_metadata_ingestor import (
    InstrumentMetadataIngestor,
)
from src.ingestion.monitoring import IngestionMonitor, AlertLevel
from src.ingestion.cache import CacheManager, CacheBackend
from src.rate_limit_tracker import record_rate_limit_status


# Configure logging
logger = setup_logger(__name__, log_to_console=True)


DataType = Literal[
    "spot_ohlcv",
    "futures_ohlcv",
    "futures_funding_rate",
    "futures_open_interest",
    "indices_ohlcv",
    "asset_metadata",
    "exchange_metadata",
    "spot_instruments",
    "futures_instruments",
]


class UnifiedIngestCLI:
    """
    Unified CLI for all data ingestion operations.

    Provides a single interface for managing all types of data ingestion
    with comprehensive monitoring, caching, and error handling.
    """

    def __init__(self):
        """Initialize the unified CLI."""
        self.config = None
        self.monitor = None
        self.cache_manager = None
        self.db_connection = None
        self.api_clients = {}
        self.ingestors = {}

    async def initialize(
        self,
        enable_monitoring: bool = False,
        enable_caching: bool = False,
        parallel_workers: int = 4,
    ):
        """
        Initialize all components.

        Args:
            enable_monitoring: Enable advanced monitoring
            enable_caching: Enable caching
            parallel_workers: Number of parallel workers
        """
        # Initialize configuration
        self.config = get_config()

        # Override parallel workers if specified
        if parallel_workers != 4:
            self.config.update_config("ingestion", parallel_workers=parallel_workers)

        # Initialize monitoring if enabled
        if enable_monitoring:
            self.monitor = IngestionMonitor(self.config)
            await self.monitor.start_monitoring()
            logger.info("Advanced monitoring enabled")

        # Initialize caching if enabled
        if enable_caching:
            self.cache_manager = CacheManager(
                backend=CacheBackend.MEMORY,
                default_ttl=1800,  # 30 minutes
                max_memory_entries=2000,
            )
            await self.cache_manager.start_background_cleanup()
            logger.info("Caching enabled")

        # Initialize database connection
        self.db_connection = DbConnectionManager()
        logger.info("Database connection established")

        # Initialize API clients
        self.api_clients = {
            "spot": CcdataSpotApiClient(),
            "futures": CcdataFuturesApiClient(),
            "indices": CcdataIndicesRefRatesApiClient(),
            "asset": CcdataAssetApiClient(),
            "utilities": CcdataUtilitiesApiClient(),
        }
        logger.info("API clients initialized")

    async def get_ingestor(self, data_type: DataType, interval: str = "1d"):
        """
        Get or create an ingestor for the specified data type.

        Args:
            data_type: Type of data to ingest
            interval: Time interval (for time series data)

        Returns:
            Appropriate ingestor instance
        """
        ingestor_key = f"{data_type}_{interval}"

        if ingestor_key not in self.ingestors:
            if data_type == "spot_ohlcv":
                self.ingestors[ingestor_key] = SpotOHLCVIngestor(
                    api_client=self.api_clients["spot"],
                    db_client=self.db_connection,
                    config=self.config,
                    interval=interval,
                )
            elif data_type in [
                "futures_ohlcv",
                "futures_funding_rate",
                "futures_open_interest",
            ]:
                futures_type = data_type.replace("futures_", "").replace("_", "-")
                self.ingestors[ingestor_key] = FuturesDataIngestor(
                    api_client=self.api_clients["futures"],
                    db_client=self.db_connection,
                    config=self.config,
                    interval=interval,
                    data_type=futures_type,
                )
            elif data_type == "indices_ohlcv":
                self.ingestors[ingestor_key] = IndicesOHLCVIngestor(
                    api_client=self.api_clients["indices"],
                    db_client=self.db_connection,
                    config=self.config,
                    interval=interval,
                    asset_api_client=self.api_clients["asset"],
                )
            elif data_type == "asset_metadata":
                self.ingestors[ingestor_key] = AssetMetadataIngestor(
                    api_client=self.api_clients["asset"],
                    db_client=self.db_connection,
                    config=self.config,
                )
            elif data_type == "exchange_metadata":
                self.ingestors[ingestor_key] = ExchangeMetadataIngestor(
                    api_client=self.api_clients["utilities"],
                    db_client=self.db_connection,
                    config=self.config,
                )
            elif data_type == "spot_instruments":
                self.ingestors[ingestor_key] = InstrumentMetadataIngestor(
                    api_client=self.api_clients["spot"],
                    db_client=self.db_connection,
                    config=self.config,
                    instrument_type="spot",
                )
            elif data_type == "futures_instruments":
                self.ingestors[ingestor_key] = InstrumentMetadataIngestor(
                    api_client=self.api_clients["futures"],
                    db_client=self.db_connection,
                    config=self.config,
                    instrument_type="futures",
                )
            else:
                raise ValueError(f"Unsupported data type: {data_type}")

        return self.ingestors[ingestor_key]

    async def ingest_single(
        self, data_type: DataType, interval: str = "1d", **kwargs
    ) -> Dict[str, Any]:
        """
        Ingest a single data type.

        Args:
            data_type: Type of data to ingest
            interval: Time interval (for time series data)
            **kwargs: Additional parameters for the ingestor

        Returns:
            Ingestion results
        """
        logger.info(f"Starting {data_type} ingestion (interval: {interval})")

        # Start performance tracking
        tracking_id = None
        if self.monitor:
            tracking_id = self.monitor.start_performance_tracking(
                f"{data_type}_ingestion",
                metadata={"interval": interval, "kwargs": kwargs},
            )

        try:
            ingestor = await self.get_ingestor(data_type, interval)

            # Call appropriate ingestion method based on data type
            if data_type in [
                "spot_ohlcv",
                "futures_ohlcv",
                "futures_funding_rate",
                "futures_open_interest",
            ]:
                if "trading_pairs" in kwargs:
                    result = await ingestor.ingest_multiple_pairs(**kwargs)
                elif "instruments" in kwargs:
                    result = await ingestor.ingest_multiple_instruments(**kwargs)
                else:
                    result = await ingestor.ingest(**kwargs)
            elif data_type == "indices_ohlcv":
                if "asset_limit" in kwargs:
                    result = await ingestor.ingest_top_assets(**kwargs)
                else:
                    result = await ingestor.ingest(**kwargs)
            else:
                # Metadata ingestors
                result = await ingestor.ingest_metadata(**kwargs)

            # End performance tracking
            if self.monitor and tracking_id:
                self.monitor.end_performance_tracking(
                    tracking_id,
                    records_processed=result.get("records_processed", 0),
                    records_inserted=result.get("records_inserted", 0),
                    success=result.get("status") == "success",
                    metadata={"result": result},
                )

            return result

        except Exception as e:
            logger.error(f"Error in {data_type} ingestion: {e}")

            # Create alert if monitoring is enabled
            if self.monitor:
                await self.monitor.create_alert(
                    alert_id=f"ingestion_error_{data_type}_{int(datetime.now().timestamp())}",
                    level=AlertLevel.ERROR,
                    message=f"Error in {data_type} ingestion: {str(e)}",
                    source="unified_ingest",
                    metadata={"data_type": data_type, "error": str(e)},
                )

            # End performance tracking with error
            if self.monitor and tracking_id:
                self.monitor.end_performance_tracking(
                    tracking_id, success=False, errors=1, metadata={"error": str(e)}
                )

            return {
                "status": "error",
                "error": str(e),
                "data_type": data_type,
            }

    async def ingest_batch(
        self,
        batch_config: List[Dict[str, Any]],
        continue_on_error: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest multiple data types in batch.

        Args:
            batch_config: List of ingestion configurations
            continue_on_error: Whether to continue if one ingestion fails

        Returns:
            Aggregated results
        """
        logger.info(f"Starting batch ingestion with {len(batch_config)} operations")

        results = []
        successful = 0
        failed = 0

        for i, config in enumerate(batch_config):
            data_type = config.pop("data_type")
            interval = config.pop("interval", "1d")

            logger.info(f"Batch operation {i+1}/{len(batch_config)}: {data_type}")

            try:
                result = await self.ingest_single(data_type, interval, **config)
                results.append(result)

                if result.get("status") == "success":
                    successful += 1
                else:
                    failed += 1
                    if not continue_on_error:
                        logger.error(f"Stopping batch due to failure in {data_type}")
                        break

            except Exception as e:
                logger.error(f"Fatal error in batch operation {data_type}: {e}")
                failed += 1
                results.append(
                    {
                        "status": "error",
                        "error": str(e),
                        "data_type": data_type,
                    }
                )

                if not continue_on_error:
                    break

        return {
            "status": "success" if failed == 0 else "partial_failure",
            "total_operations": len(batch_config),
            "successful_operations": successful,
            "failed_operations": failed,
            "results": results,
        }

    async def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the ingestion system.

        Returns:
            System status information
        """
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": "healthy",
            "components": {
                "database": "connected" if self.db_connection else "disconnected",
                "monitoring": "enabled" if self.monitor else "disabled",
                "caching": "enabled" if self.cache_manager else "disabled",
            },
            "api_clients": len(self.api_clients),
            "active_ingestors": len(self.ingestors),
        }

        # Add monitoring stats if available
        if self.monitor:
            health_status = self.monitor.get_health_status()
            status["monitoring"] = health_status

            # Get performance summary
            perf_summary = await self.monitor.get_performance_summary(
                time_window_minutes=60
            )
            if perf_summary:
                status["performance"] = perf_summary

        # Add cache stats if available
        if self.cache_manager:
            cache_stats = await self.cache_manager.get_stats()
            status["cache"] = cache_stats

        return status

    async def cleanup(self):
        """Clean up all resources."""
        try:
            if self.db_connection:
                self.db_connection.close_connection()
                logger.info("Database connection closed")

            if self.cache_manager:
                await self.cache_manager.close()
                logger.info("Cache manager closed")

            if self.monitor:
                await self.monitor.stop_monitoring()
                logger.info("Monitoring stopped")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Unified CLI for all data ingestion operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Ingest spot OHLCV data for top 50 pairs
            python unified_ingest.py spot_ohlcv --pair_limit 50 --interval 1d

            # Ingest futures OHLCV data with monitoring
            python unified_ingest.py futures_ohlcv --enable_monitoring --interval 1h

            # Ingest indices data for top assets
            python unified_ingest.py indices_ohlcv --asset_limit 100 --market cadli

            # Batch ingestion from config file
            python unified_ingest.py batch --config batch_config.json

            # Get system status
            python unified_ingest.py status --enable_monitoring
        """,
    )

    # Global options
    parser.add_argument(
        "--enable_monitoring",
        action="store_true",
        help="Enable advanced monitoring and alerting",
    )
    parser.add_argument(
        "--enable_caching",
        action="store_true",
        help="Enable caching for frequently accessed data",
    )
    parser.add_argument(
        "--parallel_workers",
        type=int,
        default=4,
        help="Number of parallel workers",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Perform a dry run without actually ingesting data",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Spot OHLCV command
    spot_parser = subparsers.add_parser("spot_ohlcv", help="Ingest spot OHLCV data")
    spot_parser.add_argument("--interval", choices=["1d", "1h", "1m"], default="1d")
    spot_parser.add_argument("--pair_limit", type=int, default=100)
    spot_parser.add_argument("--specific_market", type=str)
    spot_parser.add_argument("--specific_instrument", type=str)

    # Futures OHLCV command
    futures_parser = subparsers.add_parser(
        "futures_ohlcv", help="Ingest futures OHLCV data"
    )
    futures_parser.add_argument("--interval", choices=["1d", "1h", "1m"], default="1d")
    futures_parser.add_argument("--exchanges", nargs="+")
    futures_parser.add_argument("--instruments", nargs="+")

    # Futures funding rate command
    funding_parser = subparsers.add_parser(
        "futures_funding_rate", help="Ingest futures funding rate data"
    )
    funding_parser.add_argument("--interval", choices=["1d", "1h", "1m"], default="1d")
    funding_parser.add_argument("--exchanges", nargs="+")
    funding_parser.add_argument("--instruments", nargs="+")

    # Futures open interest command
    oi_parser = subparsers.add_parser(
        "futures_open_interest", help="Ingest futures open interest data"
    )
    oi_parser.add_argument("--interval", choices=["1d", "1h", "1m"], default="1d")
    oi_parser.add_argument("--exchanges", nargs="+")
    oi_parser.add_argument("--instruments", nargs="+")

    # Indices OHLCV command
    indices_parser = subparsers.add_parser(
        "indices_ohlcv", help="Ingest indices OHLCV data"
    )
    indices_parser.add_argument("--interval", choices=["1d", "1h", "1m"], default="1d")
    indices_parser.add_argument("--asset_limit", type=int, default=50)
    indices_parser.add_argument("--market", default="cadli")

    # Asset metadata command
    asset_parser = subparsers.add_parser("asset_metadata", help="Ingest asset metadata")
    asset_parser.add_argument("--full_refresh", action="store_true")

    # Exchange metadata command
    exchange_parser = subparsers.add_parser(
        "exchange_metadata", help="Ingest exchange metadata"
    )
    exchange_parser.add_argument(
        "--exchange_type", choices=["spot", "futures", "all"], default="all"
    )
    exchange_parser.add_argument("--full_refresh", action="store_true")

    # Instrument metadata commands
    spot_inst_parser = subparsers.add_parser(
        "spot_instruments", help="Ingest spot instrument metadata"
    )
    spot_inst_parser.add_argument("--exchanges", nargs="+")

    futures_inst_parser = subparsers.add_parser(
        "futures_instruments", help="Ingest futures instrument metadata"
    )
    futures_inst_parser.add_argument("--exchanges", nargs="+")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Run batch ingestion")
    batch_parser.add_argument(
        "--config", required=True, help="Path to batch configuration file"
    )
    batch_parser.add_argument(
        "--continue_on_error",
        action="store_true",
        help="Continue on individual failures",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Get system status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize CLI
    cli = UnifiedIngestCLI()

    try:
        await cli.initialize(
            enable_monitoring=args.enable_monitoring,
            enable_caching=args.enable_caching,
            parallel_workers=args.parallel_workers,
        )

        # Record start of operation
        record_rate_limit_status("unified_ingest", "pre")

        if args.command == "status":
            # Get and display status
            status = await cli.get_status()
            print(json.dumps(status, indent=2, default=str))

        elif args.command == "batch":
            # Load batch configuration
            config_path = Path(args.config)
            if not config_path.exists():
                logger.error(f"Batch configuration file not found: {args.config}")
                sys.exit(1)

            with open(config_path) as f:
                batch_config = json.load(f)

            if args.dry_run:
                logger.info("DRY RUN MODE - Batch configuration:")
                print(json.dumps(batch_config, indent=2))
                result = {"status": "success", "dry_run": True}
            else:
                result = await cli.ingest_batch(
                    batch_config=batch_config,
                    continue_on_error=args.continue_on_error,
                )

        else:
            # Single ingestion command
            kwargs = vars(args).copy()

            # Remove global arguments
            for key in [
                "command",
                "enable_monitoring",
                "enable_caching",
                "parallel_workers",
                "dry_run",
            ]:
                kwargs.pop(key, None)

            data_type = args.command
            interval = kwargs.pop("interval", "1d")

            if args.dry_run:
                logger.info(f"DRY RUN MODE - Would ingest {data_type} with parameters:")
                print(json.dumps(kwargs, indent=2))
                result = {"status": "success", "dry_run": True}
            else:
                result = await cli.ingest_single(data_type, interval, **kwargs)

        # Display results
        if not args.command == "status":
            logger.info("=" * 80)
            logger.info("OPERATION RESULTS")
            logger.info("=" * 80)
            logger.info(f"Status: {result.get('status', 'unknown')}")

            if not args.dry_run:
                if "total_operations" in result:
                    # Batch results
                    logger.info(
                        f"Total operations: {result.get('total_operations', 0)}"
                    )
                    logger.info(f"Successful: {result.get('successful_operations', 0)}")
                    logger.info(f"Failed: {result.get('failed_operations', 0)}")
                else:
                    # Single operation results
                    logger.info(
                        f"Records processed: {result.get('records_processed', 0)}"
                    )
                    logger.info(
                        f"Records inserted: {result.get('records_inserted', 0)}"
                    )

        # Determine exit code
        if result.get("status") == "success":
            exit_code = 0
        elif result.get("status") == "partial_failure":
            exit_code = 1
        else:
            exit_code = 2

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit_code = 3

    finally:
        # Cleanup
        await cli.cleanup()
        record_rate_limit_status("unified_ingest", "post")

    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
