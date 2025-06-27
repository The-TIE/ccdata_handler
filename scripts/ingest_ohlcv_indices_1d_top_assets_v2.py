#!/usr/bin/env python3
"""
Enhanced indices OHLCV data ingestion script using the unified framework.

This script replaces the original ingest_ohlcv_indices_1d_top_assets.py with
improved architecture, better error handling, and monitoring capabilities.

Key improvements:
- Uses the unified ingestion framework
- Async processing for better performance
- Comprehensive monitoring and alerting
- Caching for frequently accessed data
- Better error handling and recovery
"""

import asyncio
import argparse
import sys
from datetime import datetime, timezone
from typing import Optional

# Add src to path for imports
sys.path.insert(0, "src")

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.data_api.indices_ref_rates_api_client import CcdataIndicesRefRatesApiClient
from src.data_api.asset_api_client import CcdataAssetApiClient
from src.ingestion.config import get_config
from src.ingestion.ingestors.indices_ohlcv_ingestor import IndicesOHLCVIngestor
from src.ingestion.monitoring import IngestionMonitor
from src.ingestion.cache import CacheManager, CacheBackend
from src.rate_limit_tracker import record_rate_limit_status


# Configure logging
logger = setup_logger(__name__, log_to_console=True)


async def main():
    """Main ingestion function."""
    parser = argparse.ArgumentParser(
        description="Ingest daily OHLCV indices data for top assets using unified framework."
    )
    parser.add_argument(
        "--asset_limit",
        type=int,
        default=50,
        help="Limit the number of top assets to process.",
    )
    parser.add_argument(
        "--market",
        type=str,
        default="cadli",
        help="The index family to obtain data from (e.g., 'cadli').",
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="1d",
        choices=["1d", "1h", "1m"],
        help="Time interval for the data.",
    )
    parser.add_argument(
        "--parallel_workers",
        type=int,
        default=4,
        help="Number of parallel workers for processing.",
    )
    parser.add_argument(
        "--enable_monitoring",
        action="store_true",
        help="Enable advanced monitoring and alerting.",
    )
    parser.add_argument(
        "--enable_caching",
        action="store_true",
        help="Enable caching for frequently accessed data.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Perform a dry run without actually ingesting data.",
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("ENHANCED INDICES OHLCV DATA INGESTION")
    logger.info("=" * 80)
    logger.info(f"Market: {args.market}")
    logger.info(f"Interval: {args.interval}")
    logger.info(f"Asset limit: {args.asset_limit}")
    logger.info(f"Parallel workers: {args.parallel_workers}")
    logger.info(f"Monitoring enabled: {args.enable_monitoring}")
    logger.info(f"Caching enabled: {args.enable_caching}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 80)

    # Record start of ingestion
    record_rate_limit_status("ingest_ohlcv_indices_1d_top_assets_v2", "pre")

    # Initialize configuration
    config = get_config()

    # Override parallel workers if specified
    if args.parallel_workers != 4:
        config.update_config("ingestion", parallel_workers=args.parallel_workers)

    # Initialize monitoring if enabled
    monitor = None
    if args.enable_monitoring:
        monitor = IngestionMonitor(config)
        await monitor.start_monitoring()
        logger.info("Advanced monitoring enabled")

    # Initialize caching if enabled
    cache_manager = None
    if args.enable_caching:
        cache_manager = CacheManager(
            backend=CacheBackend.MEMORY,
            default_ttl=1800,  # 30 minutes for top assets
            max_memory_entries=1000,
        )
        await cache_manager.start_background_cleanup()
        logger.info("Caching enabled")

    # Initialize database connection
    db_connection = None
    api_clients = None
    ingestor = None

    try:
        # Initialize database connection
        db_connection = DbConnectionManager()
        logger.info("Database connection established")

        # Initialize API clients
        indices_api_client = CcdataIndicesRefRatesApiClient()
        asset_api_client = CcdataAssetApiClient()
        logger.info("API clients initialized")

        # Initialize the ingestor
        ingestor = IndicesOHLCVIngestor(
            api_client=indices_api_client,
            db_client=db_connection,
            config=config,
            interval=args.interval,
            asset_api_client=asset_api_client,
        )
        logger.info("Indices OHLCV ingestor initialized")

        # Start performance tracking
        tracking_id = None
        if monitor:
            tracking_id = monitor.start_performance_tracking(
                "indices_ohlcv_ingestion",
                metadata={
                    "market": args.market,
                    "interval": args.interval,
                    "asset_limit": args.asset_limit,
                    "dry_run": args.dry_run,
                },
            )

        if args.dry_run:
            logger.info("DRY RUN MODE - No data will be ingested")

            # Just fetch top assets to test the connection
            top_assets = await ingestor.get_top_assets(limit=min(10, args.asset_limit))
            logger.info(f"Would process {len(top_assets)} assets: {top_assets[:5]}...")

            result = {
                "status": "success",
                "dry_run": True,
                "total_assets": len(top_assets),
                "sample_assets": top_assets[:5],
            }
        else:
            # Perform actual ingestion
            logger.info("Starting indices OHLCV data ingestion...")

            result = await ingestor.ingest_top_assets(
                market=args.market,
                asset_limit=args.asset_limit,
            )

        # Log results
        logger.info("=" * 80)
        logger.info("INGESTION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Status: {result.get('status', 'unknown')}")

        if not args.dry_run:
            logger.info(f"Total assets processed: {result.get('total_assets', 0)}")
            logger.info(f"Successful assets: {result.get('successful_assets', 0)}")
            logger.info(f"Failed assets: {result.get('failed_assets', 0)}")
            logger.info(
                f"Total records processed: {result.get('total_records_processed', 0)}"
            )
            logger.info(
                f"Total records inserted: {result.get('total_records_inserted', 0)}"
            )

            # Calculate success rate
            total_assets = result.get("total_assets", 0)
            successful_assets = result.get("successful_assets", 0)
            if total_assets > 0:
                success_rate = (successful_assets / total_assets) * 100
                logger.info(f"Success rate: {success_rate:.1f}%")

        # End performance tracking
        if monitor and tracking_id:
            monitor.end_performance_tracking(
                tracking_id,
                records_processed=result.get("total_records_processed", 0),
                records_inserted=result.get("total_records_inserted", 0),
                success=result.get("status") == "success",
                metadata={"result": result},
            )

        # Show monitoring stats if enabled
        if monitor:
            stats = await monitor.get_performance_summary(time_window_minutes=60)
            if stats:
                logger.info("Performance Summary:")
                for operation, metrics in stats.items():
                    logger.info(
                        f"  {operation}: {metrics['success_rate']:.1%} success rate, "
                        f"{metrics['avg_duration_seconds']:.2f}s avg duration"
                    )

        # Show cache stats if enabled
        if cache_manager:
            cache_stats = await cache_manager.get_stats()
            logger.info(
                f"Cache Stats: {cache_stats['hit_rate']:.1%} hit rate, "
                f"{cache_stats['memory_entries']} entries"
            )

        logger.info("=" * 80)

        # Determine exit code
        if result.get("status") == "success":
            logger.info("Ingestion completed successfully!")
            exit_code = 0
        elif result.get("status") == "partial_failure":
            logger.warning("Ingestion completed with some failures")
            exit_code = 1
        else:
            logger.error("Ingestion failed")
            exit_code = 2

    except Exception as e:
        logger.error(f"Fatal error during ingestion: {e}", exc_info=True)

        # Create alert if monitoring is enabled
        if monitor:
            await monitor.create_alert(
                alert_id=f"fatal_error_{int(datetime.now().timestamp())}",
                level=monitor.AlertLevel.CRITICAL,
                message=f"Fatal error in indices OHLCV ingestion: {str(e)}",
                source="ingest_ohlcv_indices_1d_top_assets_v2",
                metadata={"error": str(e), "market": args.market},
            )

        exit_code = 3

    finally:
        # Cleanup resources
        try:
            if db_connection:
                db_connection.close_connection()
                logger.info("Database connection closed")

            if cache_manager:
                await cache_manager.close()
                logger.info("Cache manager closed")

            if monitor:
                await monitor.stop_monitoring()
                logger.info("Monitoring stopped")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        # Record end of ingestion
        record_rate_limit_status("ingest_ohlcv_indices_1d_top_assets_v2", "post")

    logger.info("Script execution completed")
    sys.exit(exit_code)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
