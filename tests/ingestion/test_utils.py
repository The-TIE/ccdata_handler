"""
Unit tests for the ingestion utilities module.

This module tests the utility classes and functions including DateTimeHandler,
DataTransformer, BatchProcessor, performance monitoring decorator, and
IngestionMetrics.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import time
import asyncio

from src.ingestion.utils import (
    DateTimeHandler,
    DataTransformer,
    BatchProcessor,
    performance_monitor,
    IngestionMetrics,
    ingestion_metrics,
)


class TestDateTimeHandler:
    """Test cases for DateTimeHandler utility class."""

    def test_ensure_utc_datetime_with_utc_datetime(self):
        """Test with already UTC datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = DateTimeHandler.ensure_utc_datetime(dt)

        assert result == dt
        assert result.tzinfo == timezone.utc

    def test_ensure_utc_datetime_with_naive_datetime(self):
        """Test with naive datetime (assumes UTC)."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = DateTimeHandler.ensure_utc_datetime(dt)

        assert result.tzinfo == timezone.utc
        assert result.replace(tzinfo=None) == dt

    def test_ensure_utc_datetime_with_other_timezone(self):
        """Test with datetime in different timezone."""
        # Create datetime in EST (UTC-5)
        est = timezone(timedelta(hours=-5))
        dt = datetime(2024, 1, 1, 7, 0, 0, tzinfo=est)
        result = DateTimeHandler.ensure_utc_datetime(dt)

        assert result.tzinfo == timezone.utc
        assert result == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_ensure_utc_datetime_with_timestamp(self):
        """Test with Unix timestamp."""
        timestamp = 1704110400  # 2024-01-01 12:00:00 UTC
        result = DateTimeHandler.ensure_utc_datetime(timestamp)

        expected = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_ensure_utc_datetime_with_float_timestamp(self):
        """Test with float timestamp."""
        timestamp = 1704110400.5  # 2024-01-01 12:00:00.5 UTC
        result = DateTimeHandler.ensure_utc_datetime(timestamp)

        expected = datetime(2024, 1, 1, 12, 0, 0, 500000, tzinfo=timezone.utc)
        assert result == expected

    @pytest.mark.parametrize(
        "date_string,expected",
        [
            (
                "2024-01-01 12:00:00",
                datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            (
                "2024-01-01T12:00:00",
                datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            (
                "2024-01-01T12:00:00Z",
                datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            (
                "2024-01-01T12:00:00.123456",
                datetime(2024, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc),
            ),
            (
                "2024-01-01T12:00:00.123456Z",
                datetime(2024, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc),
            ),
            ("2024-01-01", datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
        ],
    )
    def test_ensure_utc_datetime_with_string_formats(self, date_string, expected):
        """Test with various string datetime formats."""
        result = DateTimeHandler.ensure_utc_datetime(date_string)
        assert result == expected

    def test_ensure_utc_datetime_with_iso_format(self):
        """Test with ISO format string."""
        iso_string = "2024-01-01T12:00:00+05:00"
        result = DateTimeHandler.ensure_utc_datetime(iso_string)

        expected = datetime(2024, 1, 1, 7, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_ensure_utc_datetime_with_none(self):
        """Test with None input."""
        result = DateTimeHandler.ensure_utc_datetime(None)
        assert result is None

    def test_ensure_utc_datetime_with_invalid_string(self):
        """Test with invalid string format."""
        result = DateTimeHandler.ensure_utc_datetime("invalid-date")
        assert result is None

    def test_ensure_utc_datetime_with_invalid_type(self):
        """Test with unsupported type."""
        result = DateTimeHandler.ensure_utc_datetime(["not", "a", "datetime"])
        assert result is None

    def test_to_timestamp_with_utc_datetime(self):
        """Test timestamp conversion with UTC datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = DateTimeHandler.to_timestamp(dt)

        assert result == 1704110400

    def test_to_timestamp_with_naive_datetime(self):
        """Test timestamp conversion with naive datetime (assumes UTC)."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = DateTimeHandler.to_timestamp(dt)

        assert result == 1704110400

    @pytest.mark.parametrize(
        "interval,expected_start,expected_end",
        [
            (
                "1d",
                datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 23, 59, 59, 999999, tzinfo=timezone.utc),
            ),
            (
                "1h",
                datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 12, 59, 59, 999999, tzinfo=timezone.utc),
            ),
            (
                "1m",
                datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 12, 30, 59, 999999, tzinfo=timezone.utc),
            ),
        ],
    )
    def test_get_period_boundaries(self, interval, expected_start, expected_end):
        """Test period boundary calculations."""
        dt = datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=timezone.utc)
        start, end = DateTimeHandler.get_period_boundaries(dt, interval)

        assert start == expected_start
        assert end == expected_end

    def test_get_period_boundaries_invalid_interval(self):
        """Test period boundaries with invalid interval."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="Unsupported interval: 5m"):
            DateTimeHandler.get_period_boundaries(dt, "5m")

    @pytest.mark.parametrize(
        "interval,expected_offset",
        [
            ("1d", timedelta(days=1)),
            ("1h", timedelta(hours=1)),
            ("1m", timedelta(minutes=1)),
        ],
    )
    def test_get_end_of_previous_period(self, interval, expected_offset):
        """Test getting end of previous period."""
        current_dt = datetime(2024, 1, 2, 12, 30, 45, tzinfo=timezone.utc)
        result = DateTimeHandler.get_end_of_previous_period(current_dt, interval)

        # The result should be just before the start of the current period
        if interval == "1d":
            expected = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc) - timedelta(
                microseconds=1
            )
        elif interval == "1h":
            expected = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc) - timedelta(
                microseconds=1
            )
        elif interval == "1m":
            expected = datetime(2024, 1, 2, 12, 30, 0, tzinfo=timezone.utc) - timedelta(
                microseconds=1
            )

        assert result == expected

    def test_get_end_of_previous_period_invalid_interval(self):
        """Test previous period end with invalid interval."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="Unsupported interval: 5m"):
            DateTimeHandler.get_end_of_previous_period(dt, "5m")


class TestDataTransformer:
    """Test cases for DataTransformer utility class."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (100, 100.0),
            (100.5, 100.5),
            ("100", 100.0),
            ("100.5", 100.5),
            ("1,000.5", 1000.5),  # With comma
            (None, None),
            ("", None),
            ("   ", None),
            ("null", None),
            ("N/A", None),
            ("na", None),
            ("invalid", None),
        ],
    )
    def test_clean_numeric_value(self, value, expected):
        """Test numeric value cleaning with various inputs."""
        result = DataTransformer.clean_numeric_value(value)
        assert result == expected

    def test_clean_numeric_value_with_default(self):
        """Test numeric value cleaning with custom default."""
        result = DataTransformer.clean_numeric_value("invalid", default=0.0)
        assert result == 0.0

    @pytest.mark.parametrize(
        "value,expected",
        [
            (float("nan"), None),
            (float("inf"), None),
            (float("-inf"), None),
        ],
    )
    def test_clean_numeric_value_special_floats(self, value, expected):
        """Test cleaning of special float values."""
        result = DataTransformer.clean_numeric_value(value)
        assert result == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("hello", "hello"),
            ("  hello  ", "hello"),
            ("", None),
            ("   ", None),
            ("null", None),
            ("None", None),
            ("N/A", None),
            ("na", None),
            (None, None),
            (123, "123"),
            (123.45, "123.45"),
        ],
    )
    def test_clean_string_value(self, value, expected):
        """Test string value cleaning with various inputs."""
        result = DataTransformer.clean_string_value(value)
        assert result == expected

    def test_clean_string_value_with_default(self):
        """Test string value cleaning with custom default."""
        result = DataTransformer.clean_string_value("", default="default")
        assert result == "default"

    def test_validate_required_fields_all_present(self):
        """Test validation when all required fields are present."""
        record = {
            "field1": "value1",
            "field2": "value2",
            "field3": "value3",
        }
        required_fields = ["field1", "field2"]

        result = DataTransformer.validate_required_fields(record, required_fields)
        assert result is True

    def test_validate_required_fields_missing_field(self):
        """Test validation when required field is missing."""
        record = {
            "field1": "value1",
            "field3": "value3",
        }
        required_fields = ["field1", "field2"]

        result = DataTransformer.validate_required_fields(record, required_fields)
        assert result is False

    def test_validate_required_fields_none_value(self):
        """Test validation when required field is None."""
        record = {
            "field1": "value1",
            "field2": None,
        }
        required_fields = ["field1", "field2"]

        result = DataTransformer.validate_required_fields(record, required_fields)
        assert result is False

    @pytest.mark.parametrize(
        "market,instrument,expected",
        [
            ("binance", "btc-usd", ("BINANCE", "BTC-USD")),
            ("  COINBASE  ", "  eth-usd  ", ("COINBASE", "ETH-USD")),
            ("bin", "btc-usd", ("BINANCE", "BTC-USD")),
            ("cb", "eth-usd", ("COINBASE", "ETH-USD")),
            ("krk", "btc-eur", ("KRAKEN", "BTC-EUR")),
            ("unknown", "pair", ("UNKNOWN", "PAIR")),
            ("", "", ("", "")),
            (None, None, ("", "")),
        ],
    )
    def test_standardize_market_instrument(self, market, instrument, expected):
        """Test market and instrument name standardization."""
        result = DataTransformer.standardize_market_instrument(market, instrument)
        assert result == expected


class TestBatchProcessor:
    """Test cases for BatchProcessor utility class."""

    def test_create_batches_normal_case(self):
        """Test batch creation with normal input."""
        items = list(range(10))
        batch_size = 3

        batches = list(BatchProcessor.create_batches(items, batch_size))

        assert len(batches) == 4
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]

    def test_create_batches_exact_division(self):
        """Test batch creation when items divide evenly."""
        items = list(range(9))
        batch_size = 3

        batches = list(BatchProcessor.create_batches(items, batch_size))

        assert len(batches) == 3
        assert all(len(batch) == 3 for batch in batches)

    def test_create_batches_empty_list(self):
        """Test batch creation with empty list."""
        items = []
        batch_size = 3

        batches = list(BatchProcessor.create_batches(items, batch_size))

        assert len(batches) == 0

    def test_create_batches_single_item(self):
        """Test batch creation with single item."""
        items = [1]
        batch_size = 3

        batches = list(BatchProcessor.create_batches(items, batch_size))

        assert len(batches) == 1
        assert batches[0] == [1]

    def test_create_batches_invalid_batch_size(self):
        """Test batch creation with invalid batch size."""
        items = [1, 2, 3]

        with pytest.raises(ValueError, match="Batch size must be positive"):
            list(BatchProcessor.create_batches(items, 0))

        with pytest.raises(ValueError, match="Batch size must be positive"):
            list(BatchProcessor.create_batches(items, -1))

    def test_process_in_batches_success(self):
        """Test batch processing with successful processor function."""
        items = list(range(10))

        def processor(batch):
            return {"processed": len(batch), "sum": sum(batch)}

        results = BatchProcessor.process_in_batches(items, processor, batch_size=3)

        assert len(results) == 4
        assert results[0] == {"processed": 3, "sum": 3}  # [0, 1, 2]
        assert results[1] == {"processed": 3, "sum": 12}  # [3, 4, 5]
        assert results[2] == {"processed": 3, "sum": 21}  # [6, 7, 8]
        assert results[3] == {"processed": 1, "sum": 9}  # [9]

    def test_process_in_batches_with_errors(self):
        """Test batch processing with processor function that raises errors."""
        items = list(range(6))

        def processor(batch):
            if batch[0] == 3:  # Fail on second batch
                raise Exception("Processing error")
            return {"processed": len(batch)}

        results = BatchProcessor.process_in_batches(items, processor, batch_size=3)

        # Should continue processing despite error in one batch
        assert len(results) == 1  # Only successful batches
        assert results[0] == {"processed": 3}

    def test_merge_batch_results_success(self):
        """Test merging of successful batch results."""
        batch_results = [
            {
                "status": "success",
                "records_processed": 100,
                "records_inserted": 95,
                "errors": 5,
            },
            {
                "status": "success",
                "records_processed": 200,
                "records_inserted": 190,
                "errors": 10,
            },
            {
                "status": "success",
                "records_processed": 50,
                "records_inserted": 50,
                "errors": 0,
            },
        ]

        merged = BatchProcessor.merge_batch_results(batch_results)

        assert merged["total_processed"] == 350
        assert merged["total_inserted"] == 335
        assert merged["total_errors"] == 15
        assert merged["batch_count"] == 3
        assert merged["successful_batches"] == 3
        assert merged["failed_batches"] == 0
        assert merged["success_rate"] == 100.0

    def test_merge_batch_results_mixed(self):
        """Test merging of mixed success/failure batch results."""
        batch_results = [
            {"status": "success", "records_processed": 100, "records_inserted": 100},
            {
                "status": "failure",
                "records_processed": 50,
                "records_inserted": 0,
                "errors": 50,
            },
            {"status": "success", "records_processed": 75, "records_inserted": 70},
        ]

        merged = BatchProcessor.merge_batch_results(batch_results)

        assert merged["total_processed"] == 225
        assert merged["total_inserted"] == 170
        assert merged["successful_batches"] == 2
        assert merged["failed_batches"] == 1
        assert merged["success_rate"] == pytest.approx(66.67, rel=1e-2)

    def test_merge_batch_results_empty(self):
        """Test merging of empty batch results."""
        merged = BatchProcessor.merge_batch_results([])

        assert merged["total_processed"] == 0
        assert merged["total_inserted"] == 0
        assert merged["batch_count"] == 0
        assert merged["success_rate"] == 0


class TestPerformanceMonitor:
    """Test cases for performance_monitor decorator."""

    def test_performance_monitor_sync_function(self):
        """Test performance monitoring on synchronous function."""

        @performance_monitor
        def test_function(x, y):
            time.sleep(0.01)  # Small delay to measure
            return x + y

        result = test_function(1, 2)

        assert result == 3
        # Note: In a real test, you might want to check logs or metrics

    def test_performance_monitor_sync_function_with_dict_result(self):
        """Test performance monitoring with dictionary result."""

        @performance_monitor
        def test_function():
            return {"value": 42}

        result = test_function()

        assert result["value"] == 42
        assert "execution_time_seconds" in result
        assert "function_name" in result
        assert isinstance(result["execution_time_seconds"], float)

    @pytest.mark.asyncio
    async def test_performance_monitor_async_function(self):
        """Test performance monitoring on asynchronous function."""

        @performance_monitor
        async def test_async_function(x, y):
            await asyncio.sleep(0.01)  # Small delay to measure
            return x * y

        result = await test_async_function(3, 4)

        assert result == 12

    @pytest.mark.asyncio
    async def test_performance_monitor_async_function_with_dict_result(self):
        """Test performance monitoring on async function with dictionary result."""

        @performance_monitor
        async def test_async_function():
            return {"async_value": 100}

        result = await test_async_function()

        assert result["async_value"] == 100
        assert "execution_time_seconds" in result
        assert "function_name" in result
        assert isinstance(result["execution_time_seconds"], float)

    def test_performance_monitor_sync_function_with_exception(self):
        """Test performance monitoring when function raises exception."""

        @performance_monitor
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

    @pytest.mark.asyncio
    async def test_performance_monitor_async_function_with_exception(self):
        """Test performance monitoring when async function raises exception."""

        @performance_monitor
        async def failing_async_function():
            raise RuntimeError("Async test error")

        with pytest.raises(RuntimeError, match="Async test error"):
            await failing_async_function()


class TestIngestionMetrics:
    """Test cases for IngestionMetrics class."""

    def test_initialization(self):
        """Test IngestionMetrics initialization."""
        metrics = IngestionMetrics()

        assert metrics.metrics["total_runs"] == 0
        assert metrics.metrics["successful_runs"] == 0
        assert metrics.metrics["failed_runs"] == 0
        assert metrics.metrics["total_records_processed"] == 0
        assert metrics.metrics["total_records_inserted"] == 0
        assert metrics.metrics["total_execution_time"] == 0.0
        assert metrics.metrics["average_execution_time"] == 0.0
        assert metrics.metrics["last_run_timestamp"] is None
        assert metrics.metrics["last_successful_run"] is None
        assert metrics.metrics["error_counts"] == {}

    def test_record_run_success(self):
        """Test recording a successful run."""
        metrics = IngestionMetrics()

        result = {
            "status": "success",
            "records_processed": 100,
            "records_inserted": 95,
            "duration_seconds": 10.5,
        }

        metrics.record_run(result)

        assert metrics.metrics["total_runs"] == 1
        assert metrics.metrics["successful_runs"] == 1
        assert metrics.metrics["failed_runs"] == 0
        assert metrics.metrics["total_records_processed"] == 100
        assert metrics.metrics["total_records_inserted"] == 95
        assert metrics.metrics["total_execution_time"] == 10.5
        assert metrics.metrics["average_execution_time"] == 10.5
        assert metrics.metrics["last_run_timestamp"] is not None
        assert metrics.metrics["last_successful_run"] is not None

    def test_record_run_failure(self):
        """Test recording a failed run."""
        metrics = IngestionMetrics()

        result = {
            "status": "failure",
            "error": "API timeout",
            "records_processed": 50,
            "records_inserted": 0,
            "duration_seconds": 5.0,
        }

        metrics.record_run(result)

        assert metrics.metrics["total_runs"] == 1
        assert metrics.metrics["successful_runs"] == 0
        assert metrics.metrics["failed_runs"] == 1
        assert metrics.metrics["error_counts"]["API timeout"] == 1
        assert metrics.metrics["last_successful_run"] is None

    def test_record_multiple_runs(self):
        """Test recording multiple runs."""
        metrics = IngestionMetrics()

        # Record successful run
        success_result = {
            "status": "success",
            "records_processed": 100,
            "records_inserted": 100,
            "duration_seconds": 5.0,
        }
        metrics.record_run(success_result)

        # Record failed run
        failure_result = {
            "status": "failure",
            "error": "Database error",
            "records_processed": 50,
            "records_inserted": 0,
            "duration_seconds": 2.0,
        }
        metrics.record_run(failure_result)

        # Record another successful run
        success_result2 = {
            "status": "success",
            "records_processed": 200,
            "records_inserted": 190,
            "duration_seconds": 8.0,
        }
        metrics.record_run(success_result2)

        assert metrics.metrics["total_runs"] == 3
        assert metrics.metrics["successful_runs"] == 2
        assert metrics.metrics["failed_runs"] == 1
        assert metrics.metrics["total_records_processed"] == 350
        assert metrics.metrics["total_records_inserted"] == 290
        assert metrics.metrics["total_execution_time"] == 15.0
        assert metrics.metrics["average_execution_time"] == 5.0
        assert metrics.metrics["error_counts"]["Database error"] == 1

    def test_get_success_rate(self):
        """Test success rate calculation."""
        metrics = IngestionMetrics()

        # No runs yet
        assert metrics.get_success_rate() == 0.0

        # Add some runs
        metrics.record_run({"status": "success"})
        metrics.record_run({"status": "failure", "error": "test"})
        metrics.record_run({"status": "success"})
        metrics.record_run({"status": "failure", "error": "test"})

        # 2 successful out of 4 total = 50%
        assert metrics.get_success_rate() == 50.0

    def test_get_summary(self):
        """Test getting metrics summary."""
        metrics = IngestionMetrics()

        # Record some runs
        metrics.record_run(
            {
                "status": "success",
                "records_processed": 100,
                "records_inserted": 95,
                "duration_seconds": 10.0,
            }
        )
        metrics.record_run(
            {
                "status": "failure",
                "error": "timeout",
                "records_processed": 50,
                "records_inserted": 0,
                "duration_seconds": 5.0,
            }
        )

        summary = metrics.get_summary()

        assert summary["total_runs"] == 2
        assert summary["successful_runs"] == 1
        assert summary["failed_runs"] == 1
        assert summary["success_rate_percent"] == 50.0
        assert summary["total_records_processed"] == 150
        assert summary["total_records_inserted"] == 95
        assert summary["total_execution_time"] == 15.0
        assert summary["average_execution_time"] == 7.5
        assert "last_run_timestamp" in summary
        assert "error_counts" in summary

    def test_reset_metrics(self):
        """Test resetting metrics to initial state."""
        metrics = IngestionMetrics()

        # Record some data
        metrics.record_run(
            {
                "status": "success",
                "records_processed": 100,
                "records_inserted": 100,
            }
        )

        # Verify data was recorded
        assert metrics.metrics["total_runs"] == 1

        # Reset metrics
        metrics.reset_metrics()

        # Verify reset to initial state
        assert metrics.metrics["total_runs"] == 0
        assert metrics.metrics["successful_runs"] == 0
        assert metrics.metrics["total_records_processed"] == 0
        assert metrics.metrics["error_counts"] == {}

    def test_global_metrics_instance(self):
        """Test that global metrics instance exists and works."""
        # Reset global instance for clean test
        ingestion_metrics.reset_metrics()

        # Record a run
        ingestion_metrics.record_run(
            {
                "status": "success",
                "records_processed": 50,
                "records_inserted": 50,
            }
        )

        assert ingestion_metrics.metrics["total_runs"] == 1
        assert ingestion_metrics.get_success_rate() == 100.0


class TestUtilsEdgeCases:
    """Test edge cases and error conditions for utility functions."""

    def test_datetime_handler_with_malformed_iso_string(self):
        """Test DateTimeHandler with malformed ISO string."""
        malformed_strings = [
            "2024-01-01T25:00:00Z",  # Invalid hour
            "2024-13-01T12:00:00Z",  # Invalid month
            "2024-01-32T12:00:00Z",  # Invalid day
            "not-a-date-at-all",
        ]

        for date_string in malformed_strings:
            result = DateTimeHandler.ensure_utc_datetime(date_string)
            assert result is None

    def test_data_transformer_with_extreme_values(self):
        """Test DataTransformer with extreme numeric values."""
        extreme_values = [
            1e308,  # Very large number
            -1e308,  # Very large negative number
            1e-308,  # Very small number
            0,  # Zero
        ]

        for value in extreme_values:
            result = DataTransformer.clean_numeric_value(value)
            assert isinstance(result, float)
            assert result == float(value)

    def test_batch_processor_with_large_dataset(self, performance_test_data):
        """Test BatchProcessor with large dataset."""

        def simple_processor(batch):
            return {"count": len(batch)}

        results = BatchProcessor.process_in_batches(
            performance_test_data, simple_processor, batch_size=1000
        )

        assert len(results) == 10  # 10000 items / 1000 batch_size
        assert all(result["count"] == 1000 for result in results)

    def test_performance_monitor_with_nested_calls(self):
        """Test performance monitor with nested decorated functions."""

        @performance_monitor
        def outer_function(x):
            return inner_function(x * 2)

        @performance_monitor
        def inner_function(x):
            return {"result": x + 1}

        result = outer_function(5)

        # Should have metrics from both functions
        assert result["result"] == 11  # (5 * 2) + 1
        assert "execution_time_seconds" in result
        assert "function_name" in result
