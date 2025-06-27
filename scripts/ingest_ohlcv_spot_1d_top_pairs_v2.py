#!/usr/bin/env python3
"""
Enhanced spot OHLCV data ingestion script using the unified framework.

This script replaces the original ingest_ohlcv_spot_1d_top_pairs.py with
improved architecture, better error handling, and monitoring capabilities.

Key improvements:
- Uses the unified ingestion framework
- Async processing for better performance
- Comprehensive monitoring and alerting
- Caching for frequently accessed data
- Better error handling and recovery
- Support for multiple intervals
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
from src.data_api.spot_api_client import CcdataSpotApiClient
from src.ingestion.config import get_config
from src.ingestion.ingestors.spot_ohlcv_ingestor import SpotOHLCVIngestor
from src.ingestion.monitoring import IngestionMonitor
from src.ingestion.cache import CacheManager, CacheBackend
from src.rate_limit_tracker import record_rate_limit_status


# Configure logging
logger = setup_logger(__name__, log_to_console=True)


async def get_top_trading_pairs(
    db_connection: DbConnectionManager,
    cache_manager: Optional[CacheManager] = None,
    limit: int = 100,
) -> List[Dict[str, str]]:
    """
    Get top trading pairs from the database.

    Args:
        db_connection: Database connection manager
        cache_manager: Optional cache manager
        limit: Maximum number of pairs to return

    Returns:
        List of dictionaries with 'market' and 'instrument' keys
    """
    cache_key = f"top_trading_pairs:{limit}"

    # Try cache first if available
    if cache_manager:
        cached_pairs = await cache_manager.get(cache_key)
        if cached_pairs:
            logger.info(f"Retrieved {len(cached_pairs)} trading pairs from cache")
            return cached_pairs

    try:
        # Load SQL query
        query = db_connection._load_sql("get_trading_pairs.sql")

        # Execute query with limit
        results = db_connection._execute_query(query, params=(limit,), fetch=True)

        if results:
            trading_pairs = [
                {"market": row[0], "instrument": row[1]} for row in results
            ]

            # Cache the results if cache manager is available
            if cache_manager:
                await cache_manager.set(
                    cache_key, trading_pairs, ttl=1800
                )  # 30 minutes

            logger.info(f"Retrieved {len(trading_pairs)} trading pairs from database")
            return trading_pairs
        else:
            logger.warning("No trading pairs found in database")
            return []

    except Exception as e:
        logger.error(f"Error fetching trading pairs: {e}")
        return []


async def main():
    """Main ingestion function."""
    parser = argparse.ArgumentParser(
        description="Ingest spot OHLCV data for top trading pairs using unified framework."
    )
    parser.add_argument(
        "--pair_limit",
        type=int,
        default=100,
        help="Limit the number of top trading pairs to process.",
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
        "--specific_market",
        type=str,
        help="Process only a specific market (e.g., 'coinbase').",
    )
    parser.add_argument(
        "--specific_instrument",
        type=str,
        help="Process only a specific instrument (e.g., 'BTC-USD').",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Perform a dry run without actually ingesting data.",
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("ENHANCED SPOT OHLCV DATA INGESTION")
    logger.info("=" * 80)
    logger.info(f"Interval: {args.interval}")
    logger.info(f"Pair limit: {args.pair_limit}")
    logger.info(f"Parallel workers: {args.parallel_workers}")
    logger.info(f"Monitoring enabled: {args.enable_monitoring}")
    logger.info(f"Caching enabled: {args.enable_caching}")
    logger.info(f"Specific market: {args.specific_market or 'All'}")
    logger.info(f"Specific instrument: {args.specific_instrument or 'All'}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 80)

    # Record start of ingestion
    record_rate_limit_status("ingest_ohlcv_spot_1d_top_pairs_v2", "pre")

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
            default_ttl=1800,  # 30 minutes for trading pairs
            max_memory_entries=1000,
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
        api_client = CcdataSpotApiClient()
        logger.info("Spot API client initialized")

        # Initialize the ingestor
        ingestor = SpotOHLCVIngestor(
            api_client=api_client,
            db_client=db_connection,
            config=config,
            interval=args.interval,
        )
        logger.info("Spot OHLCV ingestor initialized")

        # Start performance tracking
        tracking_id = None
        if monitor:
            tracking_id = monitor.start_performance_tracking(
                "spot_ohlcv_ingestion",
                metadata={
                    "interval": args.interval,
                    "pair_limit": args.pair_limit,
                    "specific_market": args.specific_market,
                    "specific_instrument": args.specific_instrument,
                    "dry_run": args.dry_run,
                },
            )

        # Get trading pairs to process
        if args.specific_market and args.specific_instrument:
            # Process single specific pair
            trading_pairs = [
                {"market": args.specific_market, "instrument": args.specific_instrument}
            ]
            logger.info(
                f"Processing specific pair: {args.specific_market}:{args.specific_instrument}"
            )
        else:
            # Get top trading pairs
            trading_pairs = await get_top_trading_pairs(
                db_connection, cache_manager, args.pair_limit
            )

            # Filter by specific market if provided
            if args.specific_market:
                trading_pairs = [
                    pair
                    for pair in trading_pairs
                    if pair["market"] == args.specific_market
                ]
                logger.info(
                    f"Filtered to {len(trading_pairs)} pairs for market: {args.specific_market}"
                )

        if not trading_pairs:
            logger.error("No trading pairs found to process")
            sys.exit(1)

        if args.dry_run:
            logger.info("DRY RUN MODE - No data will be ingested")
            logger.info(f"Would process {len(trading_pairs)} trading pairs:")
            for i, pair in enumerate(trading_pairs[:10]):  # Show first 10
                logger.info(f"  {i+1}. {pair['market']}:{pair['instrument']}")
            if len(trading_pairs) > 10:
                logger.info(f"  ... and {len(trading_pairs) - 10} more")

            result = {
                "status": "success",
                "dry_run": True,
                "total_pairs": len(trading_pairs),
                "sample_pairs": trading_pairs[:5],
            }
        else:
            # Perform actual ingestion
            logger.info(
                f"Starting spot OHLCV data ingestion for {len(trading_pairs)} trading pairs..."
            )

            result = await ingestor.ingest_multiple_pairs(
                trading_pairs=trading_pairs,
            )

        # Log results
        logger.info("=" * 80)
        logger.info("INGESTION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Status: {result.get('status', 'unknown')}")

        if not args.dry_run:
            logger.info(f"Total pairs processed: {result.get('total_pairs', 0)}")
            logger.info(f"Successful pairs: {result.get('successful_pairs', 0)}")
            logger.info(f"Failed pairs: {result.get('failed_pairs', 0)}")
            logger.info(
                f"Total records processed: {result.get('total_records_processed', 0)}"
            )
            logger.info(
                f"Total records inserted: {result.get('total_records_inserted', 0)}"
            )

            # Calculate success rate
            total_pairs = result.get("total_pairs", 0)
            successful_pairs = result.get("successful_pairs", 0)
            if total_pairs > 0:
                success_rate = (successful_pairs / total_pairs) * 100
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
                message=f"Fatal error in spot OHLCV ingestion: {str(e)}",
                source="ingest_ohlcv_spot_1d_top_pairs_v2",
                metadata={"error": str(e), "interval": args.interval},
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
        record_rate_limit_status("ingest_ohlcv_spot_1d_top_pairs_v2", "post")

    logger.info("Script execution completed")
    sys.exit(exit_code)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
