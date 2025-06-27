"""
Unified futures data ingestor implementation.

This module provides the FuturesDataIngestor class for ingesting various types of
futures data (OHLCV, Funding Rate, Open Interest) from the CryptoCompare API.
Enhanced version of the original FuturesIngestor with improved architecture.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Literal
import logging

from ..base import TimeSeriesIngestor
from ...data_api.futures_api_client import CcdataFuturesApiClient
from ...db.utils import to_mysql_datetime, ensure_utc_datetime
from ...rate_limit_tracker import record_rate_limit_status
from ...utils import get_end_of_previous_period, map_interval_to_unit
from ...polars_schemas import (
    get_futures_ohlcv_schema,
    get_futures_funding_rate_schema,
    get_futures_open_interest_schema,
)


FuturesDataType = Literal["ohlcv", "funding-rate", "open-interest"]


class FuturesDataIngestor(TimeSeriesIngestor):
    """
    Unified ingestor for futures data (OHLCV, Funding Rate, Open Interest).

    Extends TimeSeriesIngestor to provide specialized functionality for
    ingesting futures market data with proper time series handling,
    backfilling, and incremental updates.
    """

    # Configuration for different data types
    DATA_TYPE_CONFIG = {
        "ohlcv": {
            "api_method": "get_futures_historical_ohlcv",
            "db_table_template": "market.cc_futures_ohlcv_{interval}",
            "get_instruments_sql": "get_futures_instruments.sql",
            "last_update_col": "last_trade_datetime",
            "first_update_col": "first_trade_datetime",
            "record_mapper": "_map_ohlcv_record",
            "schema_getter": get_futures_ohlcv_schema,
        },
        "funding-rate": {
            "api_method": "get_futures_historical_funding_rate_ohlc",
            "db_table_template": "market.cc_futures_funding_rate_ohlc_{interval}",
            "get_instruments_sql": "get_futures_instruments_funding_rate.sql",
            "last_update_col": "last_funding_rate_update_datetime",
            "first_update_col": "first_funding_rate_update_datetime",
            "record_mapper": "_map_funding_rate_record",
            "schema_getter": get_futures_funding_rate_schema,
        },
        "open-interest": {
            "api_method": "get_futures_historical_oi_ohlc",
            "db_table_template": "market.cc_futures_open_interest_ohlc_{interval}",
            "get_instruments_sql": "get_futures_instruments_open_interest.sql",
            "last_update_col": "last_open_interest_update_datetime",
            "first_update_col": "first_open_interest_update_datetime",
            "record_mapper": "_map_open_interest_record",
            "schema_getter": get_futures_open_interest_schema,
        },
    }

    def __init__(
        self,
        api_client: CcdataFuturesApiClient,
        db_client: Any,
        config: Any,
        interval: str,
        data_type: FuturesDataType,
    ):
        """
        Initialize the futures data ingestor.

        Args:
            api_client: CryptoCompare Futures API client instance
            db_client: Database client instance for data persistence
            config: Configuration object with ingestion settings
            interval: Time interval for the data ('1d', '1h', '1m')
            data_type: Type of futures data ('ohlcv', 'funding-rate', 'open-interest')
        """
        super().__init__(api_client, db_client, config, interval)

        # Validate that we have the correct API client type
        if not isinstance(api_client, CcdataFuturesApiClient):
            raise TypeError("FuturesDataIngestor requires CcdataFuturesApiClient")

        # Validate data type
        if data_type not in self.DATA_TYPE_CONFIG:
            raise ValueError(f"Unsupported data_type: {data_type}")

        self.data_type = data_type
        self.data_type_config = self.DATA_TYPE_CONFIG[data_type]
        self.record_mapper = getattr(self, self.data_type_config["record_mapper"])

    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch futures data from the CryptoCompare API.

        Args:
            **kwargs: API parameters including:
                - market: Exchange market (e.g., 'binance')
                - instrument: Futures instrument (e.g., 'BTC-USDT-PERP')
                - start_date: Start date for data fetching
                - limit: Maximum number of records to fetch

        Returns:
            List of raw futures data dictionaries from the API

        Raises:
            ValueError: If required parameters are missing
            Exception: If API call fails
        """
        try:
            # Extract required parameters
            market = kwargs.get("market")
            instrument = kwargs.get("instrument")
            start_date = kwargs.get("start_date")
            limit = kwargs.get(
                "limit",
                self.config.ingestion.max_limit_per_call.get(self.interval, 2000),
            )

            if not market or not instrument:
                raise ValueError(
                    "Both 'market' and 'instrument' parameters are required"
                )

            self.logger.info(
                f"Fetching futures {self.data_type} data for {market}:{instrument} "
                f"interval={self.interval} from {start_date}"
            )

            # Convert start_date to timestamp if provided
            to_ts = None
            if start_date:
                if isinstance(start_date, datetime):
                    to_ts = int(start_date.timestamp())
                else:
                    to_ts = start_date

            # Get the API method
            api_method = getattr(self.api_client, self.data_type_config["api_method"])

            # Call the API method
            response = await asyncio.to_thread(
                api_method,
                interval=map_interval_to_unit(self.interval),
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
                record_rate_limit_status(f"futures_{self.data_type}_api", "no_data")
                return []

            data = response["Data"]
            if not data:
                self.logger.info(f"Empty data set received for {market}:{instrument}")
                return []

            self.logger.info(
                f"Received {len(data)} futures {self.data_type} records from API"
            )
            record_rate_limit_status(f"futures_{self.data_type}_api", "success")
            return data

        except Exception as e:
            self.logger.error(f"Error fetching futures {self.data_type} data: {e}")
            record_rate_limit_status(f"futures_{self.data_type}_api", "failure")
            raise

    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single raw futures entry into standardized database format.

        Args:
            raw_entry: Single raw futures data entry from API response

        Returns:
            Transformed data dictionary ready for database insertion
        """
        try:
            return self.record_mapper(raw_entry)
        except Exception as e:
            self.logger.error(f"Error transforming futures {self.data_type} data: {e}")
            raise

    def _map_ohlcv_record(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Maps a raw OHLCV API entry to a standardized record."""
        return {
            "datetime": datetime.fromtimestamp(entry["TIMESTAMP"], tz=timezone.utc),
            "market": entry.get("MARKET"),
            "instrument": entry.get("INSTRUMENT"),
            "mapped_instrument": entry.get("MAPPED_INSTRUMENT"),
            "type": entry.get("TYPE"),
            "index_underlying": entry.get("INDEX_UNDERLYING"),
            "quote_currency": entry.get("QUOTE_CURRENCY"),
            "settlement_currency": entry.get("SETTLEMENT_CURRENCY"),
            "contract_currency": entry.get("CONTRACT_CURRENCY"),
            "denomination_type": entry.get("DENOMINATION_TYPE"),
            "open": entry.get("OPEN"),
            "high": entry.get("HIGH"),
            "low": entry.get("LOW"),
            "close": entry.get("CLOSE"),
            "number_of_contracts": entry.get("NUMBER_OF_CONTRACTS"),
            "volume": entry.get("VOLUME"),
            "quote_volume": entry.get("QUOTE_VOLUME"),
            "volume_buy": entry.get("VOLUME_BUY"),
            "quote_volume_buy": entry.get("QUOTE_VOLUME_BUY"),
            "volume_sell": entry.get("VOLUME_SELL"),
            "quote_volume_sell": entry.get("QUOTE_VOLUME_SELL"),
            "volume_unknown": entry.get("VOLUME_UNKNOWN"),
            "quote_volume_unknown": entry.get("QUOTE_VOLUME_UNKNOWN"),
            "total_trades": entry.get("TOTAL_TRADES"),
            "total_trades_buy": entry.get("TOTAL_TRADES_BUY"),
            "total_trades_sell": entry.get("TOTAL_TRADES_SELL"),
            "total_trades_unknown": entry.get("TOTAL_TRADES_UNKNOWN"),
            "first_trade_timestamp": (
                datetime.fromtimestamp(
                    entry.get("FIRST_TRADE_TIMESTAMP"), tz=timezone.utc
                )
                if entry.get("FIRST_TRADE_TIMESTAMP") is not None
                else None
            ),
            "last_trade_timestamp": (
                datetime.fromtimestamp(
                    entry.get("LAST_TRADE_TIMESTAMP"), tz=timezone.utc
                )
                if entry.get("LAST_TRADE_TIMESTAMP") is not None
                else None
            ),
            "first_trade_price": entry.get("FIRST_TRADE_PRICE"),
            "high_trade_price": entry.get("HIGH_TRADE_PRICE"),
            "high_trade_timestamp": (
                datetime.fromtimestamp(
                    entry.get("HIGH_TRADE_TIMESTAMP"), tz=timezone.utc
                )
                if entry.get("HIGH_TRADE_TIMESTAMP") is not None
                else None
            ),
            "low_trade_price": entry.get("LOW_TRADE_PRICE"),
            "low_trade_timestamp": (
                datetime.fromtimestamp(
                    entry.get("LOW_TRADE_TIMESTAMP"), tz=timezone.utc
                )
                if entry.get("LOW_TRADE_TIMESTAMP") is not None
                else None
            ),
            "last_trade_price": entry.get("LAST_TRADE_PRICE"),
            "collected_at": to_mysql_datetime(datetime.now(timezone.utc)),
        }

    def _map_funding_rate_record(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Maps a raw Funding Rate API entry to a standardized record."""
        return {
            "datetime": datetime.fromtimestamp(entry["TIMESTAMP"], tz=timezone.utc),
            "market": entry.get("MARKET"),
            "instrument": entry.get("INSTRUMENT"),
            "mapped_instrument": entry.get("MAPPED_INSTRUMENT"),
            "type": entry.get("TYPE"),
            "index_underlying": entry.get("INDEX_UNDERLYING"),
            "quote_currency": entry.get("QUOTE_CURRENCY"),
            "settlement_currency": entry.get("SETTLEMENT_CURRENCY"),
            "contract_currency": entry.get("CONTRACT_CURRENCY"),
            "denomination_type": entry.get("DENOMINATION_TYPE"),
            "interval_ms": entry.get("INTERVAL_MS"),
            "open_fr": entry.get("OPEN"),
            "high_fr": entry.get("HIGH"),
            "low_fr": entry.get("LOW"),
            "close_fr": entry.get("CLOSE"),
            "total_funding_rate_updates": entry.get("TOTAL_FUNDING_RATE_UPDATES"),
            "collected_at": to_mysql_datetime(datetime.now(timezone.utc)),
        }

    def _map_open_interest_record(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Maps a raw Open Interest API entry to a standardized record."""
        return {
            "datetime": datetime.fromtimestamp(entry["TIMESTAMP"], tz=timezone.utc),
            "market": entry.get("MARKET"),
            "instrument": entry.get("INSTRUMENT"),
            "mapped_instrument": entry.get("MAPPED_INSTRUMENT"),
            "type": entry.get("TYPE"),
            "index_underlying": entry.get("INDEX_UNDERLYING"),
            "quote_currency": entry.get("QUOTE_CURRENCY"),
            "settlement_currency": entry.get("SETTLEMENT_CURRENCY"),
            "contract_currency": entry.get("CONTRACT_CURRENCY"),
            "denomination_type": entry.get("DENOMINATION_TYPE"),
            "open_oi_contracts": entry.get("OPEN_SETTLEMENT"),
            "high_oi_contracts": entry.get("HIGH_SETTLEMENT"),
            "low_oi_contracts": entry.get("LOW_SETTLEMENT"),
            "close_oi_contracts": entry.get("CLOSE_SETTLEMENT"),
            "open_oi_quote": entry.get("OPEN_QUOTE"),
            "high_oi_quote": entry.get("HIGH_QUOTE"),
            "low_oi_quote": entry.get("LOW_QUOTE"),
            "close_oi_quote": entry.get("CLOSE_QUOTE"),
            "open_mark_price": entry.get("OPEN_MARK_PRICE"),
            "high_oi_mark_price": entry.get("HIGH_SETTLEMENT_MARK_PRICE"),
            "high_mark_price": entry.get("HIGH_MARK_PRICE"),
            "high_mark_price_oi": entry.get("HIGH_MARK_PRICE_SETTLEMENT"),
            "high_quote_mark_price": entry.get("HIGH_QUOTE_MARK_PRICE"),
            "low_oi_mark_price": entry.get("LOW_SETTLEMENT_MARK_PRICE"),
            "low_mark_price": entry.get("LOW_MARK_PRICE"),
            "low_mark_price_oi": entry.get("LOW_MARK_PRICE_SETTLEMENT"),
            "low_quote_mark_price": entry.get("LOW_QUOTE_MARK_PRICE"),
            "close_mark_price": entry.get("CLOSE_MARK_PRICE"),
            "total_open_interest_updates": entry.get("TOTAL_OPEN_INTEREST_UPDATES"),
            "collected_at": to_mysql_datetime(datetime.now(timezone.utc)),
        }

    def _get_schema(self) -> Dict[str, Any]:
        """
        Return the database schema for futures data.

        Returns:
            Dictionary representing the data schema for Polars DataFrame
        """
        schema_getter = self.data_type_config["schema_getter"]
        return schema_getter() if schema_getter else None

    def _get_db_table_name(self) -> str:
        """
        Return the target database table name for futures data.

        Returns:
            String name of the target database table
        """
        return self.data_type_config["db_table_template"].format(interval=self.interval)

    def _get_conflict_columns(self) -> List[str]:
        """
        Get the columns used for conflict resolution during upserts.

        Returns:
            List of column names used for conflict resolution
        """
        return ["datetime", "market", "mapped_instrument"]

    async def get_futures_exchanges(self) -> List[str]:
        """
        Fetch all futures exchanges from the database.

        Returns:
            List of exchange internal names
        """
        try:
            query = self.db_client._load_sql("get_all_futures_exchanges.sql")
            self.logger.info("Fetching all futures exchanges from database...")

            results = await asyncio.to_thread(
                self.db_client._execute_query, query, fetch=True
            )

            if results:
                exchanges = [row[0] for row in results]
                self.logger.info(
                    f"Found {len(exchanges)} futures exchanges in database."
                )
                return exchanges
            else:
                self.logger.warning("No futures exchanges found in database.")
                return []

        except FileNotFoundError:
            self.logger.error("SQL script 'get_all_futures_exchanges.sql' not found.")
            return []
        except Exception as e:
            self.logger.error(
                f"Error fetching all futures exchanges from database: {e}"
            )
            return []

    async def get_futures_instruments(
        self, exchanges: List[str], instrument_statuses: List[str]
    ) -> List[tuple]:
        """
        Fetch futures instruments for the given exchanges and statuses from the database.

        Args:
            exchanges: List of exchange internal names
            instrument_statuses: List of instrument statuses to filter by

        Returns:
            List of (exchange_internal_name, mapped_instrument_symbol, last_update_datetime,
                    first_update_datetime, instrument_status) tuples
        """
        if not exchanges:
            self.logger.warning(
                "Exchanges list is empty, returning no futures instruments."
            )
            return []

        try:
            query = self.db_client._load_sql(
                self.data_type_config["get_instruments_sql"]
            )
            params = (tuple(exchanges), tuple(instrument_statuses))

            self.logger.info(
                f"Fetching futures instruments for exchanges: {exchanges} with statuses: {instrument_statuses}..."
            )

            results = await asyncio.to_thread(
                self.db_client._execute_query, query, params=params, fetch=True
            )

            if results:
                instruments = []
                for row in results:
                    # Dynamically get the last and first update datetimes based on config
                    last_update_dt = ensure_utc_datetime(row[2])
                    first_update_dt = ensure_utc_datetime(row[3])
                    instrument_status = row[4]
                    instruments.append(
                        (
                            row[0],
                            row[1],
                            last_update_dt,
                            first_update_dt,
                            instrument_status,
                        )
                    )
                self.logger.info(
                    f"Found {len(instruments)} futures instruments in database."
                )
                return instruments
            else:
                self.logger.warning(
                    "No futures instruments found in database for the given criteria."
                )
                return []

        except FileNotFoundError:
            self.logger.error(
                f"SQL script '{self.data_type_config['get_instruments_sql']}' not found."
            )
            return []
        except Exception as e:
            self.logger.error(f"Error fetching futures instruments from database: {e}")
            return []

    async def ingest_for_instrument(
        self,
        market: str,
        mapped_instrument: str,
        last_update_datetime: Optional[datetime] = None,
        first_update_datetime: Optional[datetime] = None,
        instrument_status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """
        Ingest data for a specific futures instrument.

        Args:
            market: Exchange market name
            mapped_instrument: Mapped instrument symbol
            last_update_datetime: Last update datetime from database
            first_update_datetime: First update datetime from database
            instrument_status: Instrument status (ACTIVE, EXPIRED, etc.)

        Returns:
            Dictionary containing ingestion results and statistics
        """
        # Get last ingested timestamp for this specific instrument
        last_timestamp = await self._get_last_ingested_timestamp(
            market=market, instrument=mapped_instrument
        )

        # Calculate date range for fetching
        today_utc = datetime.now(timezone.utc)
        end_of_previous_period = get_end_of_previous_period(
            today_utc, map_interval_to_unit(self.interval)
        )

        # Determine the start date for fetching
        if last_timestamp:
            start_date_to_fetch = last_timestamp + timedelta(
                **{map_interval_to_unit(self.interval): 1}
            )
            self.logger.info(
                f"Continuing ingestion for {mapped_instrument} on {market} from {start_date_to_fetch}"
            )
        else:
            if first_update_datetime:
                start_date_to_fetch = first_update_datetime
                self.logger.info(
                    f"No existing data for {mapped_instrument} on {market}. "
                    f"Backfilling from first update datetime: {start_date_to_fetch}"
                )
            else:
                # Fallback to configured backfill period
                start_date_to_fetch = datetime.now(timezone.utc) - timedelta(
                    days=self.max_backfill_days
                )
                self.logger.info(
                    f"No existing data for {mapped_instrument} on {market} and no first update datetime. "
                    f"Backfilling from {start_date_to_fetch}"
                )

        # Determine the effective end timestamp for fetching
        if instrument_status == "ACTIVE":
            effective_end_date = end_of_previous_period
        else:
            effective_end_date = (
                last_update_datetime if last_update_datetime else end_of_previous_period
            )

        # Perform ingestion with calculated parameters
        kwargs = {
            "market": market,
            "instrument": mapped_instrument,
            "start_date": start_date_to_fetch,
        }

        return await self.ingest(**kwargs)

    async def ingest_multiple_instruments(
        self,
        exchanges: Optional[List[str]] = None,
        instruments: Optional[List[str]] = None,
        instrument_statuses: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest data for multiple futures instruments in parallel.

        Args:
            exchanges: List of exchange names to filter by
            instruments: List of specific instruments to ingest
            instrument_statuses: List of instrument statuses to filter by

        Returns:
            Dictionary containing aggregated ingestion results
        """
        # Use default values from config if not provided
        if exchanges is None:
            exchanges = await self.get_futures_exchanges()
        if instrument_statuses is None:
            instrument_statuses = self.config.ingestion.futures_instrument_statuses

        self.logger.info(
            f"Starting parallel ingestion for futures {self.data_type} data "
            f"across {len(exchanges)} exchanges"
        )

        # Get instruments from database
        db_instruments = await self.get_futures_instruments(
            exchanges, instrument_statuses
        )

        # Filter by specific instruments if provided
        if instruments:
            db_instruments = [inst for inst in db_instruments if inst[1] in instruments]

        if not db_instruments:
            self.logger.warning("No instruments found for ingestion")
            return {
                "status": "success",
                "total_instruments": 0,
                "successful_instruments": 0,
                "failed_instruments": 0,
                "total_records_processed": 0,
                "total_records_inserted": 0,
            }

        # Create tasks for parallel execution
        tasks = []
        for (
            exchange,
            mapped_instrument,
            last_update_dt,
            first_update_dt,
            status,
        ) in db_instruments:
            task = self.ingest_for_instrument(
                market=exchange,
                mapped_instrument=mapped_instrument,
                last_update_datetime=last_update_dt,
                first_update_datetime=first_update_dt,
                instrument_status=status,
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
        successful_instruments = 0
        failed_instruments = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Failed to ingest instrument {db_instruments[i][1]}: {result}"
                )
                failed_instruments += 1
            else:
                total_processed += result.get("records_processed", 0)
                total_inserted += result.get("records_inserted", 0)
                if result.get("status") == "success":
                    successful_instruments += 1
                else:
                    failed_instruments += 1

        return {
            "status": "success" if failed_instruments == 0 else "partial_failure",
            "total_instruments": len(db_instruments),
            "successful_instruments": successful_instruments,
            "failed_instruments": failed_instruments,
            "total_records_processed": total_processed,
            "total_records_inserted": total_inserted,
        }
