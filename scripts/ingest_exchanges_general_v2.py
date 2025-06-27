#!/usr/bin/env python3
"""
Enhanced exchanges general data ingestion script using the unified framework.

This script replaces the original ingest_exchanges_general.py with
improved architecture, better error handling, and monitoring capabilities.

Key improvements:
- Uses the unified ingestion framework
- Async processing for better performance
- Comprehensive monitoring and alerting
- Caching for frequently accessed data
- Better error handling and recovery
- Support for both spot and futures exchanges
"""

import asyncio
import argparse
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, "src")

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.data_api.utilities_api_client import CcdataUtilitiesApiClient
from src.ingestion.config import get_config
from src.ingestion.ingestors.exchange_metadata_ingestor import ExchangeMetadataIngestor
from src.ingestion.monitoring import IngestionMonitor
from src.ingestion.cache import CacheManager, CacheBackend
from src.rate_limit_tracker import record_rate_limit_status


# Configure logging
logger = setup_logger(__name__, log_to_console=True)


async def main():
    """Main ingestion function."""
    parser = argparse.ArgumentParser(
        description="Ingest general exchange metadata using unified framework."
    )
    parser.add_argument(
        "--exchange_type",
        type=str,
        choices=["spot", "futures", "all"],
        default="all",
        help="Type of exchanges to ingest (spot, futures, or all).",
    )
    parser.add_argument(
        "--full_refresh",
        action="store_true",
        help="Perform a full refresh of exchange metadata.",
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
        "--specific_exchanges",
        type=str,
        nargs="+",
        help="Process only specific exchanges (space-separated list).",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Perform a dry run without actually ingesting data.",
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("ENHANCED EXCHANGES GENERAL DATA INGESTION")
    logger.info("=" * 80)
    logger.info(f"Exchange type: {args.exchange_type}")
    logger.info(f"Full refresh: {args.full_refresh}")
    logger.info(f"Monitoring enabled: {args.enable_monitoring}")
    logger.info(f"Caching enabled: {args.enable_caching}")
    logger.info(f"Specific exchanges: {args.specific_exchanges or 'All'}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 80)

    # Record start of ingestion
    record_rate_limit_status("ingest_exchanges_general_v2", "pre")

    # Initialize configuration
    config = get_config()

    # Override metadata settings if full refresh is requested
    if args.full_refresh:
        config.update_config("ingestion", metadata_full_refresh=True)

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
            default_ttl=3600,  # 1 hour for exchange metadata
            max_memory_entries=500,
        )
        await cache_manager.start_background_cleanup()
        logger.info("Caching enabled")

    # Initialize database connection
    db_connection = None
    api_client = None
    ingestor = None

    try:
        # Initialize database connection
        db_connection = DbConnectionManager()
        logger.info("Database connection established")

        # Initialize API client
        api_client = CcdataUtilitiesApiClient()
        logger.info("Utilities API client initialized")

        # Initialize the ingestor
        ingestor = ExchangeMetadataIngestor(
            api_client=api_client,
            db_client=db_connection,
            config=config,
        )
        logger.info("Exchange metadata ingestor initialized")

        # Start performance tracking
        tracking_id = None
        if monitor:
            tracking_id = monitor.start_performance_tracking(
                "exchange_metadata_ingestion",
                metadata={
                    "exchange_type": args.exchange_type,
                    "full_refresh": args.full_refresh,
                    "specific_exchanges": args.specific_exchanges,
                    "dry_run": args.dry_run,
                },
            )

        if args.dry_run:
            logger.info("DRY RUN MODE - No data will be ingested")

            # Just test the API connection
            try:
                # Test API call to get exchange list
                test_response = await asyncio.to_thread(api_client.get_all_exchanges)

                if test_response and "Data" in test_response:
                    exchanges = test_response["Data"]

                    # Filter by type if specified
                    if args.exchange_type != "all":
                        exchanges = [
                            ex
                            for ex in exchanges
                            if ex.get("TYPE", "").lower() == args.exchange_type.lower()
                        ]

                    # Filter by specific exchanges if provided
                    if args.specific_exchanges:
                        exchanges = [
                            ex
                            for ex in exchanges
                            if ex.get("INTERNAL_NAME") in args.specific_exchanges
                        ]

                    logger.info(f"Would process {len(exchanges)} exchanges:")
                    for i, exchange in enumerate(exchanges[:10]):  # Show first 10
                        logger.info(
                            f"  {i+1}. {exchange.get('INTERNAL_NAME')} ({exchange.get('TYPE', 'unknown')})"
                        )
                    if len(exchanges) > 10:
                        logger.info(f"  ... and {len(exchanges) - 10} more")

                    result = {
                        "status": "success",
                        "dry_run": True,
                        "total_exchanges": len(exchanges),
                        "sample_exchanges": [
                            ex.get("INTERNAL_NAME") for ex in exchanges[:5]
                        ],
                    }
                else:
                    logger.warning("No exchanges found in API response")
                    result = {
                        "status": "warning",
                        "dry_run": True,
                        "total_exchanges": 0,
                        "message": "No exchanges found",
                    }

            except Exception as e:
                logger.error(f"Error testing API connection: {e}")
                result = {"status": "error", "dry_run": True, "error": str(e)}
        else:
            # Perform actual ingestion
            logger.info("Starting exchange metadata ingestion...")

            # Prepare ingestion parameters
            kwargs = {}
            if args.specific_exchanges:
                kwargs["exchanges"] = args.specific_exchanges
            if args.exchange_type != "all":
                kwargs["exchange_types"] = [args.exchange_type]

            result = await ingestor.ingest_metadata(**kwargs)

        # Log results
        logger.info("=" * 80)
        logger.info("INGESTION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Status: {result.get('status', 'unknown')}")

        if not args.dry_run:
            logger.info(f"Records processed: {result.get('records_processed', 0)}")
            logger.info(f"Records inserted: {result.get('records_inserted', 0)}")
            logger.info(f"Duration: {result.get('duration_seconds', 0):.2f} seconds")

            # Calculate processing rate
            records_processed = result.get("records_processed", 0)
            duration = result.get("duration_seconds", 0)
            if duration > 0 and records_processed > 0:
                rate = records_processed / duration
                logger.info(f"Processing rate: {rate:.2f} records/second")

        # End performance tracking
        if monitor and tracking_id:
            monitor.end_performance_tracking(
                tracking_id,
                records_processed=result.get("records_processed", 0),
                records_inserted=result.get("records_inserted", 0),
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

        # Show exchange statistics if not dry run
        if not args.dry_run and result.get("status") == "success":
            try:
                # Get exchange count by type
                exchange_counts = await ingestor.get_exchange_count_by_type()
                if exchange_counts:
                    logger.info("Exchange counts by type:")
                    for exchange_type, count in exchange_counts.items():
                        logger.info(f"  {exchange_type}: {count}")
            except Exception as e:
                logger.warning(f"Could not retrieve exchange statistics: {e}")

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
                message=f"Fatal error in exchange metadata ingestion: {str(e)}",
                source="ingest_exchanges_general_v2",
                metadata={"error": str(e), "exchange_type": args.exchange_type},
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
        record_rate_limit_status("ingest_exchanges_general_v2", "post")

    logger.info("Script execution completed")
    sys.exit(exit_code)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
