"""
Shared pytest fixtures for ingestion framework tests.

This module provides reusable fixtures for testing the ingestion framework,
including mock API clients, database clients, configuration objects, and
test data generators.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import asyncio

from src.ingestion.config import (
    IngestionConfigManager,
    DatabaseConfig,
    ApiConfig,
    IngestionConfig,
    LoggingConfig,
    MonitoringConfig,
)


@pytest.fixture
def mock_api_client():
    """Mock API client for testing."""
    client = Mock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.request = AsyncMock()
    return client


@pytest.fixture
def mock_db_client():
    """Mock database client for testing."""
    client = Mock()
    client._execute_query = Mock()
    client.insert_dataframe = Mock()
    client.execute = Mock()
    client.fetch_all = Mock()
    client.fetch_one = Mock()
    return client


@pytest.fixture
def test_database_config():
    """Test database configuration."""
    return DatabaseConfig(
        host="test-host",
        port=3306,
        user="test-user",
        password="test-password",
        database="test-db",
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
    )


@pytest.fixture
def test_api_config():
    """Test API configuration."""
    return ApiConfig(
        ccdata_api_key="test-api-key",
        min_api_base_url="https://test-min-api.com",
        data_api_base_url="https://test-data-api.com",
        request_timeout=30,
        max_retries=3,
        retry_delay=1.0,
        rate_limit_calls_per_second=10.0,
        rate_limit_calls_per_minute=300,
        rate_limit_calls_per_hour=10000,
    )


@pytest.fixture
def test_ingestion_config():
    """Test ingestion configuration."""
    return IngestionConfig(
        batch_size=100,
        max_api_limit=1000,
        api_call_delay=0.1,
        backfill_enabled=True,
        max_backfill_days=30,
        metadata_full_refresh=False,
        metadata_change_detection=True,
        parallel_workers=2,
        chunk_size=1000,
        default_intervals=["1d", "1h"],
        max_limit_per_call={"1d": 1000, "1h": 500},
        futures_exchanges=["BINANCE", "COINBASE"],
        futures_instrument_statuses=["ACTIVE"],
        max_consecutive_failures=3,
        failure_backoff_multiplier=2.0,
        max_failure_backoff=60,
    )


@pytest.fixture
def test_logging_config():
    """Test logging configuration."""
    return LoggingConfig(
        level="DEBUG",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        file_enabled=False,
        file_path="test.log",
        file_max_bytes=1024,
        file_backup_count=1,
        console_enabled=True,
    )


@pytest.fixture
def test_monitoring_config():
    """Test monitoring configuration."""
    return MonitoringConfig(
        metrics_enabled=True,
        performance_monitoring=True,
        alert_on_failure=False,
        alert_on_consecutive_failures=5,
        health_check_interval=60,
        metrics_retention_days=7,
    )


@pytest.fixture
def mock_config_manager(
    test_database_config,
    test_api_config,
    test_ingestion_config,
    test_logging_config,
    test_monitoring_config,
):
    """Mock configuration manager for testing."""
    config = Mock(spec=IngestionConfigManager)
    config.env = "test"
    config.database = test_database_config
    config.api = test_api_config
    config.ingestion = test_ingestion_config
    config.logging = test_logging_config
    config.monitoring = test_monitoring_config

    # Add common attributes that ingestors expect
    config.BATCH_SIZE = test_ingestion_config.batch_size
    config.MAX_RETRIES = test_api_config.max_retries
    config.RETRY_DELAY = test_api_config.retry_delay
    config.BACKFILL_ENABLED = test_ingestion_config.backfill_enabled
    config.MAX_BACKFILL_DAYS = test_ingestion_config.max_backfill_days
    config.METADATA_FULL_REFRESH = test_ingestion_config.metadata_full_refresh
    config.METADATA_CHANGE_DETECTION = test_ingestion_config.metadata_change_detection

    return config


@pytest.fixture
def sample_raw_api_data():
    """Sample raw API data for testing transformations."""
    return [
        {
            "datetime": "2024-01-01T00:00:00Z",
            "market": "BINANCE",
            "instrument": "BTC-USD",
            "open": 45000.0,
            "high": 46000.0,
            "low": 44000.0,
            "close": 45500.0,
            "volume": 1000.0,
        },
        {
            "datetime": "2024-01-01T01:00:00Z",
            "market": "BINANCE",
            "instrument": "BTC-USD",
            "open": 45500.0,
            "high": 46500.0,
            "low": 45000.0,
            "close": 46000.0,
            "volume": 1200.0,
        },
        {
            "datetime": "2024-01-01T02:00:00Z",
            "market": "BINANCE",
            "instrument": "BTC-USD",
            "open": 46000.0,
            "high": 47000.0,
            "low": 45500.0,
            "close": 46500.0,
            "volume": 800.0,
        },
    ]


@pytest.fixture
def sample_transformed_data():
    """Sample transformed data for testing database operations."""
    return [
        {
            "datetime": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "market": "BINANCE",
            "instrument": "BTC-USD",
            "open": 45000.0,
            "high": 46000.0,
            "low": 44000.0,
            "close": 45500.0,
            "volume": 1000.0,
        },
        {
            "datetime": datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            "market": "BINANCE",
            "instrument": "BTC-USD",
            "open": 45500.0,
            "high": 46500.0,
            "low": 45000.0,
            "close": 46000.0,
            "volume": 1200.0,
        },
    ]


@pytest.fixture
def sample_metadata_records():
    """Sample metadata records for testing."""
    return [
        {
            "id": "BTC",
            "symbol": "BTC",
            "name": "Bitcoin",
            "description": "The first cryptocurrency",
            "website": "https://bitcoin.org",
            "last_updated": datetime.now(timezone.utc),
        },
        {
            "id": "ETH",
            "symbol": "ETH",
            "name": "Ethereum",
            "description": "Smart contract platform",
            "website": "https://ethereum.org",
            "last_updated": datetime.now(timezone.utc),
        },
    ]


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def test_datetime_utc():
    """Test datetime in UTC timezone."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def test_datetime_naive():
    """Test naive datetime (no timezone)."""
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def test_timestamp():
    """Test Unix timestamp."""
    return 1704110400  # 2024-01-01 12:00:00 UTC


@pytest.fixture
def test_date_strings():
    """Various date string formats for testing."""
    return [
        "2024-01-01 12:00:00",
        "2024-01-01T12:00:00",
        "2024-01-01T12:00:00Z",
        "2024-01-01T12:00:00.000Z",
        "2024-01-01T12:00:00.123456",
        "2024-01-01",
    ]


@pytest.fixture
def invalid_data_samples():
    """Invalid data samples for negative testing."""
    return {
        "numeric_values": [None, "", "invalid", float("nan"), float("inf"), "N/A"],
        "string_values": [None, "", "   ", "null", "None", "n/a"],
        "datetime_values": [None, "", "invalid-date", "2024-13-01", "not-a-date"],
    }


@pytest.fixture
def mock_database_results():
    """Mock database query results."""
    return {
        "last_timestamp": [(datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),)],
        "empty_result": [],
        "count_result": [(100,)],
        "metadata_records": [
            ("BTC", "Bitcoin", "The first cryptocurrency"),
            ("ETH", "Ethereum", "Smart contract platform"),
        ],
    }


@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing."""
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        {
            "datetime": base_time + timedelta(hours=i),
            "market": "BINANCE",
            "instrument": f"PAIR-{i % 10}",
            "value": float(i * 100),
            "volume": float(i * 10),
        }
        for i in range(10000)
    ]


@pytest_asyncio.fixture
async def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class MockAsyncContextManager:
    """Mock async context manager for testing."""

    def __init__(self, return_value=None):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_async_context():
    """Mock async context manager."""
    return MockAsyncContextManager


@pytest_asyncio.fixture
async def db_manager(mock_config_manager):
    """Async database manager fixture for testing."""
    from src.ingestion.async_db import AsyncDatabaseManager

    # Create a real instance but mock the pool
    manager = AsyncDatabaseManager(mock_config_manager)

    # Mock the pool and connection methods
    mock_pool = AsyncMock()
    mock_connection = AsyncMock()

    # Set up the mock pool
    manager._pool = mock_pool
    manager.pool = mock_pool  # For backward compatibility
    manager._initialized = True

    # Mock connection context manager
    async def mock_acquire():
        return mock_connection

    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    # Mock connection methods
    mock_connection.fetch.return_value = []
    mock_connection.execute.return_value = "SELECT 1"
    mock_connection.executemany.return_value = None

    yield manager

    # Cleanup
    if hasattr(manager, "close_pool"):
        await manager.close_pool()


@pytest_asyncio.fixture
async def cache_manager(mock_config_manager):
    """Cache manager fixture for testing."""
    from src.ingestion.cache import CacheManager

    manager = CacheManager(mock_config_manager)
    await manager.initialize()
    yield manager
    await manager.close()


@pytest_asyncio.fixture
async def monitoring_manager(mock_config_manager):
    """Monitoring manager fixture for testing."""
    from src.ingestion.monitoring import IngestionMonitor

    manager = IngestionMonitor(mock_config_manager)
    manager.start()
    yield manager
    manager.stop()


# Utility functions for test data generation
def generate_ohlcv_data(
    start_date: datetime,
    end_date: datetime,
    interval: str = "1h",
    market: str = "BINANCE",
    instrument: str = "BTC-USD",
) -> List[Dict[str, Any]]:
    """Generate OHLCV test data for a date range."""
    data = []
    current = start_date

    if interval == "1h":
        delta = timedelta(hours=1)
    elif interval == "1d":
        delta = timedelta(days=1)
    elif interval == "1m":
        delta = timedelta(minutes=1)
    else:
        raise ValueError(f"Unsupported interval: {interval}")

    base_price = 45000.0

    while current <= end_date:
        # Generate realistic OHLCV data
        open_price = base_price + (hash(str(current)) % 1000 - 500)
        high_price = open_price + (hash(str(current + delta)) % 500)
        low_price = open_price - (hash(str(current - delta)) % 500)
        close_price = open_price + (hash(str(current)) % 200 - 100)
        volume = 1000 + (hash(str(current)) % 5000)

        data.append(
            {
                "datetime": current.isoformat() + "Z",
                "market": market,
                "instrument": instrument,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            }
        )

        current += delta

    return data


@pytest.fixture
def ohlcv_data_generator():
    """OHLCV data generator function."""
    return generate_ohlcv_data
