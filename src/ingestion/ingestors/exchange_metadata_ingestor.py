"""
Exchange metadata ingestor implementation.

This module provides the ExchangeMetadataIngestor class for ingesting exchange
metadata from the CryptoCompare API, including exchange general information,
supported assets, and trading pairs.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

from ..base import MetadataIngestor
from ...data_api.utilities_api_client import CcdataUtilitiesApiClient
from ...db.utils import to_mysql_datetime
from ...rate_limit_tracker import record_rate_limit_status


class ExchangeMetadataIngestor(MetadataIngestor):
    """
    Ingestor for exchange metadata.

    Extends MetadataIngestor to provide specialized functionality for
    ingesting exchange metadata including general exchange information,
    supported assets, and trading pairs.
    """

    def __init__(
        self, api_client: CcdataUtilitiesApiClient, db_client: Any, config: Any
    ):
        """
        Initialize the exchange metadata ingestor.

        Args:
            api_client: CryptoCompare Utilities API client instance
            db_client: Database client instance for data persistence
            config: Configuration object with ingestion settings
        """
        super().__init__(api_client, db_client, config)

        # Validate that we have the correct API client type
        if not isinstance(api_client, CcdataUtilitiesApiClient):
            raise TypeError(
                "ExchangeMetadataIngestor requires CcdataUtilitiesApiClient"
            )

    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch exchange metadata from the CryptoCompare Utilities API.

        Args:
            **kwargs: API parameters (currently unused for exchanges general)

        Returns:
            List of raw exchange data dictionaries from the API

        Raises:
            Exception: If API call fails
        """
        try:
            self.logger.info("Fetching exchange general data from API")

            response = await asyncio.to_thread(self.api_client.get_exchanges_general)

            if not response or "Data" not in response:
                self.logger.warning("No data received from exchanges general API")
                record_rate_limit_status("exchange_metadata_api", "no_data")
                return []

            exchanges_data = response["Data"]
            if not exchanges_data:
                self.logger.info("Empty exchanges data set received")
                return []

            self.logger.info(f"Received {len(exchanges_data)} exchanges from API")
            record_rate_limit_status("exchange_metadata_api", "success")
            return list(exchanges_data.values())  # Convert dict values to list

        except Exception as e:
            self.logger.error(f"Error fetching exchange metadata: {e}")
            record_rate_limit_status("exchange_metadata_api", "failure")
            raise

    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single raw exchange entry into standardized database format.

        Args:
            raw_entry: Single raw exchange data entry from API response

        Returns:
            Transformed data dictionary ready for database insertion
        """
        try:
            current_ts = datetime.now(timezone.utc)

            # Extract exchange information
            exchange_name = raw_entry.get("Name", "")
            if not exchange_name:
                raise ValueError("Exchange missing required Name field")

            # Transform the data to match database schema
            transformed = {
                "exchange_name": exchange_name,
                "display_name": raw_entry.get("DisplayName", ""),
                "logo_url": raw_entry.get("LogoUrl", ""),
                "affiliate_url": raw_entry.get("AffiliateURL", ""),
                "url": raw_entry.get("Url", ""),
                "country": raw_entry.get("Country", ""),
                "order_book": raw_entry.get("OrderBook", False),
                "trades": raw_entry.get("Trades", False),
                "is_active": raw_entry.get("IsActive", True),
                "total_volume_24h": self._safe_float(raw_entry.get("TotalVolume24H")),
                "total_volume_24h_to": self._safe_float(
                    raw_entry.get("TotalVolume24HTo")
                ),
                "total_top_tier_volume_24h": self._safe_float(
                    raw_entry.get("TotalTopTierVolume24H")
                ),
                "total_top_tier_volume_24h_to": self._safe_float(
                    raw_entry.get("TotalTopTierVolume24HTo")
                ),
                "internal_name": raw_entry.get("InternalName", ""),
                "centralization_type": raw_entry.get("CentralizationType", ""),
                "grade": raw_entry.get("Grade", ""),
                "grade_points": self._safe_int(raw_entry.get("GradePoints")),
                "grade_points_breakdown": self._format_grade_breakdown(
                    raw_entry.get("GradePointsBreakdown")
                ),
                "sponsored": raw_entry.get("Sponsored", False),
                "recommended": raw_entry.get("Recommended", False),
                "created_at": to_mysql_datetime(current_ts),
                "updated_at": to_mysql_datetime(current_ts),
            }

            return transformed

        except Exception as e:
            self.logger.error(f"Error transforming exchange data: {e}")
            raise

    def _safe_float(self, value: Any) -> Optional[float]:
        """
        Safely convert a value to float, returning None if conversion fails.

        Args:
            value: Value to convert

        Returns:
            Float value or None
        """
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """
        Safely convert a value to int, returning None if conversion fails.

        Args:
            value: Value to convert

        Returns:
            Integer value or None
        """
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _format_grade_breakdown(self, breakdown: Any) -> Optional[str]:
        """
        Format grade points breakdown for database storage.

        Args:
            breakdown: Grade breakdown data

        Returns:
            JSON string representation or None
        """
        if not breakdown:
            return None

        try:
            import json

            return json.dumps(breakdown, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(breakdown) if breakdown else None

    def _get_schema(self) -> Dict[str, Any]:
        """
        Return the database schema for exchange metadata.

        Returns:
            Dictionary representing the data schema for Polars DataFrame
        """
        import polars as pl

        return {
            "exchange_name": pl.Utf8,
            "display_name": pl.Utf8,
            "logo_url": pl.Utf8,
            "affiliate_url": pl.Utf8,
            "url": pl.Utf8,
            "country": pl.Utf8,
            "order_book": pl.Boolean,
            "trades": pl.Boolean,
            "is_active": pl.Boolean,
            "total_volume_24h": pl.Float64,
            "total_volume_24h_to": pl.Float64,
            "total_top_tier_volume_24h": pl.Float64,
            "total_top_tier_volume_24h_to": pl.Float64,
            "internal_name": pl.Utf8,
            "centralization_type": pl.Utf8,
            "grade": pl.Utf8,
            "grade_points": pl.Int64,
            "grade_points_breakdown": pl.Utf8,
            "sponsored": pl.Boolean,
            "recommended": pl.Boolean,
            "created_at": pl.Datetime(time_zone="UTC"),
            "updated_at": pl.Datetime(time_zone="UTC"),
        }

    def _get_db_table_name(self) -> str:
        """
        Return the target database table name for exchange metadata.

        Returns:
            String name of the target database table
        """
        return "market.cc_exchanges_general"

    def _get_conflict_columns(self) -> List[str]:
        """
        Get the columns used for conflict resolution during upserts.

        Returns:
            List of column names used for conflict resolution
        """
        return ["exchange_name"]

    async def ingest_exchanges(self) -> Dict[str, Any]:
        """
        Convenience method to ingest exchange metadata.

        Returns:
            Dictionary containing ingestion results and statistics
        """
        return await self.ingest_metadata()

    async def get_active_exchanges(self) -> List[str]:
        """
        Get list of active exchange names from the database.

        Returns:
            List of active exchange names
        """
        try:
            query = """
                SELECT exchange_name 
                FROM market.cc_exchanges_general 
                WHERE is_active = 1
                ORDER BY exchange_name
            """

            result = self.db_client._execute_query(query, fetch=True)
            if result:
                return [row[0] for row in result]
            return []

        except Exception as e:
            self.logger.error(f"Error getting active exchanges: {e}")
            return []

    async def get_exchange_info(self, exchange_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific exchange.

        Args:
            exchange_name: Name of the exchange

        Returns:
            Dictionary with exchange information or None if not found
        """
        try:
            query = """
                SELECT * 
                FROM market.cc_exchanges_general 
                WHERE exchange_name = %s
            """

            result = self.db_client._execute_query(
                query, params=(exchange_name,), fetch=True
            )

            if result and result[0]:
                # Convert result tuple to dictionary
                columns = [
                    "exchange_name",
                    "display_name",
                    "logo_url",
                    "affiliate_url",
                    "url",
                    "country",
                    "order_book",
                    "trades",
                    "is_active",
                    "total_volume_24h",
                    "total_volume_24h_to",
                    "total_top_tier_volume_24h",
                    "total_top_tier_volume_24h_to",
                    "internal_name",
                    "centralization_type",
                    "grade",
                    "grade_points",
                    "grade_points_breakdown",
                    "sponsored",
                    "recommended",
                    "created_at",
                    "updated_at",
                ]
                return dict(zip(columns, result[0]))

            return None

        except Exception as e:
            self.logger.error(f"Error getting exchange info for {exchange_name}: {e}")
            return None

    async def get_exchanges_by_country(self, country: str) -> List[Dict[str, Any]]:
        """
        Get exchanges filtered by country.

        Args:
            country: Country name to filter by

        Returns:
            List of exchange dictionaries
        """
        try:
            query = """
                SELECT exchange_name, display_name, is_active, total_volume_24h
                FROM market.cc_exchanges_general 
                WHERE country = %s
                ORDER BY total_volume_24h DESC
            """

            result = self.db_client._execute_query(query, params=(country,), fetch=True)

            if result:
                return [
                    {
                        "exchange_name": row[0],
                        "display_name": row[1],
                        "is_active": row[2],
                        "total_volume_24h": row[3],
                    }
                    for row in result
                ]

            return []

        except Exception as e:
            self.logger.error(f"Error getting exchanges by country {country}: {e}")
            return []

    async def get_top_exchanges_by_volume(
        self, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top exchanges by 24h volume.

        Args:
            limit: Maximum number of exchanges to return

        Returns:
            List of exchange dictionaries ordered by volume
        """
        try:
            query = """
                SELECT exchange_name, display_name, total_volume_24h, 
                       total_top_tier_volume_24h, country, grade
                FROM market.cc_exchanges_general 
                WHERE is_active = 1 AND total_volume_24h IS NOT NULL
                ORDER BY total_volume_24h DESC
                LIMIT %s
            """

            result = self.db_client._execute_query(query, params=(limit,), fetch=True)

            if result:
                return [
                    {
                        "exchange_name": row[0],
                        "display_name": row[1],
                        "total_volume_24h": row[2],
                        "total_top_tier_volume_24h": row[3],
                        "country": row[4],
                        "grade": row[5],
                    }
                    for row in result
                ]

            return []

        except Exception as e:
            self.logger.error(f"Error getting top exchanges by volume: {e}")
            return []
