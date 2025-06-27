"""
Base ingestion framework providing abstract classes and common functionality
for all data ingestors in the unified data ingestion pipeline.

This module implements the core abstractions defined in the architecture design,
providing a consistent interface and shared orchestration logic for different
types of data ingestion (time series, metadata, etc.).
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Union
import logging

from ..logger_config import setup_logger
from ..rate_limit_tracker import record_rate_limit_status


logger = setup_logger(__name__)


class BaseIngestor(ABC):
    """
    Abstract base class for all data ingestors.

    Defines the common interface and core orchestration logic that all
    concrete ingestors must implement. Provides shared functionality for
    configuration loading, resource management, and error handling.

    Attributes:
        api_client: The API client instance for fetching data
        db_client: The database client instance for data persistence
        config: Configuration object containing ingestion settings
        logger: Logger instance for this ingestor
    """

    def __init__(self, api_client: Any, db_client: Any, config: Any):
        """
        Initialize the base ingestor with required dependencies.

        Args:
            api_client: API client instance for data fetching
            db_client: Database client instance for data persistence
            config: Configuration object with ingestion settings
        """
        self.api_client = api_client
        self.db_client = db_client
        self.config = config
        self.logger = logger

        # Initialize common settings
        self._batch_size = getattr(config, "BATCH_SIZE", None) or 1000
        self._max_retries = getattr(config, "MAX_RETRIES", None) or 3
        self._retry_delay = getattr(config, "RETRY_DELAY", None) or 1.0

    @abstractmethod
    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Abstract method to fetch raw data from the API.

        Concrete ingestors must implement this method to define how they
        fetch data from their specific API endpoints.

        Args:
            **kwargs: API-specific parameters for data fetching

        Returns:
            List of raw data dictionaries from the API

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method to transform a single raw API entry.

        Concrete ingestors must implement this method to define how they
        transform raw API responses into standardized database records.

        Args:
            raw_entry: Single raw data entry from API response

        Returns:
            Transformed data dictionary ready for database insertion

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def _get_schema(self) -> Dict[str, Any]:
        """
        Abstract method to return the data schema.

        Concrete ingestors must implement this method to define the
        expected schema for their data type.

        Returns:
            Dictionary representing the data schema

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    @abstractmethod
    def _get_db_table_name(self) -> str:
        """
        Abstract method to return the target database table name.

        Concrete ingestors must implement this method to specify
        which database table their data should be inserted into.

        Returns:
            String name of the target database table

        Raises:
            NotImplementedError: If not implemented by concrete class
        """
        pass

    def _get_conflict_columns(self) -> List[str]:
        """
        Get the columns used for conflict resolution during upserts.

        Default implementation returns common conflict columns.
        Concrete ingestors can override this method to specify
        their own conflict resolution columns.

        Returns:
            List of column names used for conflict resolution
        """
        return ["datetime", "market", "instrument"]

    async def _get_last_ingested_timestamp(self, **filters) -> Optional[datetime]:
        """
        Get the timestamp of the last ingested record.

        This method queries the database to find the most recent
        timestamp for the given filters, enabling incremental ingestion.

        Args:
            **filters: Filter criteria for finding the last timestamp

        Returns:
            DateTime of last ingested record, or None if no records exist
        """
        try:
            table_name = self._get_db_table_name()

            # Build WHERE clause from filters
            where_conditions = []
            params = []
            for key, value in filters.items():
                where_conditions.append(f"{key} = %s")
                params.append(value)

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = f"""
                SELECT MAX(datetime)
                FROM {table_name}
                WHERE {where_clause}
            """

            # Use synchronous database call for now (compatible with existing code)
            if hasattr(self.db_client, "_execute_query"):
                result = self.db_client._execute_query(
                    query, params=tuple(params), fetch=True
                )
                if result and result[0] and result[0][0]:
                    timestamp = result[0][0]
                    # Handle both datetime objects and tuples from mocks
                    if isinstance(timestamp, tuple):
                        timestamp = timestamp[0]
                    if hasattr(timestamp, "replace"):
                        return timestamp.replace(tzinfo=timezone.utc)
                    return timestamp

            return None

        except Exception as e:
            self.logger.error(f"Error getting last ingested timestamp: {e}")
            return None

    async def _validate_and_filter_records(
        self, records: List[Dict[str, Any]], last_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Validate and filter records before database insertion.

        This method performs data validation and filters out records
        that have already been ingested based on timestamps.

        Args:
            records: List of transformed records to validate
            last_timestamp: Timestamp of last ingested record for filtering

        Returns:
            List of validated and filtered records
        """
        if not records:
            return []

        valid_records = []

        for record in records:
            try:
                # Call subclass-specific validation
                if not self._validate_record(record):
                    continue

                # Filter out records older than last ingested timestamp (only for time-series data)
                if (
                    last_timestamp
                    and "datetime" in record
                    and record["datetime"] <= last_timestamp
                ):
                    continue

                # Ensure datetime is timezone-aware (only if datetime field exists)
                if (
                    "datetime" in record
                    and isinstance(record["datetime"], datetime)
                    and record["datetime"].tzinfo is None
                ):
                    record["datetime"] = record["datetime"].replace(tzinfo=timezone.utc)

                # Additional validation for datetime field
                if "datetime" in record and not isinstance(
                    record["datetime"], datetime
                ):
                    # Try to skip records with invalid datetime objects
                    continue

                valid_records.append(record)

            except Exception as e:
                self.logger.warning(f"Error validating record: {e}, skipping record")
                continue

        return valid_records

    def _validate_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate a single record. Can be overridden by subclasses.

        Args:
            record: Record to validate

        Returns:
            True if record is valid, False otherwise
        """
        # Default validation - check that record is not empty and has datetime field
        if not record:
            return False

        # For time-series data, datetime field is required
        if "datetime" not in record:
            return False

        return True

    async def _insert_records(self, records: List[Dict[str, Any]]) -> bool:
        """
        Insert records into the database with error handling.

        This method handles the database insertion with proper error
        handling and retry logic.

        Args:
            records: List of validated records to insert

        Returns:
            True if insertion successful, False otherwise
        """
        if not records:
            return True

        try:
            table_name = self._get_db_table_name()
            schema = self._get_schema()

            # Use existing database client method for compatibility
            if hasattr(self.db_client, "insert_dataframe"):
                self.db_client.insert_dataframe(
                    records, table_name, replace=True, schema=schema
                )
                self.logger.info(
                    f"Successfully inserted {len(records)} records into {table_name}"
                )
                record_rate_limit_status("db_insert", "success")
                return True
            else:
                self.logger.error(
                    "Database client does not support insert_dataframe method"
                )
                record_rate_limit_status("db_insert", "failure")
                return False

        except Exception as e:
            self.logger.error(f"Error inserting records into database: {e}")
            record_rate_limit_status("db_insert", "failure")
            return False

    async def ingest(self, **kwargs) -> Dict[str, Any]:
        """
        Main ingestion orchestration method.

        This method contains the shared logic for the complete ingestion
        process: fetching data, transforming it, validating it, and
        inserting it into the database.

        Args:
            **kwargs: Ingestion parameters specific to the concrete ingestor

        Returns:
            Dictionary containing ingestion results and statistics
        """
        start_time = datetime.now(timezone.utc)
        total_records_processed = 0
        total_records_inserted = 0

        try:
            self.logger.info(f"Starting ingestion for {self._get_db_table_name()}")

            # Get last ingested timestamp for incremental loading
            last_timestamp = await self._get_last_ingested_timestamp(**kwargs)
            if last_timestamp:
                self.logger.info(f"Last ingested timestamp: {last_timestamp}")
            else:
                self.logger.info("No previous data found, starting fresh ingestion")

            # Fetch raw data from API
            self.logger.info("Fetching data from API...")
            raw_data = await self._fetch_data_from_api(**kwargs)

            if not raw_data:
                self.logger.info("No new data received from API")
                return {
                    "status": "success",
                    "records_processed": 0,
                    "records_inserted": 0,
                    "duration_seconds": (
                        datetime.now(timezone.utc) - start_time
                    ).total_seconds(),
                }

            self.logger.info(f"Received {len(raw_data)} raw records from API")

            # Transform raw data to standardized format
            self.logger.info("Transforming raw data...")
            transformed_records = []

            for raw_entry in raw_data:
                try:
                    transformed_record = self._transform_data(raw_entry)
                    transformed_records.append(transformed_record)
                    total_records_processed += 1
                except Exception as e:
                    self.logger.warning(f"Error transforming record: {e}, skipping")
                    continue

            # Validate and filter records
            valid_records = await self._validate_and_filter_records(
                transformed_records, last_timestamp
            )

            if not valid_records:
                self.logger.info("No new valid records to insert after filtering")
                return {
                    "status": "success",
                    "records_processed": total_records_processed,
                    "records_inserted": 0,
                    "duration_seconds": (
                        datetime.now(timezone.utc) - start_time
                    ).total_seconds(),
                }

            # Insert records into database
            self.logger.info(f"Inserting {len(valid_records)} valid records...")
            insertion_success = await self._insert_records(valid_records)

            if insertion_success:
                total_records_inserted = len(valid_records)
                self.logger.info(f"Ingestion completed successfully")
            else:
                self.logger.error("Database insertion failed")

            return {
                "status": "success" if insertion_success else "partial_failure",
                "records_processed": total_records_processed,
                "records_inserted": total_records_inserted,
                "duration_seconds": (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds(),
            }

        except Exception as e:
            self.logger.error(f"Error during ingestion: {e}", exc_info=True)
            return {
                "status": "failure",
                "error": str(e),
                "records_processed": total_records_processed,
                "records_inserted": total_records_inserted,
                "duration_seconds": (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds(),
            }


class TimeSeriesIngestor(BaseIngestor):
    """
    Specialized ingestor for time-series data.

    Extends BaseIngestor with time-series specific functionality including
    interval-based processing, backfilling logic, and time-based pagination.

    Attributes:
        interval: Time interval for the data (e.g., '1d', '1h', '1m')
        backfill_enabled: Whether to perform historical data backfilling
        max_backfill_days: Maximum number of days to backfill
    """

    def __init__(self, api_client: Any, db_client: Any, config: Any, interval: str):
        """
        Initialize the time series ingestor.

        Args:
            api_client: API client instance for data fetching
            db_client: Database client instance for data persistence
            config: Configuration object with ingestion settings
            interval: Time interval for the data (e.g., '1d', '1h', '1m')
        """
        super().__init__(api_client, db_client, config)
        self.interval = interval
        self.backfill_enabled = getattr(config, "BACKFILL_ENABLED", True)
        self.max_backfill_days = getattr(config, "MAX_BACKFILL_DAYS", 365)

        # Validate interval
        if interval not in ["1d", "1h", "1m"]:
            raise ValueError(f"Unsupported interval: {interval}")

    def _get_interval_timedelta(self) -> timedelta:
        """
        Get timedelta object for the configured interval.

        Returns:
            timedelta object representing the interval
        """
        if self.interval == "1d":
            return timedelta(days=1)
        elif self.interval == "1h":
            return timedelta(hours=1)
        elif self.interval == "1m":
            return timedelta(minutes=1)
        else:
            raise ValueError(f"Unsupported interval: {self.interval}")

    def _calculate_backfill_start_date(
        self, last_timestamp: Optional[datetime]
    ) -> datetime:
        """
        Calculate the start date for backfilling historical data.

        Args:
            last_timestamp: Timestamp of last ingested record

        Returns:
            DateTime to start backfilling from
        """
        if last_timestamp:
            # Continue from where we left off
            return last_timestamp + self._get_interval_timedelta()

        if self.backfill_enabled:
            # Start backfilling from configured days ago
            backfill_start = datetime.now(timezone.utc) - timedelta(
                days=self.max_backfill_days
            )
            return backfill_start.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Start from current time if backfill disabled
            return datetime.now(timezone.utc)

    async def ingest_with_backfill(self, **kwargs) -> Dict[str, Any]:
        """
        Perform ingestion with automatic backfilling of historical data.

        This method extends the base ingestion logic with time-series
        specific backfilling capabilities.

        Args:
            **kwargs: Ingestion parameters specific to the concrete ingestor

        Returns:
            Dictionary containing ingestion results and statistics
        """
        self.logger.info(
            f"Starting time-series ingestion with backfill for interval {self.interval}"
        )

        # Get last ingested timestamp
        last_timestamp = await self._get_last_ingested_timestamp(**kwargs)

        # Calculate backfill start date
        start_date = self._calculate_backfill_start_date(last_timestamp)

        # Add start date to kwargs for API fetching
        kwargs["start_date"] = start_date
        kwargs["interval"] = self.interval

        # Perform standard ingestion
        return await self.ingest(**kwargs)


class MetadataIngestor(BaseIngestor):
    """
    Specialized ingestor for one-time metadata ingestion.

    Extends BaseIngestor with metadata-specific functionality including
    change detection, full refresh capabilities, and metadata validation.

    Attributes:
        full_refresh: Whether to perform full refresh of metadata
        change_detection_enabled: Whether to detect changes in metadata
    """

    def __init__(self, api_client: Any, db_client: Any, config: Any):
        """
        Initialize the metadata ingestor.

        Args:
            api_client: API client instance for data fetching
            db_client: Database client instance for data persistence
            config: Configuration object with ingestion settings
        """
        super().__init__(api_client, db_client, config)
        self.full_refresh = getattr(config, "METADATA_FULL_REFRESH", False)
        self.change_detection_enabled = getattr(
            config, "METADATA_CHANGE_DETECTION", True
        )

    def _get_conflict_columns(self) -> List[str]:
        """
        Get conflict columns specific to metadata ingestion.

        Metadata typically uses different conflict resolution columns
        than time-series data.

        Returns:
            List of column names used for metadata conflict resolution
        """
        return ["id", "symbol", "name"]  # Common metadata identifiers

    def _validate_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate a metadata record.

        Metadata records don't require datetime fields, unlike time-series data.

        Args:
            record: Record to validate

        Returns:
            True if record is valid, False otherwise
        """
        # For metadata, we just need the record to be non-empty
        # No datetime field requirement
        return bool(record)

    async def _detect_changes(
        self, new_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect changes in metadata records.

        This method compares new records with existing ones to identify
        changes that need to be updated in the database.

        Args:
            new_records: List of new metadata records

        Returns:
            List of records that have changes
        """
        if not self.change_detection_enabled or self.full_refresh:
            return new_records

        # For now, return all records (change detection can be enhanced later)
        # In a full implementation, this would query existing records and compare
        return new_records

    async def ingest_metadata(self, **kwargs) -> Dict[str, Any]:
        """
        Perform metadata ingestion with change detection.

        This method extends the base ingestion logic with metadata-specific
        functionality like change detection and full refresh capabilities.

        Args:
            **kwargs: Ingestion parameters specific to the concrete ingestor

        Returns:
            Dictionary containing ingestion results and statistics
        """
        self.logger.info(
            f"Starting metadata ingestion (full_refresh={self.full_refresh})"
        )

        if self.full_refresh:
            # For full refresh, we don't need to check last timestamp
            kwargs["ignore_last_timestamp"] = True

        # Perform standard ingestion
        result = await self.ingest(**kwargs)

        # Add metadata-specific information to result
        result["full_refresh"] = self.full_refresh
        result["change_detection_enabled"] = self.change_detection_enabled

        return result
