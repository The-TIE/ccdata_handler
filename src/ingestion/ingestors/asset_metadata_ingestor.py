"""
Asset metadata ingestor implementation.

This module provides the AssetMetadataIngestor class for ingesting asset
metadata from the CryptoCompare Asset API, including asset details,
alternative IDs, industries, consensus mechanisms, and market data.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

from ..base import MetadataIngestor
from ...data_api.asset_api_client import CcdataAssetApiClient
from ...db.utils import to_mysql_datetime
from ...rate_limit_tracker import record_rate_limit_status


class AssetMetadataIngestor(MetadataIngestor):
    """
    Ingestor for asset metadata.

    Extends MetadataIngestor to provide specialized functionality for
    ingesting comprehensive asset metadata including basic asset information,
    alternative IDs, industries, consensus mechanisms, and market data.
    """

    def __init__(self, api_client: CcdataAssetApiClient, db_client: Any, config: Any):
        """
        Initialize the asset metadata ingestor.

        Args:
            api_client: CryptoCompare Asset API client instance
            db_client: Database client instance for data persistence
            config: Configuration object with ingestion settings
        """
        super().__init__(api_client, db_client, config)

        # Validate that we have the correct API client type
        if not isinstance(api_client, CcdataAssetApiClient):
            raise TypeError("AssetMetadataIngestor requires CcdataAssetApiClient")

        # Asset-specific configuration
        self.page_size = getattr(config.ingestion, "batch_size", 100)
        self.groups = [
            "ID",
            "BASIC",
            "CLASSIFICATION",
            "DESCRIPTION_SUMMARY",
            "PRICE",
            "MKT_CAP",
            "VOLUME",
        ]

    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch asset metadata from the CryptoCompare Asset API.

        Args:
            **kwargs: API parameters including:
                - page_size: Number of assets per page (default: 100)
                - max_pages: Maximum number of pages to fetch (optional)

        Returns:
            List of raw asset data dictionaries from the API

        Raises:
            Exception: If API call fails
        """
        try:
            page_size = kwargs.get("page_size", self.page_size)
            max_pages = kwargs.get("max_pages")

            self.logger.info(f"Fetching asset metadata with page_size={page_size}")

            page = 1
            all_assets = []
            total_assets = None

            while True:
                self.logger.info(f"Fetching asset top list - Page: {page}")

                response = await asyncio.to_thread(
                    self.api_client.get_top_list_general,
                    page=page,
                    page_size=page_size,
                    groups=self.groups,
                )

                if not response or "Data" not in response:
                    self.logger.warning(f"No data received from API on page {page}")
                    break

                page_assets = response["Data"]["LIST"]
                if not page_assets:
                    self.logger.info(f"No assets received on page {page}, stopping")
                    break

                all_assets.extend(page_assets)

                # Get total count from first page
                if total_assets is None:
                    total_assets = (
                        response["Data"]
                        .get("STATS", {})
                        .get("TOTAL_ASSETS", len(page_assets))
                    )
                    self.logger.info(f"Total assets available: {total_assets}")

                # Check if we should continue
                if max_pages and page >= max_pages:
                    self.logger.info(f"Reached max_pages limit: {max_pages}")
                    break

                if (page * page_size) >= total_assets:
                    self.logger.info("Fetched all available assets")
                    break

                page += 1

                # Add delay between API calls to respect rate limits
                if hasattr(self.config.ingestion, "api_call_delay"):
                    await asyncio.sleep(self.config.ingestion.api_call_delay)

            self.logger.info(
                f"Fetched {len(all_assets)} total assets from {page-1} pages"
            )
            record_rate_limit_status("asset_metadata_api", "success")
            return all_assets

        except Exception as e:
            self.logger.error(f"Error fetching asset metadata: {e}")
            record_rate_limit_status("asset_metadata_api", "failure")
            raise

    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single raw asset entry into multiple database records.

        This method transforms one asset into records for multiple tables:
        - cc_assets (main asset data)
        - cc_asset_alternative_ids
        - cc_asset_industries_map
        - cc_asset_consensus_mechanisms_map
        - cc_asset_consensus_algorithm_types_map
        - cc_asset_hashing_algorithm_types_map
        - cc_asset_previous_symbols_map
        - cc_asset_market_data

        Args:
            raw_entry: Single raw asset data entry from API response

        Returns:
            Transformed data dictionary with records for all related tables
        """
        try:
            current_ts = datetime.now(timezone.utc)
            asset_id = raw_entry.get("ID")

            if not asset_id:
                raise ValueError("Asset missing required ID field")

            # Main asset record
            asset_record = {
                "asset_id": asset_id,
                "symbol": raw_entry.get("SYMBOL"),
                "name": raw_entry.get("NAME"),
                "uri": raw_entry.get("URI"),
                "asset_type": raw_entry.get("ASSET_TYPE"),
                "cc_internal_type": raw_entry.get("TYPE"),
                "id_legacy": raw_entry.get("ID_LEGACY"),
                "id_parent_asset": raw_entry.get("ID_PARENT_ASSET"),
                "id_asset_issuer": raw_entry.get("ID_ASSET_ISSUER"),
                "asset_issuer_name": raw_entry.get("ASSET_ISSUER_NAME"),
                "parent_asset_symbol": raw_entry.get("PARENT_ASSET_SYMBOL"),
                "cc_created_on": to_mysql_datetime(raw_entry.get("CREATED_ON")),
                "cc_updated_on": to_mysql_datetime(raw_entry.get("UPDATED_ON")),
                "public_notice": raw_entry.get("PUBLIC_NOTICE"),
                "logo_url": raw_entry.get("LOGO_URL"),
                "launch_date": to_mysql_datetime(raw_entry.get("LAUNCH_DATE")),
                "description_summary": raw_entry.get("ASSET_DESCRIPTION_SUMMARY"),
                "decimal_points": raw_entry.get("ASSET_DECIMAL_POINTS"),
                "symbol_glyph": raw_entry.get("ASSET_SYMBOL_GLYPH"),
                "created_at": to_mysql_datetime(current_ts),
                "updated_at": to_mysql_datetime(current_ts),
            }

            # Alternative IDs
            alt_ids_record = {
                "asset_id": asset_id,
                "created_at": to_mysql_datetime(current_ts),
                "updated_at": to_mysql_datetime(current_ts),
                "cmc_id": None,
                "cg_id": None,
                "isin_id": None,
                "valor_id": None,
                "dti_id": None,
                "chain_id": None,
            }

            for alt_id in raw_entry.get("ASSET_ALTERNATIVE_IDS", []) or []:
                source_name = alt_id.get("NAME")
                id_value = alt_id.get("ID")
                if source_name and id_value:
                    column_name = f"{source_name.lower()}_id"
                    if column_name in alt_ids_record:
                        alt_ids_record[column_name] = id_value

            # Industries
            industries_records = []
            for industry in raw_entry.get("ASSET_INDUSTRIES", []) or []:
                industries_records.append(
                    {
                        "asset_id": asset_id,
                        "industry_name": industry.get("ASSET_INDUSTRY"),
                        "justification": industry.get("JUSTIFICATION"),
                        "created_at": to_mysql_datetime(current_ts),
                        "updated_at": to_mysql_datetime(current_ts),
                    }
                )

            # Consensus mechanisms
            consensus_mechanisms_records = []
            for mechanism in raw_entry.get("CONSENSUS_MECHANISMS", []) or []:
                consensus_mechanisms_records.append(
                    {
                        "asset_id": asset_id,
                        "mechanism_name": mechanism.get("NAME"),
                        "created_at": to_mysql_datetime(current_ts),
                        "updated_at": to_mysql_datetime(current_ts),
                    }
                )

            # Consensus algorithm types
            consensus_algorithm_types_records = []
            for algo_type in raw_entry.get("CONSENSUS_ALGORITHM_TYPES", []) or []:
                consensus_algorithm_types_records.append(
                    {
                        "asset_id": asset_id,
                        "algorithm_name": algo_type.get("NAME"),
                        "description": algo_type.get("DESCRIPTION"),
                        "created_at": to_mysql_datetime(current_ts),
                        "updated_at": to_mysql_datetime(current_ts),
                    }
                )

            # Hashing algorithm types
            hashing_algorithm_types_records = []
            for hashing_algo in raw_entry.get("HASHING_ALGORITHM_TYPES", []) or []:
                hashing_algorithm_types_records.append(
                    {
                        "asset_id": asset_id,
                        "algorithm_name": hashing_algo.get("NAME"),
                        "created_at": to_mysql_datetime(current_ts),
                        "updated_at": to_mysql_datetime(current_ts),
                    }
                )

            # Previous symbols
            previous_symbols_records = []
            for prev_symbol in raw_entry.get("PREVIOUS_ASSET_SYMBOLS", []) or []:
                if isinstance(prev_symbol, dict):
                    symbol_val = prev_symbol.get("SYMBOL") or json.dumps(
                        prev_symbol, ensure_ascii=False
                    )
                elif isinstance(prev_symbol, list):
                    symbol_val = json.dumps(prev_symbol, ensure_ascii=False)
                else:
                    symbol_val = str(prev_symbol)

                previous_symbols_records.append(
                    {
                        "asset_id": asset_id,
                        "previous_symbol": symbol_val,
                        "created_at": to_mysql_datetime(current_ts),
                        "updated_at": to_mysql_datetime(current_ts),
                    }
                )

            # Market data
            price_usd_last_update_ts = raw_entry.get("PRICE_USD_LAST_UPDATE_TS")
            if price_usd_last_update_ts:
                snapshot_ts = datetime.fromtimestamp(
                    price_usd_last_update_ts, tz=timezone.utc
                )
            else:
                snapshot_ts = None

            market_data_record = {
                "asset_id": asset_id,
                "snapshot_ts": to_mysql_datetime(snapshot_ts),
                "price_usd": raw_entry.get("PRICE_USD"),
                "price_usd_source": raw_entry.get("PRICE_USD_SOURCE"),
                "mkt_cap_penalty": raw_entry.get("MKT_CAP_PENALTY"),
                "circulating_mkt_cap_usd": raw_entry.get("CIRCULATING_MKT_CAP_USD"),
                "total_mkt_cap_usd": raw_entry.get("TOTAL_MKT_CAP_USD"),
                "spot_moving_24_hour_quote_volume_top_tier_usd": raw_entry.get(
                    "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_TOP_TIER_USD"
                ),
                "spot_moving_24_hour_quote_volume_usd": raw_entry.get(
                    "SPOT_MOVING_24_HOUR_QUOTE_VOLUME_USD"
                ),
                "spot_moving_7_day_quote_volume_top_tier_usd": raw_entry.get(
                    "SPOT_MOVING_7_DAY_QUOTE_VOLUME_TOP_TIER_USD"
                ),
                "spot_moving_7_day_quote_volume_usd": raw_entry.get(
                    "SPOT_MOVING_7_DAY_QUOTE_VOLUME_USD"
                ),
                "spot_moving_30_day_quote_volume_top_tier_usd": raw_entry.get(
                    "SPOT_MOVING_30_DAY_QUOTE_VOLUME_TOP_TIER_USD"
                ),
                "spot_moving_30_day_quote_volume_usd": raw_entry.get(
                    "SPOT_MOVING_30_DAY_QUOTE_VOLUME_USD"
                ),
                "created_at": to_mysql_datetime(current_ts),
                "updated_at": to_mysql_datetime(current_ts),
            }

            return {
                "asset": asset_record,
                "alt_ids": alt_ids_record,
                "industries": industries_records,
                "consensus_mechanisms": consensus_mechanisms_records,
                "consensus_algorithm_types": consensus_algorithm_types_records,
                "hashing_algorithm_types": hashing_algorithm_types_records,
                "previous_symbols": previous_symbols_records,
                "market_data": market_data_record,
            }

        except Exception as e:
            self.logger.error(f"Error transforming asset data: {e}")
            raise

    def _get_schema(self) -> Dict[str, Any]:
        """
        Return the database schema for asset metadata.

        Note: This returns the schema for the main assets table.
        Each related table has its own schema handled separately.

        Returns:
            Dictionary representing the data schema for the main assets table
        """
        import polars as pl

        return {
            "asset_id": pl.Int64,
            "symbol": pl.Utf8,
            "name": pl.Utf8,
            "uri": pl.Utf8,
            "asset_type": pl.Utf8,
            "cc_internal_type": pl.Utf8,
            "id_legacy": pl.Int64,
            "id_parent_asset": pl.Int64,
            "id_asset_issuer": pl.Int64,
            "asset_issuer_name": pl.Utf8,
            "parent_asset_symbol": pl.Utf8,
            "cc_created_on": pl.Datetime(time_zone="UTC"),
            "cc_updated_on": pl.Datetime(time_zone="UTC"),
            "public_notice": pl.Utf8,
            "logo_url": pl.Utf8,
            "launch_date": pl.Datetime(time_zone="UTC"),
            "description_summary": pl.Utf8,
            "decimal_points": pl.Int64,
            "symbol_glyph": pl.Utf8,
            "created_at": pl.Datetime(time_zone="UTC"),
            "updated_at": pl.Datetime(time_zone="UTC"),
        }

    def _get_db_table_name(self) -> str:
        """
        Return the target database table name for asset metadata.

        Returns:
            String name of the main assets table
        """
        return "market.cc_assets"

    def _get_conflict_columns(self) -> List[str]:
        """
        Get the columns used for conflict resolution during upserts.

        Returns:
            List of column names used for conflict resolution
        """
        return ["asset_id"]

    async def _insert_records(self, records: List[Dict[str, Any]]) -> bool:
        """
        Insert asset records into multiple related tables.

        This method overrides the base implementation to handle
        the complex multi-table structure of asset metadata.

        Args:
            records: List of transformed asset records

        Returns:
            True if insertion successful, False otherwise
        """
        if not records:
            return True

        try:
            # Separate records by table type
            assets_records = []
            alt_ids_records = []
            industries_records = []
            consensus_mechanisms_records = []
            consensus_algorithm_types_records = []
            hashing_algorithm_types_records = []
            previous_symbols_records = []
            market_data_records = []

            for record in records:
                if "asset" in record:
                    assets_records.append(record["asset"])
                if "alt_ids" in record and record["alt_ids"].get("asset_id"):
                    alt_ids_records.append(record["alt_ids"])
                if "industries" in record:
                    industries_records.extend(record["industries"])
                if "consensus_mechanisms" in record:
                    consensus_mechanisms_records.extend(record["consensus_mechanisms"])
                if "consensus_algorithm_types" in record:
                    consensus_algorithm_types_records.extend(
                        record["consensus_algorithm_types"]
                    )
                if "hashing_algorithm_types" in record:
                    hashing_algorithm_types_records.extend(
                        record["hashing_algorithm_types"]
                    )
                if "previous_symbols" in record:
                    previous_symbols_records.extend(record["previous_symbols"])
                if "market_data" in record:
                    market_data_records.append(record["market_data"])

            # Insert into each table
            tables_data = [
                (assets_records, "market.cc_assets", True),
                (alt_ids_records, "market.cc_asset_alternative_ids", True),
                (industries_records, "market.cc_asset_industries_map", True),
                (
                    consensus_mechanisms_records,
                    "market.cc_asset_consensus_mechanisms_map",
                    True,
                ),
                (
                    consensus_algorithm_types_records,
                    "market.cc_asset_consensus_algorithm_types_map",
                    True,
                ),
                (
                    hashing_algorithm_types_records,
                    "market.cc_asset_hashing_algorithm_types_map",
                    True,
                ),
                (
                    previous_symbols_records,
                    "market.cc_asset_previous_symbols_map",
                    True,
                ),
                (
                    market_data_records,
                    "market.cc_asset_market_data",
                    False,
                ),  # Append-only
            ]

            total_inserted = 0
            for table_records, table_name, replace in tables_data:
                if table_records:
                    self.db_client.insert_dataframe(
                        table_records, table_name, replace=replace
                    )
                    total_inserted += len(table_records)
                    self.logger.info(
                        f"Inserted {len(table_records)} records into {table_name}"
                    )

            self.logger.info(
                f"Successfully inserted {total_inserted} total records across all asset tables"
            )
            record_rate_limit_status("db_insert", "success")
            return True

        except Exception as e:
            self.logger.error(f"Error inserting asset records into database: {e}")
            record_rate_limit_status("db_insert", "failure")
            return False

    async def ingest_assets(
        self, page_size: Optional[int] = None, max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to ingest asset metadata.

        Args:
            page_size: Number of assets per page
            max_pages: Maximum number of pages to fetch

        Returns:
            Dictionary containing ingestion results and statistics
        """
        kwargs = {}
        if page_size:
            kwargs["page_size"] = page_size
        if max_pages:
            kwargs["max_pages"] = max_pages

        return await self.ingest_metadata(**kwargs)
