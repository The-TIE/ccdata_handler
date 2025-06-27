"""
Spot OHLCV data ingestor implementation.

This module provides the SpotOHLCVIngestor class for ingesting spot market
OHLCV (Open, High, Low, Close, Volume) time series data from the CryptoCompare API.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import logging

from ..base import TimeSeriesIngestor
from ...data_api.spot_api_client import CcdataSpotApiClient
from ...db.utils import to_mysql_datetime
from ...rate_limit_tracker import record_rate_limit_status


class SpotOHLCVIngestor(TimeSeriesIngestor):
    """
    Ingestor for spot OHLCV time series data.

    Extends TimeSeriesIngestor to provide specialized functionality for
    ingesting spot market OHLCV data with proper time series handling,
    backfilling, and incremental updates.
    """

    def __init__(
        self,
        api_client: CcdataSpotApiClient,
        db_client: Any,
        config: Any,
        interval: str,
    ):
        """
        Initialize the spot OHLCV ingestor.

        Args:
            api_client: CryptoCompare Spot API client instance
            db_client: Database client instance for data persistence
            config: Configuration object with ingestion settings
            interval: Time interval for the data ('1d', '1h', '1m')
        """
        super().__init__(api_client, db_client, config, interval)

        # Validate that we have the correct API client type
        if not isinstance(api_client, CcdataSpotApiClient):
            raise TypeError("SpotOHLCVIngestor requires CcdataSpotApiClient")

    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch spot OHLCV data from the CryptoCompare API.

        Args:
            **kwargs: API parameters including:
                - market: Exchange market (e.g., 'coinbase')
                - instrument: Trading pair (e.g., 'BTC-USD')
                - start_date: Start date for data fetching
                - limit: Maximum number of records to fetch

        Returns:
            List of raw OHLCV data dictionaries from the API

        Raises:
            ValueError: If required parameters are missing
            Exception: If API call fails
        """
        try:
            # Extract required parameters
            market = kwargs.get("market")
            instrument = kwargs.get("instrument")
            start_date = kwargs.get("start_date")
            limit = kwargs.get("limit", self.config.ingestion.max_api_limit)

            if not market or not instrument:
                raise ValueError(
                    "Both 'market' and 'instrument' parameters are required"
                )

            self.logger.info(
                f"Fetching spot OHLCV data for {market}:{instrument} "
                f"interval={self.interval} from {start_date}"
            )

            # Convert start_date to timestamp if provided
            to_ts = None
            if start_date:
                if isinstance(start_date, datetime):
                    to_ts = int(start_date.timestamp())
                else:
                    to_ts = start_date

            # Call the appropriate API method based on interval
            if self.interval == "1d":
                response = await asyncio.to_thread(
                    self.api_client.get_ohlc_daily,
                    market=market,
                    instrument=instrument,
                    to_ts=to_ts,
                    limit=limit,
                )
            elif self.interval == "1h":
                response = await asyncio.to_thread(
                    self.api_client.get_ohlc_hourly,
                    market=market,
                    instrument=instrument,
                    to_ts=to_ts,
                    limit=limit,
                )
            elif self.interval == "1m":
                response = await asyncio.to_thread(
                    self.api_client.get_ohlc_minute,
                    market=market,
                    instrument=instrument,
                    to_ts=to_ts,
                    limit=limit,
                )
            else:
                raise ValueError(f"Unsupported interval: {self.interval}")

            # Extract data from response
            if not response or "Data" not in response:
                self.logger.warning(
                    f"No data received from API for {market}:{instrument}"
                )
                record_rate_limit_status("spot_ohlcv_api", "no_data")
                return []

            data = response["Data"]
            if not data:
                self.logger.info(f"Empty data set received for {market}:{instrument}")
                return []

            self.logger.info(f"Received {len(data)} OHLCV records from API")
            record_rate_limit_status("spot_ohlcv_api", "success")
            return data

        except Exception as e:
            self.logger.error(f"Error fetching spot OHLCV data: {e}")
            record_rate_limit_status("spot_ohlcv_api", "failure")
            raise

    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single raw OHLCV entry into standardized database format.

        Args:
            raw_entry: Single raw OHLCV data entry from API response

        Returns:
            Transformed data dictionary ready for database insertion
        """
        try:
            # Convert timestamp to datetime
            timestamp = raw_entry.get("TIMESTAMP")
            if timestamp:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            else:
                raise ValueError("Missing TIMESTAMP in raw data")

            # Transform the data to match database schema
            transformed = {
                "datetime": dt,
                "market": raw_entry.get("MARKET", ""),
                "instrument": raw_entry.get("INSTRUMENT", ""),
                "interval_name": self.interval,
                "open": (
                    float(raw_entry.get("OPEN", 0))
                    if raw_entry.get("OPEN") is not None
                    else None
                ),
                "high": (
                    float(raw_entry.get("HIGH", 0))
                    if raw_entry.get("HIGH") is not None
                    else None
                ),
                "low": (
                    float(raw_entry.get("LOW", 0))
                    if raw_entry.get("LOW") is not None
                    else None
                ),
                "close": (
                    float(raw_entry.get("CLOSE", 0))
                    if raw_entry.get("CLOSE") is not None
                    else None
                ),
                "volume_from": (
                    float(raw_entry.get("VOLUMEFROM", 0))
                    if raw_entry.get("VOLUMEFROM") is not None
                    else None
                ),
                "volume_to": (
                    float(raw_entry.get("VOLUMETO", 0))
                    if raw_entry.get("VOLUMETO") is not None
                    else None
                ),
                "total_trades": (
                    int(raw_entry.get("TOTAL_TRADES", 0))
                    if raw_entry.get("TOTAL_TRADES") is not None
                    else None
                ),
                "created_at": to_mysql_datetime(datetime.now(timezone.utc)),
                "updated_at": to_mysql_datetime(datetime.now(timezone.utc)),
            }

            return transformed

        except Exception as e:
            self.logger.error(f"Error transforming OHLCV data: {e}")
            raise

    def _get_schema(self) -> Dict[str, Any]:
        """
        Return the database schema for spot OHLCV data.

        Returns:
            Dictionary representing the data schema for Polars DataFrame
        """
        import polars as pl

        return {
            "datetime": pl.Datetime(time_zone="UTC"),
            "market": pl.Utf8,
            "instrument": pl.Utf8,
            "interval_name": pl.Utf8,
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "volume_from": pl.Float64,
            "volume_to": pl.Float64,
            "total_trades": pl.Int64,
            "created_at": pl.Datetime(time_zone="UTC"),
            "updated_at": pl.Datetime(time_zone="UTC"),
        }

    def _get_db_table_name(self) -> str:
        """
        Return the target database table name for spot OHLCV data.

        Returns:
            String name of the target database table
        """
        # Map interval to table suffix
        interval_suffix = {"1d": "1d", "1h": "1h", "1m": "1m"}.get(
            self.interval, self.interval
        )

        return f"market.ohlcv_spot_{interval_suffix}_raw"

    def _get_conflict_columns(self) -> List[str]:
        """
        Get the columns used for conflict resolution during upserts.

        Returns:
            List of column names used for conflict resolution
        """
        return ["datetime", "market", "instrument"]

    async def ingest_for_trading_pair(
        self,
        market: str,
        instrument: str,
        start_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method to ingest data for a specific trading pair.

        Args:
            market: Exchange market (e.g., 'coinbase')
            instrument: Trading pair (e.g., 'BTC-USD')
            start_date: Optional start date for data fetching
            limit: Optional limit on number of records to fetch

        Returns:
            Dictionary containing ingestion results and statistics
        """
        kwargs = {
            "market": market,
            "instrument": instrument,
        }

        if start_date:
            kwargs["start_date"] = start_date
        if limit:
            kwargs["limit"] = limit

        return await self.ingest_with_backfill(**kwargs)

    async def ingest_multiple_pairs(
        self,
        trading_pairs: List[Dict[str, str]],
        start_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Ingest data for multiple trading pairs in parallel.

        Args:
            trading_pairs: List of dictionaries with 'market' and 'instrument' keys
            start_date: Optional start date for data fetching
            limit: Optional limit on number of records to fetch per pair

        Returns:
            Dictionary containing aggregated ingestion results
        """
        self.logger.info(
            f"Starting parallel ingestion for {len(trading_pairs)} trading pairs"
        )

        # Create tasks for parallel execution
        tasks = []
        for pair in trading_pairs:
            task = self.ingest_for_trading_pair(
                market=pair["market"],
                instrument=pair["instrument"],
                start_date=start_date,
                limit=limit,
            )
            tasks.append(task)

        # Execute tasks with controlled concurrency
        semaphore = asyncio.Semaphore(self.config.ingestion.parallel_workers)

        async def bounded_task(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(
            *[bounded_task(task) for task in tasks], return_exceptions=True
        )

        # Aggregate results
        total_processed = 0
        total_inserted = 0
        successful_pairs = 0
        failed_pairs = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to ingest pair {trading_pairs[i]}: {result}")
                failed_pairs += 1
            else:
                total_processed += result.get("records_processed", 0)
                total_inserted += result.get("records_inserted", 0)
                if result.get("status") == "success":
                    successful_pairs += 1
                else:
                    failed_pairs += 1

        return {
            "status": "success" if failed_pairs == 0 else "partial_failure",
            "total_pairs": len(trading_pairs),
            "successful_pairs": successful_pairs,
            "failed_pairs": failed_pairs,
            "total_records_processed": total_processed,
            "total_records_inserted": total_inserted,
        }
