"""
Shared utility modules for the unified data ingestion pipeline.

This module provides common, reusable functionalities including datetime handling,
data transformation patterns, batch processing, and performance monitoring.
"""

import time
import functools
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Union, Callable, Iterator
import logging

from ..logger_config import setup_logger


logger = setup_logger(__name__)


class DateTimeHandler:
    """
    Utility class for consistent timestamp conversions and datetime operations.

    Provides standardized methods for handling datetime operations across
    the ingestion pipeline, ensuring consistent timezone handling and
    timestamp conversions.
    """

    @staticmethod
    def ensure_utc_datetime(
        dt: Union[datetime, str, int, float, None],
    ) -> Optional[datetime]:
        """
        Ensure a datetime object is timezone-aware and in UTC.

        Args:
            dt: Input datetime in various formats (datetime, string, timestamp, None)

        Returns:
            UTC datetime object or None if input is None/invalid
        """
        if dt is None:
            return None

        try:
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    # Assume naive datetime is UTC
                    return dt.replace(tzinfo=timezone.utc)
                else:
                    # Convert to UTC if not already
                    return dt.astimezone(timezone.utc)

            elif isinstance(dt, (int, float)):
                # Assume timestamp is in seconds
                return datetime.fromtimestamp(dt, tz=timezone.utc)

            elif isinstance(dt, str):
                # Try to parse string datetime
                # Handle common formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%d",
                ]

                for fmt in formats:
                    try:
                        parsed_dt = datetime.strptime(dt, fmt)
                        return parsed_dt.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue

                # If no format matches, try ISO format parsing
                try:
                    parsed_dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                    return parsed_dt.astimezone(timezone.utc)
                except ValueError:
                    logger.warning(f"Unable to parse datetime string: {dt}")
                    return None

            else:
                logger.warning(f"Unsupported datetime type: {type(dt)}")
                return None

        except Exception as e:
            logger.warning(f"Error converting datetime {dt}: {e}")
            return None

    @staticmethod
    def to_timestamp(dt: datetime) -> int:
        """
        Convert datetime to Unix timestamp.

        Args:
            dt: Datetime object to convert

        Returns:
            Unix timestamp as integer
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())

    @staticmethod
    def get_period_boundaries(dt: datetime, interval: str) -> tuple[datetime, datetime]:
        """
        Get the start and end boundaries for a given period.

        Args:
            dt: Reference datetime
            interval: Time interval ('1d', '1h', '1m')

        Returns:
            Tuple of (period_start, period_end) datetimes
        """
        dt_utc = DateTimeHandler.ensure_utc_datetime(dt)

        if interval == "1d":
            period_start = dt_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1) - timedelta(microseconds=1)
        elif interval == "1h":
            period_start = dt_utc.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1) - timedelta(microseconds=1)
        elif interval == "1m":
            period_start = dt_utc.replace(second=0, microsecond=0)
            period_end = period_start + timedelta(minutes=1) - timedelta(microseconds=1)
        else:
            raise ValueError(f"Unsupported interval: {interval}")

        return period_start, period_end

    @staticmethod
    def get_end_of_previous_period(current_dt: datetime, interval: str) -> datetime:
        """
        Get the end of the previous complete period.

        Args:
            current_dt: Current datetime reference
            interval: Time interval ('1d', '1h', '1m')

        Returns:
            End datetime of the previous complete period
        """
        current_utc = DateTimeHandler.ensure_utc_datetime(current_dt)

        if interval == "1d":
            # End of previous day
            today_start = current_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            return today_start - timedelta(microseconds=1)
        elif interval == "1h":
            # End of previous hour
            current_hour_start = current_utc.replace(minute=0, second=0, microsecond=0)
            return current_hour_start - timedelta(microseconds=1)
        elif interval == "1m":
            # End of previous minute
            current_minute_start = current_utc.replace(second=0, microsecond=0)
            return current_minute_start - timedelta(microseconds=1)
        else:
            raise ValueError(f"Unsupported interval: {interval}")


class DataTransformer:
    """
    Utility class for common data transformation patterns.

    Provides standardized methods for data cleaning, validation,
    and transformation operations commonly used across ingestors.
    """

    @staticmethod
    def clean_numeric_value(
        value: Any, default: Optional[float] = None
    ) -> Optional[float]:
        """
        Clean and convert a value to float, handling various edge cases.

        Args:
            value: Input value to clean and convert
            default: Default value to return if conversion fails

        Returns:
            Cleaned float value or default
        """
        if value is None:
            return default

        try:
            if isinstance(value, (int, float)):
                return (
                    float(value)
                    if not (
                        isinstance(value, float)
                        and (
                            value != value
                            or value == float("inf")
                            or value == float("-inf")
                        )
                    )
                    else default
                )

            if isinstance(value, str):
                # Handle empty strings
                if not value.strip():
                    return default

                # Handle common string representations
                value = value.strip().replace(",", "")
                if value.lower() in ["null", "none", "n/a", "na", ""]:
                    return default

                return float(value)

            return default

        except (ValueError, TypeError):
            return default

    @staticmethod
    def clean_string_value(value: Any, default: Optional[str] = None) -> Optional[str]:
        """
        Clean and standardize string values.

        Args:
            value: Input value to clean
            default: Default value to return if cleaning fails

        Returns:
            Cleaned string value or default
        """
        if value is None:
            return default

        try:
            if isinstance(value, str):
                cleaned = value.strip()
                if not cleaned or cleaned.lower() in ["null", "none", "n/a", "na"]:
                    return default
                return cleaned

            # Convert non-string types to string
            return str(value).strip() if str(value).strip() else default

        except Exception:
            return default

    @staticmethod
    def validate_required_fields(
        record: Dict[str, Any], required_fields: List[str]
    ) -> bool:
        """
        Validate that a record contains all required fields.

        Args:
            record: Data record to validate
            required_fields: List of required field names

        Returns:
            True if all required fields are present and not None
        """
        for field in required_fields:
            if field not in record or record[field] is None:
                return False
        return True

    @staticmethod
    def standardize_market_instrument(market: str, instrument: str) -> tuple[str, str]:
        """
        Standardize market and instrument names for consistency.

        Args:
            market: Market name to standardize
            instrument: Instrument name to standardize

        Returns:
            Tuple of (standardized_market, standardized_instrument)
        """
        # Convert to uppercase and strip whitespace
        std_market = market.upper().strip() if market else ""
        std_instrument = instrument.upper().strip() if instrument else ""

        # Apply common standardizations
        market_mappings = {
            "BINANCE": "BINANCE",
            "BIN": "BINANCE",
            "COINBASE": "COINBASE",
            "CB": "COINBASE",
            "KRAKEN": "KRAKEN",
            "KRK": "KRAKEN",
        }

        std_market = market_mappings.get(std_market, std_market)

        return std_market, std_instrument


class BatchProcessor:
    """
    Utility class for efficient batch operations.

    Provides methods for processing data in batches to optimize
    memory usage and database operations.
    """

    @staticmethod
    def create_batches(items: List[Any], batch_size: int) -> Iterator[List[Any]]:
        """
        Split a list into batches of specified size.

        Args:
            items: List of items to batch
            batch_size: Maximum size of each batch

        Yields:
            Batches of items
        """
        if batch_size <= 0:
            raise ValueError("Batch size must be positive")

        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]

    @staticmethod
    def process_in_batches(
        items: List[Any],
        processor_func: Callable[[List[Any]], Any],
        batch_size: int = 1000,
    ) -> List[Any]:
        """
        Process items in batches using the provided processor function.

        Args:
            items: List of items to process
            processor_func: Function to process each batch
            batch_size: Size of each batch

        Returns:
            List of results from processing each batch
        """
        results = []

        for batch in BatchProcessor.create_batches(items, batch_size):
            try:
                result = processor_func(batch)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing batch: {e}")
                # Continue with next batch instead of failing completely
                continue

        return results

    @staticmethod
    def merge_batch_results(batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge results from multiple batch operations.

        Args:
            batch_results: List of result dictionaries from batch operations

        Returns:
            Merged result dictionary with aggregated statistics
        """
        merged = {
            "total_processed": 0,
            "total_inserted": 0,
            "total_errors": 0,
            "batch_count": len(batch_results),
            "successful_batches": 0,
            "failed_batches": 0,
        }

        for result in batch_results:
            if isinstance(result, dict):
                merged["total_processed"] += result.get("records_processed", 0)
                merged["total_inserted"] += result.get("records_inserted", 0)
                merged["total_errors"] += result.get("errors", 0)

                if result.get("status") == "success":
                    merged["successful_batches"] += 1
                else:
                    merged["failed_batches"] += 1

        merged["success_rate"] = (
            (merged["successful_batches"] / merged["batch_count"]) * 100.0
            if merged["batch_count"] > 0
            else 0.0
        )

        return merged


def performance_monitor(func: Callable) -> Callable:
    """
    Decorator for monitoring performance of ingestion operations.

    This decorator logs execution time, memory usage, and other
    performance metrics for decorated functions.

    Args:
        func: Function to monitor

    Returns:
        Decorated function with performance monitoring
    """

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__qualname__}"

        logger.info(f"Starting {func_name}")

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log performance metrics
            logger.info(f"Completed {func_name} in {execution_time:.2f}s")

            # Add performance info to result if it's a dict
            if isinstance(result, dict):
                result["execution_time_seconds"] = execution_time
                result["function_name"] = func_name

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func_name} after {execution_time:.2f}s: {e}")
            raise

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__qualname__}"

        logger.info(f"Starting {func_name}")

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log performance metrics
            logger.info(f"Completed {func_name} in {execution_time:.2f}s")

            # Add performance info to result if it's a dict
            if isinstance(result, dict):
                result["execution_time_seconds"] = execution_time
                result["function_name"] = func_name

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func_name} after {execution_time:.2f}s: {e}")
            raise

    # Return appropriate wrapper based on whether function is async
    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class IngestionMetrics:
    """
    Utility class for collecting and reporting ingestion metrics.

    Provides methods for tracking ingestion performance, success rates,
    and other operational metrics.
    """

    def __init__(self):
        self.metrics = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_records_processed": 0,
            "total_records_inserted": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "last_run_timestamp": None,
            "last_successful_run": None,
            "error_counts": {},
        }

    def record_run(self, result: Dict[str, Any]):
        """
        Record metrics from an ingestion run.

        Args:
            result: Result dictionary from ingestion run
        """
        self.metrics["total_runs"] += 1
        self.metrics["last_run_timestamp"] = datetime.now(timezone.utc)

        if result.get("status") == "success":
            self.metrics["successful_runs"] += 1
            self.metrics["last_successful_run"] = self.metrics["last_run_timestamp"]
        else:
            self.metrics["failed_runs"] += 1

            # Track error types
            error = result.get("error", "unknown_error")
            self.metrics["error_counts"][error] = (
                self.metrics["error_counts"].get(error, 0) + 1
            )

        # Update record counts
        self.metrics["total_records_processed"] += result.get("records_processed", 0)
        self.metrics["total_records_inserted"] += result.get("records_inserted", 0)

        # Update execution time
        execution_time = result.get("duration_seconds", 0)
        self.metrics["total_execution_time"] += execution_time
        self.metrics["average_execution_time"] = (
            self.metrics["total_execution_time"] / self.metrics["total_runs"]
        )

    def get_success_rate(self) -> float:
        """
        Calculate the success rate of ingestion runs.

        Returns:
            Success rate as a percentage (0-100)
        """
        if self.metrics["total_runs"] == 0:
            return 0.0

        return (self.metrics["successful_runs"] / self.metrics["total_runs"]) * 100

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all collected metrics.

        Returns:
            Dictionary containing metric summary
        """
        summary = self.metrics.copy()
        summary["success_rate_percent"] = self.get_success_rate()
        return summary

    def reset_metrics(self):
        """Reset all metrics to initial state."""
        self.__init__()


# Global metrics instance for tracking across the application
ingestion_metrics = IngestionMetrics()
