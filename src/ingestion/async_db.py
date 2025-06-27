"""
Async database operations module for the unified data ingestion pipeline.

This module provides async database operations with connection pooling,
retry logic, and proper error handling for high-performance data ingestion.
"""

import asyncio
import logging
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from pathlib import Path

import polars as pl
import aiomysql
from aiomysql import Pool

from ..logger_config import setup_logger
from ..rate_limit_tracker import record_rate_limit_status
from .config import get_database_config


logger = setup_logger(__name__)


class AsyncDbConnectionManager:
    """
    Async database connection manager with connection pooling.

    Provides high-performance async database operations for the ingestion
    pipeline with automatic connection pooling, retry logic, and proper
    resource management.
    """

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize the async database connection manager.

        Args:
            config: Database configuration object (uses global config if None)
        """
        self.config = config or get_database_config()
        self.pool: Optional[Pool] = None
        self._pool_lock = asyncio.Lock()

    async def initialize_pool(self) -> None:
        """
        Initialize the connection pool.

        This method should be called before using any database operations.
        """
        async with self._pool_lock:
            if self.pool is not None:
                logger.debug("Connection pool already initialized")
                return

            try:
                logger.info(
                    f"Initializing async database connection pool: "
                    f"{self.config.user}@{self.config.host}:{self.config.port}/{self.config.database}"
                )

                self.pool = await aiomysql.create_pool(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.user,
                    password=self.config.password,
                    db=self.config.database,
                    charset="utf8mb4",
                    minsize=1,
                    maxsize=self.config.pool_size,
                    pool_recycle=self.config.pool_recycle,
                    autocommit=False,
                    local_infile=True,
                )

                logger.info("Async database connection pool initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize database connection pool: {e}")
                raise

    async def close_pool(self) -> None:
        """Close the connection pool and all connections."""
        async with self._pool_lock:
            if self.pool is not None:
                self.pool.close()
                await self.pool.wait_closed()
                self.pool = None
                logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiomysql.Connection, None]:
        """
        Get a database connection from the pool.

        Returns:
            Async context manager yielding a database connection
        """
        if self.pool is None:
            await self.initialize_pool()

        connection = None
        try:
            connection = await self.pool.acquire()
            yield connection
        finally:
            if connection is not None:
                await self.pool.release(connection)

    async def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: bool = False,
        commit: bool = False,
        max_retries: int = 3,
    ) -> Optional[List[Tuple]]:
        """
        Execute a SQL query with retry logic.

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results
            commit: Whether to commit the transaction
            max_retries: Maximum number of retry attempts

        Returns:
            Query results if fetch=True, otherwise None

        Raises:
            Exception: If query execution fails after all retries
        """
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                async with self.get_connection() as conn:
                    async with conn.cursor() as cursor:
                        logger.debug(
                            f"Executing query (attempt {attempt}): {query[:100]}... | Params: {params}"
                        )

                        if params:
                            await cursor.execute(query, params)
                        else:
                            await cursor.execute(query)

                        if fetch:
                            results = await cursor.fetchall()
                            logger.debug(f"Fetched {len(results)} rows")
                            return results
                        else:
                            if commit:
                                await conn.commit()
                                logger.debug("Query committed")
                            return cursor.rowcount

            except (aiomysql.OperationalError, aiomysql.InterfaceError) as e:
                logger.warning(f"Database connection error on attempt {attempt}: {e}")
                last_exception = e
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                    continue
                else:
                    break

            except Exception as e:
                logger.error(f"Database query error: {e}")
                last_exception = e
                break

        logger.error(f"Query execution failed after {max_retries} attempts")
        if last_exception:
            raise last_exception
        else:
            raise Exception("Query execution failed for unknown reason")

    async def execute_many(
        self,
        query: str,
        data: List[Tuple],
        batch_size: int = 1000,
        max_retries: int = 3,
    ) -> int:
        """
        Execute a query with multiple parameter sets in batches.

        Args:
            query: SQL query string
            data: List of parameter tuples
            batch_size: Number of records per batch
            max_retries: Maximum number of retry attempts

        Returns:
            Total number of affected rows

        Raises:
            Exception: If execution fails after all retries
        """
        if not data:
            logger.info("No data provided to execute_many")
            return 0

        total_affected = 0

        # Process data in batches
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    async with self.get_connection() as conn:
                        async with conn.cursor() as cursor:
                            logger.debug(
                                f"Executing batch {i//batch_size + 1} "
                                f"(attempt {attempt}): {len(batch)} records"
                            )

                            await cursor.executemany(query, batch)
                            await conn.commit()

                            affected = cursor.rowcount or len(batch)
                            total_affected += affected
                            logger.debug(f"Batch committed, affected rows: {affected}")
                            break

                except (aiomysql.OperationalError, aiomysql.InterfaceError) as e:
                    logger.warning(
                        f"Database connection error on batch {i//batch_size + 1}, "
                        f"attempt {attempt}: {e}"
                    )
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(2**attempt)
                        continue
                    else:
                        raise

                except Exception as e:
                    logger.error(f"Database batch execution error: {e}")
                    raise

        return total_affected

    async def insert_dataframe(
        self,
        records: List[Dict[str, Any]],
        table_name: str,
        replace: bool = False,
        schema: Optional[Dict[str, Any]] = None,
        batch_size: int = 10000,
    ) -> int:
        """
        Insert a list of records into a table using bulk load operations.

        Args:
            records: List of record dictionaries
            table_name: Target table name
            replace: Whether to use REPLACE INTO semantics
            schema: Optional Polars schema for the DataFrame
            batch_size: Number of records per batch

        Returns:
            Number of records inserted

        Raises:
            Exception: If insertion fails
        """
        if not records:
            logger.info(f"No records provided for insertion into {table_name}")
            return 0

        try:
            # Create DataFrame with optional schema
            if schema:
                df = pl.DataFrame(records, schema=schema)
            else:
                df = pl.DataFrame(records)

            logger.info(
                f"Inserting {len(records)} records into {table_name} "
                f"using async bulk load (replace={replace})"
            )

            return await self._bulk_load_dataframe(
                df, table_name, replace=replace, batch_size=batch_size
            )

        except Exception as e:
            logger.error(f"Error inserting DataFrame into {table_name}: {e}")
            record_rate_limit_status("async_db_insert", "failure")
            raise

    async def _bulk_load_dataframe(
        self,
        df: pl.DataFrame,
        table_name: str,
        replace: bool = False,
        batch_size: int = 10000,
    ) -> int:
        """
        Bulk load a Polars DataFrame using LOAD DATA LOCAL INFILE.

        Args:
            df: Polars DataFrame to load
            table_name: Target table name
            replace: Whether to use REPLACE semantics
            batch_size: Number of records per batch

        Returns:
            Number of records loaded

        Raises:
            Exception: If bulk load fails
        """
        if df.is_empty():
            logger.info(f"DataFrame is empty, skipping bulk load to {table_name}")
            return 0

        total_loaded = 0
        columns = df.columns

        # Process DataFrame in batches
        for i in range(0, len(df), batch_size):
            batch_df = df.slice(i, batch_size)

            # Create temporary CSV file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False, encoding="utf-8"
            ) as tmp_file:
                csv_path = tmp_file.name

            try:
                # Write batch to CSV
                batch_df.write_csv(
                    csv_path, include_header=False, separator=",", quote_char='"'
                )

                # Execute LOAD DATA command
                replace_keyword = "REPLACE" if replace else ""
                cols_str = ", ".join([f"`{col}`" for col in columns])

                load_sql = f"""
                    LOAD DATA LOCAL INFILE '{csv_path}'
                    {replace_keyword} INTO TABLE {table_name}
                    FIELDS TERMINATED BY ',' ENCLOSED BY '"'
                    LINES TERMINATED BY '\\n'
                    ({cols_str})
                """

                async with self.get_connection() as conn:
                    async with conn.cursor() as cursor:
                        logger.debug(
                            f"Executing LOAD DATA for batch {i//batch_size + 1} "
                            f"of {table_name}"
                        )

                        await cursor.execute(load_sql)
                        await conn.commit()

                        affected = cursor.rowcount or len(batch_df)
                        total_loaded += affected

                        logger.debug(
                            f"Batch {i//batch_size + 1} loaded: {affected} records"
                        )

            finally:
                # Clean up temporary file
                try:
                    Path(csv_path).unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {csv_path}: {e}")

        logger.info(
            f"Successfully bulk loaded {total_loaded} records into {table_name}"
        )
        record_rate_limit_status("async_db_insert", "success")
        return total_loaded

    async def get_last_timestamp(
        self,
        table_name: str,
        timestamp_column: str = "datetime",
        filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[datetime]:
        """
        Get the latest timestamp from a table.

        Args:
            table_name: Name of the table to query
            timestamp_column: Name of the timestamp column
            filters: Optional filters to apply

        Returns:
            Latest timestamp or None if no records found
        """
        try:
            where_conditions = []
            params = []

            if filters:
                for key, value in filters.items():
                    where_conditions.append(f"{key} = %s")
                    params.append(value)

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = f"""
                SELECT MAX({timestamp_column})
                FROM {table_name}
                WHERE {where_clause}
            """

            result = await self.execute_query(
                query, params=tuple(params) if params else None, fetch=True
            )

            if result and result[0] and result[0][0]:
                timestamp = result[0][0]
                if hasattr(timestamp, "replace"):
                    return timestamp.replace(tzinfo=timezone.utc)
                return timestamp

            return None

        except Exception as e:
            logger.error(f"Error getting last timestamp from {table_name}: {e}")
            return None

    async def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        try:
            # Split schema and table name if provided
            if "." in table_name:
                schema, table = table_name.split(".", 1)
                query = """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                """
                params = (schema, table)
            else:
                query = """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_name = %s
                """
                params = (table_name,)

            result = await self.execute_query(query, params=params, fetch=True)
            return result and result[0] and result[0][0] > 0

        except Exception as e:
            logger.error(f"Error checking if table {table_name} exists: {e}")
            return False

    async def get_table_row_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows in the table
        """
        try:
            query = f"SELECT COUNT(*) FROM {table_name}"
            result = await self.execute_query(query, fetch=True)
            return result[0][0] if result and result[0] else 0

        except Exception as e:
            logger.error(f"Error getting row count for {table_name}: {e}")
            return 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_pool()


# Alias for backward compatibility and test expectations
AsyncDatabaseManager = AsyncDbConnectionManager


# Convenience functions for common operations
async def create_async_db_manager(
    config: Optional[Any] = None,
) -> AsyncDbConnectionManager:
    """
    Create and initialize an async database manager.

    Args:
        config: Optional database configuration

    Returns:
        Initialized AsyncDbConnectionManager instance
    """
    manager = AsyncDbConnectionManager(config)
    await manager.initialize_pool()
    return manager


async def insert_records_async(
    records: List[Dict[str, Any]],
    table_name: str,
    replace: bool = False,
    schema: Optional[Dict[str, Any]] = None,
    config: Optional[Any] = None,
) -> int:
    """
    Convenience function to insert records asynchronously.

    Args:
        records: List of record dictionaries
        table_name: Target table name
        replace: Whether to use REPLACE semantics
        schema: Optional Polars schema
        config: Optional database configuration

    Returns:
        Number of records inserted
    """
    async with AsyncDbConnectionManager(config) as db_manager:
        return await db_manager.insert_dataframe(
            records, table_name, replace=replace, schema=schema
        )


async def get_last_ingested_timestamp_async(
    table_name: str,
    timestamp_column: str = "datetime",
    filters: Optional[Dict[str, Any]] = None,
    config: Optional[Any] = None,
) -> Optional[datetime]:
    """
    Convenience function to get the last ingested timestamp.

    Args:
        table_name: Name of the table to query
        timestamp_column: Name of the timestamp column
        filters: Optional filters to apply
        config: Optional database configuration

    Returns:
        Latest timestamp or None if no records found
    """
    async with AsyncDbConnectionManager(config) as db_manager:
        return await db_manager.get_last_timestamp(
            table_name, timestamp_column, filters
        )
