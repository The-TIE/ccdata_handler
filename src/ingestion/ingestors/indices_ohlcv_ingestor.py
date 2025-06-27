"""
Indices OHLCV data ingestor implementation.

This module provides the IndicesOHLCVIngestor class for ingesting indices market
OHLCV (Open, High, Low, Close, Volume) time series data from the CryptoCompare API.
Migrated from the original ingest_ohlcv_indices_1d_top_assets.py script.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import logging

from ..base import TimeSeriesIngestor
from ...data_api.indices_ref_rates_api_client import CcdataIndicesRefRatesApiClient
from ...data_api.asset_api_client import CcdataAssetApiClient
from ...db.utils import to_mysql_datetime
from ...rate_limit_tracker import record_rate_limit_status


class IndicesOHLCVIngestor(TimeSeriesIngestor):
    """
    Ingestor for indices OHLCV time series data.

    Extends TimeSeriesIngestor to provide specialized functionality for
    ingesting indices market OHLCV data with proper time series handling,
    backfilling, and incremental updates.
    """

    def __init__(
        self,
        api_client: CcdataIndicesRefRatesApiClient,
        db_client: Any,
        config: Any,
        interval: str,
        asset_api_client: Optional[CcdataAssetApiClient] = None,
    ):
        """
        Initialize the indices OHLCV ingestor.

        Args:
            api_client: CryptoCompare Indices API client instance
            db_client: Database client instance for data persistence
            config: Configuration object with ingestion settings
            interval: Time interval for the data ('1d', '1h', '1m')
            asset_api_client: Optional asset API client for fetching top assets
        """
        super().__init__(api_client, db_client, config, interval)

        # Validate that we have the correct API client type
        if not isinstance(api_client, CcdataIndicesRefRatesApiClient):
            raise TypeError(
                "IndicesOHLCVIngestor requires CcdataIndicesRefRatesApiClient"
            )

        self.asset_api_client = asset_api_client or CcdataAssetApiClient()

    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch indices OHLCV data from the CryptoCompare API.

        Args:
            **kwargs: API parameters including:
                - market: Index family (e.g., 'cadli')
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
                f"Fetching indices OHLCV data for {market}:{instrument} "
                f"interval={self.interval} from {start_date}"
            )

            # Convert start_date to timestamp if provided
            to_ts = None
            if start_date:
                if isinstance(start_date, datetime):
                    to_ts = int(start_date.timestamp())
                else:
                    to_ts = start_date

            # Map interval to time period
            time_period_map = {"1d": "days", "1h": "hours", "1m": "minutes"}
            time_period = time_period_map.get(self.interval)

            if not time_period:
                raise ValueError(f"Unsupported interval: {self.interval}")

            # Call the API method
            response = await asyncio.to_thread(
                self.api_client.get_historical_ohlcv,
                time_period=time_period,
                market=market,
                instrument=instrument,
                to_ts=to_ts,
                limit=limit,
            )

            # Extract data from response
            if not response or "Data" not in response:
                self.logger.warning(
                    f"No data received from API for {market}:{instrument}"
                )
                record_rate_limit_status("indices_ohlcv_api", "no_data")
                return []

            data = response["Data"]
            if not data:
                self.logger.info(f"Empty data set received for {market}:{instrument}")
                return []

            self.logger.info(f"Received {len(data)} indices OHLCV records from API")
            record_rate_limit_status("indices_ohlcv_api", "success")
            return data

        except Exception as e:
            self.logger.error(f"Error fetching indices OHLCV data: {e}")
            record_rate_limit_status("indices_ohlcv_api", "failure")
            raise

    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single raw indices OHLCV entry into standardized database format.

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
                "unit": raw_entry.get("UNIT"),
                "datetime": dt,
                "type": raw_entry.get("TYPE"),
                "market": raw_entry.get("MARKET"),
                "asset": raw_entry.get("ASSET"),  # Extract from instrument if needed
                "quote": raw_entry.get("QUOTE", "USD"),  # Default to USD
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
                "first_message_timestamp": (
                    datetime.fromtimestamp(
                        raw_entry.get("FIRST_MESSAGE_TIMESTAMP"), tz=timezone.utc
                    )
                    if raw_entry.get("FIRST_MESSAGE_TIMESTAMP") is not None
                    else None
                ),
                "last_message_timestamp": (
                    datetime.fromtimestamp(
                        raw_entry.get("LAST_MESSAGE_TIMESTAMP"), tz=timezone.utc
                    )
                    if raw_entry.get("LAST_MESSAGE_TIMESTAMP") is not None
                    else None
                ),
                "first_message_value": raw_entry.get("FIRST_MESSAGE_VALUE"),
                "high_message_value": raw_entry.get("HIGH_MESSAGE_VALUE"),
                "high_message_timestamp": (
                    datetime.fromtimestamp(
                        raw_entry.get("HIGH_MESSAGE_TIMESTAMP"), tz=timezone.utc
                    )
                    if raw_entry.get("HIGH_MESSAGE_TIMESTAMP") is not None
                    else None
                ),
                "low_message_value": raw_entry.get("LOW_MESSAGE_VALUE"),
                "low_message_timestamp": (
                    datetime.fromtimestamp(
                        raw_entry.get("LOW_MESSAGE_TIMESTAMP"), tz=timezone.utc
                    )
                    if raw_entry.get("LOW_MESSAGE_TIMESTAMP") is not None
                    else None
                ),
                "last_message_value": raw_entry.get("LAST_MESSAGE_VALUE"),
                "total_index_updates": raw_entry.get("TOTAL_INDEX_UPDATES"),
                "volume": (
                    float(raw_entry.get("VOLUME", 0))
                    if raw_entry.get("VOLUME") is not None
                    else None
                ),
                "quote_volume": (
                    float(raw_entry.get("QUOTE_VOLUME", 0))
                    if raw_entry.get("QUOTE_VOLUME") is not None
                    else None
                ),
                "volume_top_tier": (
                    float(raw_entry.get("VOLUME_TOP_TIER", 0))
                    if raw_entry.get("VOLUME_TOP_TIER") is not None
                    else None
                ),
                "quote_volume_top_tier": (
                    float(raw_entry.get("QUOTE_VOLUME_TOP_TIER", 0))
                    if raw_entry.get("QUOTE_VOLUME_TOP_TIER") is not None
                    else None
                ),
                "volume_direct": (
                    float(raw_entry.get("VOLUME_DIRECT", 0))
                    if raw_entry.get("VOLUME_DIRECT") is not None
                    else None
                ),
                "quote_volume_direct": (
                    float(raw_entry.get("QUOTE_VOLUME_DIRECT", 0))
                    if raw_entry.get("QUOTE_VOLUME_DIRECT") is not None
                    else None
                ),
                "volume_top_tier_direct": (
                    float(raw_entry.get("VOLUME_TOP_TIER_DIRECT", 0))
                    if raw_entry.get("VOLUME_TOP_TIER_DIRECT") is not None
                    else None
                ),
                "quote_volume_top_tier_direct": (
                    float(raw_entry.get("QUOTE_VOLUME_TOP_TIER_DIRECT", 0))
                    if raw_entry.get("QUOTE_VOLUME_TOP_TIER_DIRECT") is not None
                    else None
                ),
                "collected_at": to_mysql_datetime(datetime.now(timezone.utc)),
            }

            return transformed

        except Exception as e:
            self.logger.error(f"Error transforming indices OHLCV data: {e}")
            raise

    def _get_schema(self) -> Dict[str, Any]:
        """
        Return the database schema for indices OHLCV data.

        Returns:
            Dictionary representing the data schema for Polars DataFrame
        """
        import polars as pl

        return {
            "unit": pl.Utf8,
            "datetime": pl.Datetime(time_zone="UTC"),
            "type": pl.Utf8,
            "market": pl.Utf8,
            "asset": pl.Utf8,
            "quote": pl.Utf8,
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "first_message_timestamp": pl.Datetime(time_zone="UTC"),
            "last_message_timestamp": pl.Datetime(time_zone="UTC"),
            "first_message_value": pl.Float64,
            "high_message_value": pl.Float64,
            "high_message_timestamp": pl.Datetime(time_zone="UTC"),
            "low_message_value": pl.Float64,
            "low_message_timestamp": pl.Datetime(time_zone="UTC"),
            "last_message_value": pl.Float64,
            "total_index_updates": pl.Int64,
            "volume": pl.Float64,
            "quote_volume": pl.Float64,
            "volume_top_tier": pl.Float64,
            "quote_volume_top_tier": pl.Float64,
            "volume_direct": pl.Float64,
            "quote_volume_direct": pl.Float64,
            "volume_top_tier_direct": pl.Float64,
            "quote_volume_top_tier_direct": pl.Float64,
            "collected_at": pl.Datetime(time_zone="UTC"),
        }

    def _get_db_table_name(self) -> str:
        """
        Return the target database table name for indices OHLCV data.

        Returns:
            String name of the target database table
        """
        # Map interval to table suffix
        interval_suffix = {"1d": "1d", "1h": "1h", "1m": "1m"}.get(
            self.interval, self.interval
        )

        return f"market.cc_ohlcv_spot_indices_{interval_suffix}_raw"

    def _get_conflict_columns(self) -> List[str]:
        """
        Get the columns used for conflict resolution during upserts.

        Returns:
            List of column names used for conflict resolution
        """
        return ["datetime", "market", "asset"]

    async def get_top_assets(self, limit: int = 50) -> List[str]:
        """
        Fetch the top assets by 30-day spot quote volume in USD.

        Args:
            limit: Maximum number of top assets to fetch

        Returns:
            List of asset symbols
        """
        try:
            self.logger.info(
                f"Fetching top {limit} assets by SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD..."
            )

            response = await asyncio.to_thread(
                self.asset_api_client.get_top_list_general,
                page_size=limit,
                sort_by="SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD",
                toplist_quote_asset="USD",
            )

            if response and response.get("Data") and response["Data"].get("LIST"):
                assets = [entry["SYMBOL"] for entry in response["Data"]["LIST"]]
                self.logger.info(f"Found {len(assets)} top assets.")
                return assets
            else:
                self.logger.warning("No top assets found or API response was empty.")
                return []

        except Exception as e:
            self.logger.error(f"Error fetching top assets: {e}")
            return []

    async def ingest_for_asset(
        self,
        market: str,
        asset_symbol: str,
        quote_symbol: str = "USD",
        start_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method to ingest data for a specific asset.

        Args:
            market: Index family (e.g., 'cadli')
            asset_symbol: Asset symbol (e.g., 'BTC')
            quote_symbol: Quote symbol (e.g., 'USD')
            start_date: Optional start date for data fetching
            limit: Optional limit on number of records to fetch

        Returns:
            Dictionary containing ingestion results and statistics
        """
        instrument = f"{asset_symbol}-{quote_symbol}"

        kwargs = {
            "market": market,
            "instrument": instrument,
            "asset": asset_symbol,  # Add asset for filtering
        }

        if start_date:
            kwargs["start_date"] = start_date
        if limit:
            kwargs["limit"] = limit

        return await self.ingest_with_backfill(**kwargs)

    async def ingest_top_assets(
        self,
        market: str,
        asset_limit: int = 50,
        quote_symbol: str = "USD",
        start_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Ingest data for top assets by volume.

        Args:
            market: Index family (e.g., 'cadli')
            asset_limit: Maximum number of top assets to process
            quote_symbol: Quote symbol (e.g., 'USD')
            start_date: Optional start date for data fetching

        Returns:
            Dictionary containing aggregated ingestion results
        """
        self.logger.info(f"Starting ingestion for top {asset_limit} assets on {market}")

        # Get top assets
        top_assets = await self.get_top_assets(limit=asset_limit)
        if not top_assets:
            self.logger.error("Failed to retrieve top assets. Aborting.")
            return {
                "status": "failure",
                "error": "Failed to retrieve top assets",
                "total_assets": 0,
                "successful_assets": 0,
                "failed_assets": 0,
            }

        # Create tasks for parallel execution
        tasks = []
        for asset_symbol in top_assets:
            task = self.ingest_for_asset(
                market=market,
                asset_symbol=asset_symbol,
                quote_symbol=quote_symbol,
                start_date=start_date,
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
        successful_assets = 0
        failed_assets = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to ingest asset {top_assets[i]}: {result}")
                failed_assets += 1
            else:
                total_processed += result.get("records_processed", 0)
                total_inserted += result.get("records_inserted", 0)
                if result.get("status") == "success":
                    successful_assets += 1
                else:
                    failed_assets += 1

        return {
            "status": "success" if failed_assets == 0 else "partial_failure",
            "total_assets": len(top_assets),
            "successful_assets": successful_assets,
            "failed_assets": failed_assets,
            "total_records_processed": total_processed,
            "total_records_inserted": total_inserted,
        }
