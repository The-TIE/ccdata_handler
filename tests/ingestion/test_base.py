"""
Unit tests for the base ingestion framework classes.

This module tests the core functionality of BaseIngestor, TimeSeriesIngestor,
and MetadataIngestor classes, including initialization, data processing,
error handling, and database operations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import asyncio

from src.ingestion.base import BaseIngestor, TimeSeriesIngestor, MetadataIngestor


class ConcreteIngestor(BaseIngestor):
    """Concrete implementation of BaseIngestor for testing."""

    def __init__(self, api_client, db_client, config, table_name="test_table"):
        super().__init__(api_client, db_client, config)
        self._table_name = table_name
        self._schema = {"datetime": "DATETIME", "value": "FLOAT"}

    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """Mock implementation for testing."""
        result = self.api_client.get_data(**kwargs)
        # Handle both sync and async mock returns
        if hasattr(result, "__await__"):
            return await result
        return result

    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Mock transformation for testing."""
        return {
            "datetime": datetime.fromisoformat(
                raw_entry["datetime"].replace("Z", "+00:00")
            ),
            "value": float(raw_entry["value"]),
            "market": raw_entry.get("market", "TEST"),
            "instrument": raw_entry.get("instrument", "TEST-PAIR"),
        }

    def _get_schema(self) -> Dict[str, Any]:
        return self._schema

    def _get_db_table_name(self) -> str:
        return self._table_name


class TestBaseIngestor:
    """Test cases for BaseIngestor class."""

    def test_initialization(self, mock_api_client, mock_db_client, mock_config_manager):
        """Test BaseIngestor initialization."""
        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        assert ingestor.api_client == mock_api_client
        assert ingestor.db_client == mock_db_client
        assert ingestor.config == mock_config_manager
        assert ingestor._batch_size == mock_config_manager.BATCH_SIZE
        assert ingestor._max_retries == mock_config_manager.MAX_RETRIES
        assert ingestor._retry_delay == mock_config_manager.RETRY_DELAY

    def test_initialization_with_defaults(self, mock_api_client, mock_db_client):
        """Test BaseIngestor initialization with default config values."""
        config = Mock()
        # Ensure getattr returns None for missing attributes so defaults are used
        config.BATCH_SIZE = None
        config.MAX_RETRIES = None
        config.RETRY_DELAY = None

        ingestor = ConcreteIngestor(mock_api_client, mock_db_client, config)

        assert ingestor._batch_size == 1000  # default
        assert ingestor._max_retries == 3  # default
        assert ingestor._retry_delay == 1.0  # default

    def test_get_conflict_columns_default(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test default conflict columns."""
        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        columns = ingestor._get_conflict_columns()
        assert columns == ["datetime", "market", "instrument"]

    @pytest.mark.asyncio
    async def test_get_last_ingested_timestamp_success(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test successful retrieval of last ingested timestamp."""
        # Setup mock database response
        test_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        mock_db_client._execute_query.return_value = [[(test_timestamp,)]]

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor._get_last_ingested_timestamp(market="BINANCE")

        assert result == test_timestamp.replace(tzinfo=timezone.utc)
        mock_db_client._execute_query.assert_called_once()

        # Check the query was constructed correctly
        call_args = mock_db_client._execute_query.call_args
        query = call_args[0][0]
        params = call_args[1]["params"]

        assert "SELECT MAX(datetime)" in query
        assert "FROM test_table" in query
        assert "WHERE market = %s" in query
        assert params == ("BINANCE",)

    @pytest.mark.asyncio
    async def test_get_last_ingested_timestamp_no_data(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test retrieval when no data exists."""
        mock_db_client._execute_query.return_value = []

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor._get_last_ingested_timestamp()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_last_ingested_timestamp_error(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test error handling in timestamp retrieval."""
        mock_db_client._execute_query.side_effect = Exception("Database error")

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor._get_last_ingested_timestamp()

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_and_filter_records_valid_data(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test validation and filtering with valid data."""
        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        records = [
            {
                "datetime": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "value": 100.0,
                "market": "BINANCE",
            },
            {
                "datetime": datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
                "value": 200.0,
                "market": "BINANCE",
            },
        ]

        result = await ingestor._validate_and_filter_records(records)

        assert len(result) == 2
        assert all("datetime" in record for record in result)

    @pytest.mark.asyncio
    async def test_validate_and_filter_records_with_timestamp_filter(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test filtering based on last timestamp."""
        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        last_timestamp = datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
        records = [
            {
                "datetime": datetime(
                    2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
                ),  # Before last
                "value": 100.0,
            },
            {
                "datetime": datetime(
                    2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc
                ),  # After last
                "value": 200.0,
            },
        ]

        result = await ingestor._validate_and_filter_records(records, last_timestamp)

        assert len(result) == 1
        assert result[0]["datetime"] == datetime(
            2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc
        )

    @pytest.mark.asyncio
    async def test_validate_and_filter_records_missing_datetime(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test validation with missing datetime field."""
        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        records = [
            {"value": 100.0, "market": "BINANCE"},  # Missing datetime
            {
                "datetime": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "value": 200.0,
            },
        ]

        result = await ingestor._validate_and_filter_records(records)

        assert len(result) == 1
        assert result[0]["value"] == 200.0

    @pytest.mark.asyncio
    async def test_validate_and_filter_records_naive_datetime(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test handling of naive datetime objects."""
        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        records = [
            {
                "datetime": datetime(2024, 1, 1, 12, 0, 0),  # Naive datetime
                "value": 100.0,
            }
        ]

        result = await ingestor._validate_and_filter_records(records)

        assert len(result) == 1
        assert result[0]["datetime"].tzinfo == timezone.utc

    @pytest.mark.asyncio
    async def test_insert_records_success(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test successful record insertion."""
        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        records = [
            {
                "datetime": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "value": 100.0,
            }
        ]

        result = await ingestor._insert_records(records)

        assert result is True
        mock_db_client.insert_dataframe.assert_called_once_with(
            records, "test_table", replace=True, schema=ingestor._get_schema()
        )

    @pytest.mark.asyncio
    async def test_insert_records_empty_list(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test insertion with empty record list."""
        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor._insert_records([])

        assert result is True
        mock_db_client.insert_dataframe.assert_not_called()

    @pytest.mark.asyncio
    async def test_insert_records_db_error(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test handling of database insertion errors."""
        mock_db_client.insert_dataframe.side_effect = Exception("Database error")

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        records = [{"datetime": datetime.now(timezone.utc), "value": 100.0}]
        result = await ingestor._insert_records(records)

        assert result is False

    @pytest.mark.asyncio
    async def test_insert_records_no_insert_method(
        self, mock_api_client, mock_config_manager
    ):
        """Test handling when database client lacks insert_dataframe method."""
        db_client = Mock()
        # Remove insert_dataframe method
        del db_client.insert_dataframe

        ingestor = ConcreteIngestor(mock_api_client, db_client, mock_config_manager)

        records = [{"datetime": datetime.now(timezone.utc), "value": 100.0}]
        result = await ingestor._insert_records(records)

        assert result is False

    @pytest.mark.asyncio
    async def test_ingest_full_workflow_success(
        self, mock_api_client, mock_db_client, mock_config_manager, sample_raw_api_data
    ):
        """Test complete ingestion workflow with successful execution."""
        # Setup API client to return test data
        mock_api_client.get_data = AsyncMock(return_value=sample_raw_api_data)

        # Setup database client
        mock_db_client._execute_query.return_value = []  # No previous data

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor.ingest(market="BINANCE")

        assert result["status"] == "success"
        assert result["records_processed"] == len(sample_raw_api_data)
        assert result["records_inserted"] == len(sample_raw_api_data)
        assert "duration_seconds" in result

        # Verify API was called
        mock_api_client.get_data.assert_called_once_with(market="BINANCE")

        # Verify database insertion was called
        mock_db_client.insert_dataframe.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_no_api_data(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test ingestion when API returns no data."""
        mock_api_client.get_data = AsyncMock(return_value=[])

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor.ingest()

        assert result["status"] == "success"
        assert result["records_processed"] == 0
        assert result["records_inserted"] == 0

    @pytest.mark.asyncio
    async def test_ingest_api_error(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test ingestion with API error."""
        mock_api_client.get_data = AsyncMock(side_effect=Exception("API error"))

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor.ingest()

        assert result["status"] == "failure"
        assert "error" in result
        assert result["records_processed"] == 0
        assert result["records_inserted"] == 0

    @pytest.mark.asyncio
    async def test_ingest_transformation_errors(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test ingestion with transformation errors."""
        # API data with invalid entries
        invalid_data = [
            {"datetime": "2024-01-01T00:00:00Z", "value": "100.0"},  # Valid
            {"datetime": "invalid-date", "value": "200.0"},  # Invalid datetime
            {"datetime": "2024-01-01T01:00:00Z", "value": "invalid"},  # Invalid value
        ]

        mock_api_client.get_data = AsyncMock(return_value=invalid_data)
        mock_db_client._execute_query.return_value = []

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor.ingest()

        # Should process all records but only insert valid ones
        assert result["status"] == "success"
        assert result["records_processed"] == 1  # Only one valid transformation
        assert result["records_inserted"] == 1

    @pytest.mark.asyncio
    async def test_ingest_with_incremental_loading(
        self, mock_api_client, mock_db_client, mock_config_manager, sample_raw_api_data
    ):
        """Test ingestion with incremental loading based on last timestamp."""
        # Setup last timestamp
        last_timestamp = datetime(2024, 1, 1, 0, 30, 0)
        mock_db_client._execute_query.return_value = [[(last_timestamp,)]]

        mock_api_client.get_data = AsyncMock(return_value=sample_raw_api_data)

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor.ingest()

        # Should filter out records older than last timestamp
        assert result["status"] == "success"
        assert result["records_inserted"] < len(sample_raw_api_data)


class ConcreteTimeSeriesIngestor(TimeSeriesIngestor):
    """Concrete implementation of TimeSeriesIngestor for testing."""

    def __init__(
        self, api_client, db_client, config, interval, table_name="test_ts_table"
    ):
        super().__init__(api_client, db_client, config, interval)
        self._table_name = table_name
        self._schema = {
            "datetime": "DATETIME",
            "value": "FLOAT",
            "market": "VARCHAR(50)",
            "instrument": "VARCHAR(50)",
        }

    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """Mock implementation for testing."""
        return self.api_client.get_data(**kwargs)

    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Mock transformation for testing."""
        return {
            "datetime": datetime.fromisoformat(
                raw_entry["datetime"].replace("Z", "+00:00")
            ),
            "value": float(raw_entry["value"]),
            "market": raw_entry.get("market", "TEST"),
            "instrument": raw_entry.get("instrument", "TEST-PAIR"),
        }

    def _get_schema(self) -> Dict[str, Any]:
        return self._schema

    def _get_db_table_name(self) -> str:
        return self._table_name


class TestTimeSeriesIngestor:
    """Test cases for TimeSeriesIngestor class."""

    def test_initialization_valid_interval(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test TimeSeriesIngestor initialization with valid interval."""
        ingestor = ConcreteTimeSeriesIngestor(
            mock_api_client, mock_db_client, mock_config_manager, "1h"
        )

        assert ingestor.interval == "1h"
        assert ingestor.backfill_enabled == mock_config_manager.BACKFILL_ENABLED
        assert ingestor.max_backfill_days == mock_config_manager.MAX_BACKFILL_DAYS

    def test_initialization_invalid_interval(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test TimeSeriesIngestor initialization with invalid interval."""
        with pytest.raises(ValueError, match="Unsupported interval: 5m"):
            ConcreteTimeSeriesIngestor(
                mock_api_client, mock_db_client, mock_config_manager, "5m"
            )

    def test_get_interval_timedelta(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test interval to timedelta conversion."""
        # Test 1 day
        ingestor_1d = ConcreteTimeSeriesIngestor(
            mock_api_client, mock_db_client, mock_config_manager, "1d"
        )
        assert ingestor_1d._get_interval_timedelta() == timedelta(days=1)

        # Test 1 hour
        ingestor_1h = ConcreteTimeSeriesIngestor(
            mock_api_client, mock_db_client, mock_config_manager, "1h"
        )
        assert ingestor_1h._get_interval_timedelta() == timedelta(hours=1)

        # Test 1 minute
        ingestor_1m = ConcreteTimeSeriesIngestor(
            mock_api_client, mock_db_client, mock_config_manager, "1m"
        )
        assert ingestor_1m._get_interval_timedelta() == timedelta(minutes=1)

    def test_calculate_backfill_start_date_with_last_timestamp(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test backfill start date calculation with existing data."""
        ingestor = ConcreteTimeSeriesIngestor(
            mock_api_client, mock_db_client, mock_config_manager, "1h"
        )

        last_timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        start_date = ingestor._calculate_backfill_start_date(last_timestamp)

        expected = last_timestamp + timedelta(hours=1)
        assert start_date == expected

    def test_calculate_backfill_start_date_no_data_backfill_enabled(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test backfill start date calculation with no existing data and backfill enabled."""
        mock_config_manager.BACKFILL_ENABLED = True
        mock_config_manager.MAX_BACKFILL_DAYS = 30

        ingestor = ConcreteTimeSeriesIngestor(
            mock_api_client, mock_db_client, mock_config_manager, "1d"
        )

        with patch("src.ingestion.base.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 31, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            start_date = ingestor._calculate_backfill_start_date(None)

            expected = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            assert start_date == expected

    def test_calculate_backfill_start_date_no_data_backfill_disabled(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test backfill start date calculation with backfill disabled."""
        mock_config_manager.BACKFILL_ENABLED = False

        ingestor = ConcreteTimeSeriesIngestor(
            mock_api_client, mock_db_client, mock_config_manager, "1h"
        )

        with patch("src.ingestion.base.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            start_date = ingestor._calculate_backfill_start_date(None)

            assert start_date == mock_now

    @pytest.mark.asyncio
    async def test_ingest_with_backfill(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test ingestion with backfill functionality."""
        ingestor = ConcreteTimeSeriesIngestor(
            mock_api_client, mock_db_client, mock_config_manager, "1h"
        )

        # Mock the base ingest method
        with patch.object(ingestor, "ingest", new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = {"status": "success", "records_processed": 0}

            result = await ingestor.ingest_with_backfill(market="BINANCE")

            # Verify ingest was called with backfill parameters
            mock_ingest.assert_called_once()
            call_kwargs = mock_ingest.call_args[1]

            assert "start_date" in call_kwargs
            assert call_kwargs["interval"] == "1h"
            assert call_kwargs["market"] == "BINANCE"


class ConcreteMetadataIngestor(MetadataIngestor):
    """Concrete implementation of MetadataIngestor for testing."""

    def __init__(self, api_client, db_client, config, table_name="test_metadata_table"):
        super().__init__(api_client, db_client, config)
        self._table_name = table_name
        self._schema = {
            "id": "VARCHAR(50)",
            "symbol": "VARCHAR(50)",
            "name": "VARCHAR(255)",
            "description": "TEXT",
        }

    async def _fetch_data_from_api(self, **kwargs) -> List[Dict[str, Any]]:
        """Mock implementation for testing."""
        return self.api_client.get_data(**kwargs)

    def _transform_data(self, raw_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Mock transformation for testing."""
        return {
            "id": raw_entry.get("id", "TEST"),
            "symbol": raw_entry.get("symbol", "TEST"),
            "name": raw_entry.get("name", "Test Asset"),
            "description": raw_entry.get("description", "Test description"),
        }

    def _get_schema(self) -> Dict[str, Any]:
        return self._schema

    def _get_db_table_name(self) -> str:
        return self._table_name


class TestMetadataIngestor:
    """Test cases for MetadataIngestor class."""

    def test_initialization(self, mock_api_client, mock_db_client, mock_config_manager):
        """Test MetadataIngestor initialization."""
        ingestor = ConcreteMetadataIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        assert ingestor.full_refresh == mock_config_manager.METADATA_FULL_REFRESH
        assert (
            ingestor.change_detection_enabled
            == mock_config_manager.METADATA_CHANGE_DETECTION
        )

    def test_get_conflict_columns(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test metadata-specific conflict columns."""
        ingestor = ConcreteMetadataIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        columns = ingestor._get_conflict_columns()
        assert columns == ["id", "symbol", "name"]

    @pytest.mark.asyncio
    async def test_detect_changes_full_refresh(
        self,
        mock_api_client,
        mock_db_client,
        mock_config_manager,
        sample_metadata_records,
    ):
        """Test change detection with full refresh enabled."""
        mock_config_manager.METADATA_FULL_REFRESH = True

        ingestor = ConcreteMetadataIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor._detect_changes(sample_metadata_records)

        # With full refresh, all records should be returned
        assert result == sample_metadata_records

    @pytest.mark.asyncio
    async def test_detect_changes_disabled(
        self,
        mock_api_client,
        mock_db_client,
        mock_config_manager,
        sample_metadata_records,
    ):
        """Test change detection when disabled."""
        mock_config_manager.METADATA_CHANGE_DETECTION = False
        mock_config_manager.METADATA_FULL_REFRESH = False

        ingestor = ConcreteMetadataIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor._detect_changes(sample_metadata_records)

        # With change detection disabled, all records should be returned
        assert result == sample_metadata_records

    @pytest.mark.asyncio
    async def test_detect_changes_enabled(
        self,
        mock_api_client,
        mock_db_client,
        mock_config_manager,
        sample_metadata_records,
    ):
        """Test change detection when enabled (basic implementation)."""
        mock_config_manager.METADATA_CHANGE_DETECTION = True
        mock_config_manager.METADATA_FULL_REFRESH = False

        ingestor = ConcreteMetadataIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor._detect_changes(sample_metadata_records)

        # Current implementation returns all records
        # In a full implementation, this would compare with existing data
        assert result == sample_metadata_records

    @pytest.mark.asyncio
    async def test_ingest_metadata_full_refresh(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test metadata ingestion with full refresh."""
        mock_config_manager.METADATA_FULL_REFRESH = True

        ingestor = ConcreteMetadataIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        # Mock the base ingest method
        with patch.object(ingestor, "ingest", new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = {
                "status": "success",
                "records_processed": 0,
                "records_inserted": 0,
            }

            result = await ingestor.ingest_metadata()

            # Verify ingest was called with ignore_last_timestamp flag
            mock_ingest.assert_called_once()
            call_kwargs = mock_ingest.call_args[1]
            assert call_kwargs["ignore_last_timestamp"] is True

            # Verify metadata-specific fields in result
            assert result["full_refresh"] is True
            assert (
                result["change_detection_enabled"]
                == mock_config_manager.METADATA_CHANGE_DETECTION
            )

    @pytest.mark.asyncio
    async def test_ingest_metadata_incremental(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test metadata ingestion without full refresh."""
        mock_config_manager.METADATA_FULL_REFRESH = False

        ingestor = ConcreteMetadataIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        # Mock the base ingest method
        with patch.object(ingestor, "ingest", new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = {
                "status": "success",
                "records_processed": 0,
                "records_inserted": 0,
            }

            result = await ingestor.ingest_metadata()

            # Verify ingest was called without ignore_last_timestamp flag
            mock_ingest.assert_called_once()
            call_kwargs = mock_ingest.call_args[1]
            assert "ignore_last_timestamp" not in call_kwargs

            # Verify metadata-specific fields in result
            assert result["full_refresh"] is False
            assert (
                result["change_detection_enabled"]
                == mock_config_manager.METADATA_CHANGE_DETECTION
            )


class TestBaseIngestorEdgeCases:
    """Test edge cases and error conditions for BaseIngestor."""

    @pytest.mark.asyncio
    async def test_ingest_partial_failure(
        self, mock_api_client, mock_db_client, mock_config_manager, sample_raw_api_data
    ):
        """Test ingestion with partial failure (database insertion fails)."""
        mock_api_client.get_data = AsyncMock(return_value=sample_raw_api_data)
        mock_db_client._execute_query.return_value = []
        mock_db_client.insert_dataframe.side_effect = Exception("Database error")

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor.ingest()

        assert result["status"] == "partial_failure"
        assert result["records_processed"] == len(sample_raw_api_data)
        assert result["records_inserted"] == 0

    @pytest.mark.asyncio
    async def test_validate_records_with_exception(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test validation with records that cause exceptions during processing."""
        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        # Create records that will cause exceptions during validation
        problematic_records = [
            {
                "datetime": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "value": 100.0,
            },
            {
                "datetime": "invalid-datetime-object",  # This will cause an exception
                "value": 200.0,
            },
            {
                "datetime": datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
                "value": 300.0,
            },
        ]

        result = await ingestor._validate_and_filter_records(problematic_records)

        # Should skip the problematic record and continue with valid ones
        assert len(result) == 2
        assert all(record["value"] in [100.0, 300.0] for record in result)

    @pytest.mark.asyncio
    async def test_get_last_timestamp_multiple_filters(
        self, mock_api_client, mock_db_client, mock_config_manager
    ):
        """Test last timestamp retrieval with multiple filter conditions."""
        test_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        mock_db_client._execute_query.return_value = [[(test_timestamp,)]]

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor._get_last_ingested_timestamp(
            market="BINANCE", instrument="BTC-USD", status="ACTIVE"
        )

        assert result == test_timestamp.replace(tzinfo=timezone.utc)

        # Check that all filters were included in the query
        call_args = mock_db_client._execute_query.call_args
        query = call_args[0][0]
        params = call_args[1]["params"]

        assert "market = %s" in query
        assert "instrument = %s" in query
        assert "status = %s" in query
        assert params == ("BINANCE", "BTC-USD", "ACTIVE")

    @pytest.mark.asyncio
    async def test_ingest_with_performance_metrics(
        self, mock_api_client, mock_db_client, mock_config_manager, sample_raw_api_data
    ):
        """Test that ingestion includes performance metrics in results."""
        mock_api_client.get_data = AsyncMock(return_value=sample_raw_api_data)
        mock_db_client._execute_query.return_value = []

        ingestor = ConcreteIngestor(
            mock_api_client, mock_db_client, mock_config_manager
        )

        result = await ingestor.ingest()

        assert "duration_seconds" in result
        assert isinstance(result["duration_seconds"], float)
        assert result["duration_seconds"] >= 0
