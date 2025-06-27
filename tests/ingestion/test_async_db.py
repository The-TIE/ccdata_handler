"""
Unit tests for async database operations in the unified data ingestion pipeline.

This module tests the AsyncDbConnectionManager with comprehensive coverage of
connection pooling, async query execution, retry logic, bulk loading, and
error handling scenarios.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import tempfile
import os

import aiomysql
import polars as pl

from src.ingestion.async_db import AsyncDbConnectionManager
from src.ingestion.config import DatabaseConfig


class TestAsyncDbConnectionManager:
    """Test cases for AsyncDbConnectionManager."""

    @pytest.fixture
    def mock_config(self):
        """Mock database configuration."""
        config = Mock(spec=DatabaseConfig)
        config.host = "test-host"
        config.port = 3306
        config.user = "test-user"
        config.password = "test-password"
        config.database = "test-db"
        config.pool_size = 5
        config.pool_recycle = 3600
        return config

    @pytest.fixture
    def mock_pool(self):
        """Mock aiomysql connection pool."""
        pool = AsyncMock()
        pool.acquire = AsyncMock()
        pool.release = AsyncMock()
        pool.close = Mock()
        pool.wait_closed = AsyncMock()
        return pool

    @pytest.fixture
    def mock_connection(self):
        """Mock aiomysql connection."""
        conn = AsyncMock()
        conn.commit = AsyncMock()
        conn.rollback = AsyncMock()

        # Create a mock cursor that supports async context manager
        mock_cursor = AsyncMock()
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=None)
        mock_cursor.execute = AsyncMock()
        mock_cursor.executemany = AsyncMock()
        mock_cursor.fetchall = AsyncMock()
        mock_cursor.fetchone = AsyncMock()
        mock_cursor.rowcount = 10

        conn.cursor.return_value = mock_cursor
        return conn

    @pytest.fixture
    def mock_cursor(self):
        """Mock aiomysql cursor."""
        cursor = AsyncMock()
        cursor.execute = AsyncMock()
        cursor.executemany = AsyncMock()
        cursor.fetchall = AsyncMock()
        cursor.fetchone = AsyncMock()
        cursor.rowcount = 10
        cursor.__aenter__ = AsyncMock(return_value=cursor)
        cursor.__aexit__ = AsyncMock(return_value=None)
        return cursor

    @pytest_asyncio.fixture
    async def db_manager(self, mock_config):
        """Create AsyncDbConnectionManager instance."""
        manager = AsyncDbConnectionManager(mock_config)
        yield manager
        if manager.pool:
            await manager.close_pool()

    def test_init(self, mock_config):
        """Test AsyncDbConnectionManager initialization."""
        manager = AsyncDbConnectionManager(mock_config)

        assert manager.config == mock_config
        assert manager.pool is None
        assert manager._pool_lock is not None

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        with patch("src.ingestion.async_db.get_database_config") as mock_get_config:
            mock_config = Mock()
            mock_get_config.return_value = mock_config

            manager = AsyncDbConnectionManager()
            assert manager.config == mock_config

    @pytest.mark.asyncio
    async def test_initialize_pool_success(self, db_manager, mock_pool):
        """Test successful pool initialization."""
        # Create an async mock that can be awaited
        async_mock_pool = AsyncMock(return_value=mock_pool)

        with patch("aiomysql.create_pool", async_mock_pool) as mock_create:
            await db_manager.initialize_pool()

            assert db_manager.pool == mock_pool
            mock_create.assert_called_once_with(
                host=db_manager.config.host,
                port=db_manager.config.port,
                user=db_manager.config.user,
                password=db_manager.config.password,
                db=db_manager.config.database,
                charset="utf8mb4",
                minsize=1,
                maxsize=db_manager.config.pool_size,
                pool_recycle=db_manager.config.pool_recycle,
                autocommit=False,
                local_infile=True,
            )

    @pytest.mark.asyncio
    async def test_initialize_pool_already_initialized(self, db_manager, mock_pool):
        """Test pool initialization when already initialized."""
        db_manager.pool = mock_pool

        with patch("aiomysql.create_pool") as mock_create:
            await db_manager.initialize_pool()
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_pool_failure(self, db_manager):
        """Test pool initialization failure."""
        with patch("aiomysql.create_pool", side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await db_manager.initialize_pool()

    @pytest.mark.asyncio
    async def test_close_pool(self, db_manager, mock_pool):
        """Test pool closure."""
        db_manager.pool = mock_pool

        await db_manager.close_pool()

        mock_pool.close.assert_called_once()
        mock_pool.wait_closed.assert_called_once()
        assert db_manager.pool is None

    @pytest.mark.asyncio
    async def test_close_pool_no_pool(self, db_manager):
        """Test closing pool when no pool exists."""
        await db_manager.close_pool()  # Should not raise exception

    @pytest.mark.asyncio
    async def test_get_connection_success(self, db_manager, mock_pool, mock_connection):
        """Test successful connection acquisition."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection

        async with db_manager.get_connection() as conn:
            assert conn == mock_connection
            mock_pool.acquire.assert_called_once()

        mock_pool.release.assert_called_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_get_connection_auto_initialize(
        self, db_manager, mock_pool, mock_connection
    ):
        """Test connection acquisition with auto pool initialization."""
        mock_pool.acquire.return_value = mock_connection

        with patch("aiomysql.create_pool", return_value=mock_pool):
            async with db_manager.get_connection() as conn:
                assert conn == mock_connection
                assert db_manager.pool == mock_pool

    @pytest.mark.asyncio
    async def test_get_connection_exception_handling(
        self, db_manager, mock_pool, mock_connection
    ):
        """Test connection exception handling."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection

        try:
            async with db_manager.get_connection() as conn:
                raise Exception("Test exception")
        except Exception:
            pass

        mock_pool.release.assert_called_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_execute_query_select_success(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test successful SELECT query execution."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("result1",), ("result2",)]

        result = await db_manager.execute_query("SELECT * FROM test_table", fetch=True)

        assert result == [("result1",), ("result2",)]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table")
        mock_cursor.fetchall.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_with_params(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test query execution with parameters."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        await db_manager.execute_query(
            "INSERT INTO test_table VALUES (%s, %s)",
            params=("value1", "value2"),
            commit=True,
        )

        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO test_table VALUES (%s, %s)", ("value1", "value2")
        )
        mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_retry_logic(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test query execution retry logic on connection errors."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        # First attempt fails, second succeeds
        mock_cursor.execute.side_effect = [
            aiomysql.OperationalError("Connection lost"),
            None,
        ]
        mock_cursor.fetchall.return_value = [("success",)]

        with patch("asyncio.sleep") as mock_sleep:
            result = await db_manager.execute_query(
                "SELECT * FROM test_table", fetch=True, max_retries=2
            )

        assert result == [("success",)]
        assert mock_cursor.execute.call_count == 2
        mock_sleep.assert_called_once_with(2)  # Exponential backoff

    @pytest.mark.asyncio
    async def test_execute_query_max_retries_exceeded(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test query execution when max retries exceeded."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_cursor.execute.side_effect = aiomysql.OperationalError("Connection lost")

        with patch("asyncio.sleep"):
            with pytest.raises(aiomysql.OperationalError):
                await db_manager.execute_query(
                    "SELECT * FROM test_table", max_retries=2
                )

    @pytest.mark.asyncio
    async def test_execute_query_non_retryable_error(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test query execution with non-retryable error."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_cursor.execute.side_effect = ValueError("Invalid query")

        with pytest.raises(ValueError):
            await db_manager.execute_query("INVALID QUERY")

    @pytest.mark.asyncio
    async def test_execute_many_success(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test successful batch execution."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.rowcount = 5

        data = [("value1", "value2"), ("value3", "value4"), ("value5", "value6")]

        result = await db_manager.execute_many(
            "INSERT INTO test_table VALUES (%s, %s)", data, batch_size=2
        )

        assert result == 10  # 2 batches * 5 rows each
        assert mock_cursor.executemany.call_count == 2  # 2 batches
        assert mock_connection.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_many_empty_data(self, db_manager):
        """Test execute_many with empty data."""
        result = await db_manager.execute_many(
            "INSERT INTO test_table VALUES (%s, %s)", []
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_execute_many_retry_logic(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test execute_many retry logic."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.rowcount = 2

        # First batch fails, second succeeds
        mock_cursor.executemany.side_effect = [
            aiomysql.OperationalError("Connection lost"),
            None,
        ]

        data = [("value1", "value2"), ("value3", "value4")]

        with patch("asyncio.sleep"):
            result = await db_manager.execute_many(
                "INSERT INTO test_table VALUES (%s, %s)",
                data,
                batch_size=2,
                max_retries=2,
            )

        assert result == 2
        assert mock_cursor.executemany.call_count == 2

    @pytest.mark.asyncio
    async def test_insert_dataframe_success(self, db_manager):
        """Test successful DataFrame insertion."""
        records = [
            {"id": 1, "name": "test1", "value": 100.0},
            {"id": 2, "name": "test2", "value": 200.0},
        ]

        with patch.object(
            db_manager, "_bulk_load_dataframe", return_value=2
        ) as mock_bulk:
            result = await db_manager.insert_dataframe(
                records, "test_table", replace=True
            )

        assert result == 2
        mock_bulk.assert_called_once()

        # Check DataFrame creation
        call_args = mock_bulk.call_args[0]
        df = call_args[0]
        assert isinstance(df, pl.DataFrame)
        assert len(df) == 2

    @pytest.mark.asyncio
    async def test_insert_dataframe_empty_records(self, db_manager):
        """Test DataFrame insertion with empty records."""
        result = await db_manager.insert_dataframe([], "test_table")
        assert result == 0

    @pytest.mark.asyncio
    async def test_insert_dataframe_with_schema(self, db_manager):
        """Test DataFrame insertion with schema."""
        records = [{"id": 1, "value": "100"}]
        schema = {"id": pl.Int64, "value": pl.Utf8}

        with patch.object(
            db_manager, "_bulk_load_dataframe", return_value=1
        ) as mock_bulk:
            await db_manager.insert_dataframe(records, "test_table", schema=schema)

        call_args = mock_bulk.call_args[0]
        df = call_args[0]
        assert df.schema == schema

    @pytest.mark.asyncio
    async def test_bulk_load_dataframe_success(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test successful bulk load operation."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.rowcount = 2

        df = pl.DataFrame(
            {"id": [1, 2], "name": ["test1", "test2"], "value": [100.0, 200.0]}
        )

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/test.csv"
            mock_temp.return_value.__enter__.return_value = mock_file

            with patch("pathlib.Path.unlink") as mock_unlink:
                result = await db_manager._bulk_load_dataframe(
                    df, "test_table", replace=True
                )

        assert result == 2
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        mock_unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_load_dataframe_empty(self, db_manager):
        """Test bulk load with empty DataFrame."""
        df = pl.DataFrame()

        result = await db_manager._bulk_load_dataframe(df, "test_table")
        assert result == 0

    @pytest.mark.asyncio
    async def test_bulk_load_dataframe_batching(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test bulk load with batching."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.rowcount = 1

        # Create DataFrame with 3 rows, batch size 2
        df = pl.DataFrame({"id": [1, 2, 3], "value": [100, 200, 300]})

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/test.csv"
            mock_temp.return_value.__enter__.return_value = mock_file

            with patch("pathlib.Path.unlink"):
                result = await db_manager._bulk_load_dataframe(
                    df, "test_table", batch_size=2
                )

        assert result == 2  # 2 batches * 1 row each
        assert mock_cursor.execute.call_count == 2
        assert mock_connection.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_get_last_timestamp_success(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test successful last timestamp retrieval."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        test_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        mock_cursor.fetchall.return_value = [(test_timestamp,)]

        result = await db_manager.get_last_timestamp("test_table")

        assert result == test_timestamp.replace(tzinfo=timezone.utc)
        mock_cursor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_last_timestamp_with_filters(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test last timestamp retrieval with filters."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        test_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        mock_cursor.fetchall.return_value = [(test_timestamp,)]

        filters = {"market": "BINANCE", "instrument": "BTC-USD"}

        result = await db_manager.get_last_timestamp(
            "test_table", timestamp_column="created_at", filters=filters
        )

        assert result == test_timestamp.replace(tzinfo=timezone.utc)

        # Check query construction
        call_args = mock_cursor.execute.call_args[0]
        query = call_args[0]
        params = call_args[1]

        assert "MAX(created_at)" in query
        assert "market = %s" in query
        assert "instrument = %s" in query
        assert params == ("BINANCE", "BTC-USD")

    @pytest.mark.asyncio
    async def test_get_last_timestamp_no_result(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test last timestamp retrieval with no results."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [(None,)]

        result = await db_manager.get_last_timestamp("test_table")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_last_timestamp_error(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test last timestamp retrieval error handling."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Database error")

        result = await db_manager.get_last_timestamp("test_table")
        assert result is None

    @pytest.mark.asyncio
    async def test_table_exists_true(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test table existence check - table exists."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [(1,)]

        result = await db_manager.table_exists("test_table")
        assert result is True

    @pytest.mark.asyncio
    async def test_table_exists_false(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test table existence check - table doesn't exist."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [(0,)]

        result = await db_manager.table_exists("test_table")
        assert result is False

    @pytest.mark.asyncio
    async def test_table_exists_with_schema(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test table existence check with schema."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [(1,)]

        result = await db_manager.table_exists("test_schema.test_table")
        assert result is True

        # Check query parameters
        call_args = mock_cursor.execute.call_args[0]
        params = call_args[1]
        assert params == ("test_schema", "test_table")

    @pytest.mark.asyncio
    async def test_get_table_row_count_success(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test successful row count retrieval."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [(100,)]

        result = await db_manager.get_table_row_count("test_table")
        assert result == 100

    @pytest.mark.asyncio
    async def test_get_table_row_count_error(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test row count retrieval error handling."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Database error")

        result = await db_manager.get_table_row_count("test_table")
        assert result == 0

    @pytest.mark.asyncio
    async def test_context_manager_success(self, mock_config, mock_pool):
        """Test async context manager usage."""
        with patch("aiomysql.create_pool", return_value=mock_pool):
            async with AsyncDbConnectionManager(mock_config) as manager:
                assert manager.pool == mock_pool

            mock_pool.close.assert_called_once()
            mock_pool.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_exception(self, mock_config, mock_pool):
        """Test async context manager with exception."""
        with patch("aiomysql.create_pool", return_value=mock_pool):
            try:
                async with AsyncDbConnectionManager(mock_config) as manager:
                    raise Exception("Test exception")
            except Exception:
                pass

            mock_pool.close.assert_called_once()
            mock_pool.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test concurrent database operations."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("result",)]

        # Run multiple concurrent queries
        tasks = [
            db_manager.execute_query(f"SELECT * FROM table_{i}", fetch=True)
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(result == [("result",)] for result in results)
        assert mock_cursor.execute.call_count == 5

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self, db_manager, mock_pool):
        """Test behavior when connection pool is exhausted."""
        db_manager.pool = mock_pool
        mock_pool.acquire.side_effect = asyncio.TimeoutError("Pool exhausted")

        with pytest.raises(asyncio.TimeoutError):
            async with db_manager.get_connection():
                pass

    @pytest.mark.asyncio
    async def test_large_batch_processing(
        self, db_manager, mock_pool, mock_connection, mock_cursor
    ):
        """Test processing of large data batches."""
        db_manager.pool = mock_pool
        mock_pool.acquire.return_value = mock_connection
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.rowcount = 1000

        # Create large dataset
        large_data = [(f"value_{i}", i) for i in range(10000)]

        result = await db_manager.execute_many(
            "INSERT INTO test_table VALUES (%s, %s)", large_data, batch_size=1000
        )

        assert result == 10000  # 10 batches * 1000 rows each
        assert mock_cursor.executemany.call_count == 10
        assert mock_connection.commit.call_count == 10
