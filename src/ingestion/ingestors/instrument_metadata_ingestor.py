"""
Instrument metadata ingestor implementation.

This module provides the InstrumentMetadataIngestor class for ingesting spot and
futures instrument metadata from the CryptoCompare API. This includes exchange
instrument mappings, trading pair information, and instrument status data.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Literal
import logging

from ..base import MetadataIngestor
from ...data_api.spot_api_client import CcdataSpotApiClient
from ...data_api.futures_api_client import CcdataFuturesApiClient
from ...db.utils import to_mysql_datetime
from ...rate_limit_tracker import record_rate_limit_status


InstrumentType = Literal["spot", "futures"]


class InstrumentMetadataIngestor(MetadataIngestor):
    """
    Ingestor for instrument metadata (spot and futures).

    Extends MetadataIngestor to provide specialized functionality for
    ingesting instrument metadata with change detection and full refresh capabilities.
    """

    def __init__(
        self,
        api_client: Any,
        db_client: Any,
        config: Any,
        instrument_type: InstrumentType,
    ):
        """
        Initialize the instrument metadata ingestor.

        Args:
            api_client: API client instance (Spot or Futures)
            db_client: Database client instance for data persistence
            config: Configuration object with ingestion settings
            instrument_type: Type of instruments ('spot' or 'futures')
        """
        super().__init__(api_client, db_client, config)

        # Validate instrument type
        if instrument_type not in ["spot", "futures"]:
            raise ValueError(f"Unsupported instrument_type: {instrument_type}")

        self.instrument_type = instrument_type

        # Validate API client type based on instrument type
        if instrument_type == "spot" and not isinstance(
            api_client, CcdataSpotApiClient
        ):
            raise TypeError("Spot instrument metadata requires CcdataSpotApiClient")
        elif instrument_type == "futures" and not isinstance(
            api_client, CcdataFuturesApiClient
        ):
            raise TypeError(
                "Futures instrument metadata requires CcdataFuturesApiClient"
            )

    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch instrument metadata from the CryptoCompare API.

        Args:
            **kwargs: API parameters including:
                - exchanges: List of exchange names to fetch instruments for
                - instrument_statuses: List of statuses to filter by

        Returns:
            List of raw instrument metadata dictionaries from the API

        Raises:
            Exception: If API call fails
        """
        try:
            exchanges = kwargs.get("exchanges", [])
            instrument_statuses = kwargs.get("instrument_statuses", ["ACTIVE"])

            if not exchanges:
                # Get all exchanges if none specified
                exchanges = await self._get_all_exchanges()

            self.logger.info(
                f"Fetching {self.instrument_type} instrument metadata for "
                f"{len(exchanges)} exchanges with statuses: {instrument_statuses}"
            )

            all_instruments = []

            for exchange in exchanges:
                try:
                    if self.instrument_type == "spot":
                        # Fetch spot instruments for this exchange
                        response = await asyncio.to_thread(
                            self.api_client.get_exchange_instruments,
                            exchange=exchange,
                        )
                    else:
                        # Fetch futures instruments for this exchange
                        response = await asyncio.to_thread(
                            self.api_client.get_exchange_instruments,
                            exchange=exchange,
                        )

                    if response and "Data" in response:
                        instruments = response["Data"]
                        if instruments:
                            # Filter by status if specified
                            if instrument_statuses:
                                instruments = [
                                    inst
                                    for inst in instruments
                                    if inst.get("INSTRUMENT_STATUS")
                                    in instrument_statuses
                                ]

                            # Add exchange information to each instrument
                            for instrument in instruments:
                                instrument["EXCHANGE"] = exchange

                            all_instruments.extend(instruments)
                            self.logger.info(
                                f"Received {len(instruments)} {self.instrument_type} instruments from {exchange}"
                            )
                        else:
                            self.logger.info(
                                f"No {self.instrument_type} instruments found for {exchange}"
                            )
                    else:
                        self.logger.warning(f"No data received for {exchange}")

                except Exception as e:
                    self.logger.error(f"Error fetching instruments for {exchange}: {e}")
                    continue

                # Small delay to avoid rate limiting
                await asyncio.sleep(self.config.ingestion.api_call_delay)

            self.logger.info(
                f"Total {self.instrument_type} instruments fetched: {len(all_instruments)}"
            )
            record_rate_limit_status(
                f"{self.instrument_type}_instruments_api", "success"
            )
            return all_instruments

        except Exception as e:
            self.logger.error(
                f"Error fetching {self.instrument_type} instrument metadata: {e}"
            )
            record_rate_limit_status(
                f"{self.instrument_type}_instruments_api", "failure"
            )
            raise

    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single raw instrument entry into standardized database format.

        Args:
            raw_entry: Single raw instrument data entry from API response

        Returns:
            Transformed data dictionary ready for database insertion
        """
        try:
            if self.instrument_type == "spot":
                return self._transform_spot_instrument(raw_entry)
            else:
                return self._transform_futures_instrument(raw_entry)

        except Exception as e:
            self.logger.error(
                f"Error transforming {self.instrument_type} instrument data: {e}"
            )
            raise

    def _transform_spot_instrument(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a spot instrument entry."""
        return {
            "exchange_internal_name": raw_entry.get("EXCHANGE"),
            "instrument_symbol": raw_entry.get("INSTRUMENT"),
            "mapped_instrument_symbol": raw_entry.get("MAPPED_INSTRUMENT"),
            "base_asset": raw_entry.get("BASE"),
            "quote_asset": raw_entry.get("QUOTE"),
            "instrument_status": raw_entry.get("INSTRUMENT_STATUS"),
            "first_trade_datetime": (
                datetime.fromtimestamp(raw_entry.get("FIRST_TRADE_TS"), tz=timezone.utc)
                if raw_entry.get("FIRST_TRADE_TS")
                else None
            ),
            "last_trade_datetime": (
                datetime.fromtimestamp(raw_entry.get("LAST_TRADE_TS"), tz=timezone.utc)
                if raw_entry.get("LAST_TRADE_TS")
                else None
            ),
            "instrument_metadata": raw_entry.get("INSTRUMENT_METADATA", {}),
            "collected_at": to_mysql_datetime(datetime.now(timezone.utc)),
            "updated_at": to_mysql_datetime(datetime.now(timezone.utc)),
        }

    def _transform_futures_instrument(
        self, raw_entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform a futures instrument entry."""
        return {
            "exchange_internal_name": raw_entry.get("EXCHANGE"),
            "instrument_symbol": raw_entry.get("INSTRUMENT"),
            "mapped_instrument_symbol": raw_entry.get("MAPPED_INSTRUMENT"),
            "base_asset": raw_entry.get("BASE"),
            "quote_asset": raw_entry.get("QUOTE"),
            "instrument_status": raw_entry.get("INSTRUMENT_STATUS"),
            "instrument_type": raw_entry.get("TYPE"),
            "contract_currency": raw_entry.get("CONTRACT_CURRENCY"),
            "settlement_currency": raw_entry.get("SETTLEMENT_CURRENCY"),
            "index_underlying": raw_entry.get("INDEX_UNDERLYING"),
            "denomination_type": raw_entry.get("DENOMINATION_TYPE"),
            "first_trade_datetime": (
                datetime.fromtimestamp(raw_entry.get("FIRST_TRADE_TS"), tz=timezone.utc)
                if raw_entry.get("FIRST_TRADE_TS")
                else None
            ),
            "last_trade_datetime": (
                datetime.fromtimestamp(raw_entry.get("LAST_TRADE_TS"), tz=timezone.utc)
                if raw_entry.get("LAST_TRADE_TS")
                else None
            ),
            "last_funding_rate_update_datetime": (
                datetime.fromtimestamp(
                    raw_entry.get("LAST_FUNDING_RATE_UPDATE_TS"), tz=timezone.utc
                )
                if raw_entry.get("LAST_FUNDING_RATE_UPDATE_TS")
                else None
            ),
            "first_funding_rate_update_datetime": (
                datetime.fromtimestamp(
                    raw_entry.get("FIRST_FUNDING_RATE_UPDATE_TS"), tz=timezone.utc
                )
                if raw_entry.get("FIRST_FUNDING_RATE_UPDATE_TS")
                else None
            ),
            "last_open_interest_update_datetime": (
                datetime.fromtimestamp(
                    raw_entry.get("LAST_OPEN_INTEREST_UPDATE_TS"), tz=timezone.utc
                )
                if raw_entry.get("LAST_OPEN_INTEREST_UPDATE_TS")
                else None
            ),
            "first_open_interest_update_datetime": (
                datetime.fromtimestamp(
                    raw_entry.get("FIRST_OPEN_INTEREST_UPDATE_TS"), tz=timezone.utc
                )
                if raw_entry.get("FIRST_OPEN_INTEREST_UPDATE_TS")
                else None
            ),
            "instrument_metadata": raw_entry.get("INSTRUMENT_METADATA", {}),
            "collected_at": to_mysql_datetime(datetime.now(timezone.utc)),
            "updated_at": to_mysql_datetime(datetime.now(timezone.utc)),
        }

    def _get_schema(self) -> Dict[str, Any]:
        """
        Return the database schema for instrument metadata.

        Returns:
            Dictionary representing the data schema for Polars DataFrame
        """
        import polars as pl

        if self.instrument_type == "spot":
            return {
                "exchange_internal_name": pl.Utf8,
                "instrument_symbol": pl.Utf8,
                "mapped_instrument_symbol": pl.Utf8,
                "base_asset": pl.Utf8,
                "quote_asset": pl.Utf8,
                "instrument_status": pl.Utf8,
                "first_trade_datetime": pl.Datetime(time_zone="UTC"),
                "last_trade_datetime": pl.Datetime(time_zone="UTC"),
                "instrument_metadata": pl.Utf8,  # JSON string
                "collected_at": pl.Datetime(time_zone="UTC"),
                "updated_at": pl.Datetime(time_zone="UTC"),
            }
        else:
            return {
                "exchange_internal_name": pl.Utf8,
                "instrument_symbol": pl.Utf8,
                "mapped_instrument_symbol": pl.Utf8,
                "base_asset": pl.Utf8,
                "quote_asset": pl.Utf8,
                "instrument_status": pl.Utf8,
                "instrument_type": pl.Utf8,
                "contract_currency": pl.Utf8,
                "settlement_currency": pl.Utf8,
                "index_underlying": pl.Utf8,
                "denomination_type": pl.Utf8,
                "first_trade_datetime": pl.Datetime(time_zone="UTC"),
                "last_trade_datetime": pl.Datetime(time_zone="UTC"),
                "last_funding_rate_update_datetime": pl.Datetime(time_zone="UTC"),
                "first_funding_rate_update_datetime": pl.Datetime(time_zone="UTC"),
                "last_open_interest_update_datetime": pl.Datetime(time_zone="UTC"),
                "first_open_interest_update_datetime": pl.Datetime(time_zone="UTC"),
                "instrument_metadata": pl.Utf8,  # JSON string
                "collected_at": pl.Datetime(time_zone="UTC"),
                "updated_at": pl.Datetime(time_zone="UTC"),
            }

    def _get_db_table_name(self) -> str:
        """
        Return the target database table name for instrument metadata.

        Returns:
            String name of the target database table
        """
        if self.instrument_type == "spot":
            return "market.cc_spot_exchange_instrument_data"
        else:
            return "market.cc_futures_exchange_instrument_data"

    def _get_conflict_columns(self) -> List[str]:
        """
        Get the columns used for conflict resolution during upserts.

        Returns:
            List of column names used for conflict resolution
        """
        return ["exchange_internal_name", "instrument_symbol"]

    async def _get_all_exchanges(self) -> List[str]:
        """
        Get all exchanges from the database for the instrument type.

        Returns:
            List of exchange internal names
        """
        try:
            if self.instrument_type == "spot":
                query = self.db_client._load_sql("get_qualified_exchanges.sql")
            else:
                query = self.db_client._load_sql("get_all_futures_exchanges.sql")

            self.logger.info(
                f"Fetching all {self.instrument_type} exchanges from database..."
            )

            results = await asyncio.to_thread(
                self.db_client._execute_query, query, fetch=True
            )

            if results:
                exchanges = [row[0] for row in results]
                self.logger.info(
                    f"Found {len(exchanges)} {self.instrument_type} exchanges in database."
                )
                return exchanges
            else:
                self.logger.warning(
                    f"No {self.instrument_type} exchanges found in database."
                )
                return []

        except FileNotFoundError as e:
            self.logger.error(f"SQL script not found: {e}")
            return []
        except Exception as e:
            self.logger.error(
                f"Error fetching {self.instrument_type} exchanges from database: {e}"
            )
            return []

    async def ingest_for_exchanges(
        self,
        exchanges: Optional[List[str]] = None,
        instrument_statuses: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method to ingest instrument metadata for specific exchanges.

        Args:
            exchanges: List of exchange names to fetch instruments for
            instrument_statuses: List of instrument statuses to filter by

        Returns:
            Dictionary containing ingestion results and statistics
        """
        kwargs = {}

        if exchanges:
            kwargs["exchanges"] = exchanges
        if instrument_statuses:
            kwargs["instrument_statuses"] = instrument_statuses

        return await self.ingest_metadata(**kwargs)

    async def ingest_all_instruments(
        self,
        instrument_statuses: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest instrument metadata for all exchanges.

        Args:
            instrument_statuses: List of instrument statuses to filter by

        Returns:
            Dictionary containing ingestion results and statistics
        """
        self.logger.info(
            f"Starting full {self.instrument_type} instrument metadata ingestion"
        )

        kwargs = {}
        if instrument_statuses:
            kwargs["instrument_statuses"] = instrument_statuses

        return await self.ingest_metadata(**kwargs)

    async def get_instrument_count_by_exchange(self) -> Dict[str, int]:
        """
        Get the count of instruments by exchange from the database.

        Returns:
            Dictionary mapping exchange names to instrument counts
        """
        try:
            table_name = self._get_db_table_name()
            query = f"""
                SELECT exchange_internal_name, COUNT(*) as instrument_count
                FROM {table_name}
                WHERE instrument_status = 'ACTIVE'
                GROUP BY exchange_internal_name
                ORDER BY instrument_count DESC
            """

            results = await asyncio.to_thread(
                self.db_client._execute_query, query, fetch=True
            )

            if results:
                return {row[0]: row[1] for row in results}
            else:
                return {}

        except Exception as e:
            self.logger.error(f"Error getting instrument count by exchange: {e}")
            return {}

    async def get_inactive_instruments(
        self, days_threshold: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get instruments that have been inactive for more than the specified threshold.

        Args:
            days_threshold: Number of days to consider an instrument inactive

        Returns:
            List of inactive instrument records
        """
        try:
            table_name = self._get_db_table_name()
            query = f"""
                SELECT exchange_internal_name, instrument_symbol, mapped_instrument_symbol,
                       last_trade_datetime, instrument_status
                FROM {table_name}
                WHERE last_trade_datetime < DATE_SUB(NOW(), INTERVAL %s DAY)
                   OR last_trade_datetime IS NULL
                ORDER BY last_trade_datetime ASC
            """

            results = await asyncio.to_thread(
                self.db_client._execute_query,
                query,
                params=(days_threshold,),
                fetch=True,
            )

            if results:
                return [
                    {
                        "exchange": row[0],
                        "instrument": row[1],
                        "mapped_instrument": row[2],
                        "last_trade_datetime": row[3],
                        "status": row[4],
                    }
                    for row in results
                ]
            else:
                return []

        except Exception as e:
            self.logger.error(f"Error getting inactive instruments: {e}")
            return []
