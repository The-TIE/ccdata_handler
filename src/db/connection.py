# src/db_connection.py
import singlestoredb as s2
import os
import logging
import tempfile
import polars as pl  # Import polars for type hinting
from typing import Optional, List, Tuple, Any
from dotenv import load_dotenv, find_dotenv, dotenv_values
from pathlib import Path

logger = logging.getLogger(__name__)

# Define the path to the SQL directory relative to this file's parent's parent (project root)
# Go up two levels from src/db/ to the project root, then into sql/
SQL_DIR = Path(__file__).parent.parent.parent / "sql"


_ENV_LOADED = False


def _load_env_if_not_loaded():
    """
    Loads environment variables from .env file if not already loaded.
    This function ensures that dotenv is called only once.
    """
    global _ENV_LOADED
    if not _ENV_LOADED:
        dotenv_path = find_dotenv()
        loaded = load_dotenv(dotenv_path=dotenv_path, override=True)
        logger.info(f".env file loaded: {loaded} from path: {dotenv_path}")
        _ENV_LOADED = True
    else:
        logger.debug(".env file already loaded, skipping.")


class DbConnectionManager:
    """
    Manages the connection to SingleStoreDB and provides basic query execution methods.
    Loads SQL queries from the 'sql/' directory.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """
        Initializes the DbConnectionManager and establishes a database connection.

        Connection parameters are loaded from environment variables by default:
        S2_HOST, S2_PORT, S2_USER, S2_PASSWORD, S2_DATABASE

        Args:
            host (Optional[str]): Database host. Overrides S2_HOST env var.
            port (Optional[int]): Database port. Overrides S2_PORT env var.
            user (Optional[str]): Database user. Overrides S2_USER env var.
            password (Optional[str]): Database password. Overrides S2_PASSWORD env var.
            database (Optional[str]): Database name. Overrides S2_DATABASE env var.

        Raises:
            ValueError: If required connection parameters are missing.
            s2.exceptions.ProgrammingError: If connection fails due to auth/config issues.
            Exception: For other unexpected connection errors.
        """
        _load_env_if_not_loaded()  # Ensure env vars are loaded

        # Log the environment variables *after* trying to load from .env
        s2_user_env = os.getenv("S2_USER")
        s2_host_env = os.getenv("S2_HOST")
        logger.debug(f"S2_USER from env: {s2_user_env}")
        logger.debug(f"S2_HOST from env: {s2_host_env}")

        self.host = host or s2_host_env
        self.port = port or int(os.getenv("S2_PORT", 3306))
        self.user = user or s2_user_env
        self.password = password or os.getenv("S2_PASSWORD")
        self.database = database or os.getenv("S2_DATABASE")

        if not all([self.host, self.user, self.password, self.database]):
            missing = [
                k
                for k, v in {
                    "host": self.host,
                    "user": self.user,
                    "password": "[set]",
                    "database": self.database,
                }.items()
                if not v
            ]
            raise ValueError(
                f"Missing required database connection parameters: {', '.join(missing)}. "
                "Ensure S2_HOST, S2_PORT, S2_USER, S2_PASSWORD, S2_DATABASE are set in .env or passed to constructor."
            )

        self.conn: Optional[s2.connection.Connection] = None
        try:
            logger.info(
                f"Connecting to SingleStoreDB: {self.user}@{self.host}:{self.port}/{self.database}"
            )
            self.conn = s2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                local_infile=True,  # Enable LOAD DATA LOCAL INFILE
                charset="utf8mb4",  # Ensure full Unicode support for emojis etc.
            )
            logger.info("Database connection successful.")

        except s2.exceptions.ProgrammingError as e:
            logger.error(
                f"Database connection failed (check credentials/permissions): {e}"
            )
            raise
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred during database connection: {e}"
            )
            raise

    def close_connection(self):
        """Closes the database connection if it's open."""
        if self.conn:
            try:
                self.conn.close()
                logger.info("Database connection closed.")
            except Exception as e:
                logger.exception(f"Error closing database connection: {e}")
        self.conn = None

    def _reconnect(self, attempt: int = 1, max_attempts: int = 2):
        """Attempts to close the current connection and establish a new one."""
        logger.warning(
            f"Attempting to reconnect to the database (Attempt {attempt}/{max_attempts})..."
        )
        self.close_connection()  # Ensure old connection is closed
        try:
            self.conn = s2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                local_infile=True,
                charset="utf8mb4",
            )
            logger.info("Database re-connection successful.")
            return True  # Indicate success
        except s2.exceptions.ProgrammingError as e:
            logger.error(
                f"Database re-connection failed (check credentials/permissions): {e}"
            )
            # Don't raise immediately, let the caller handle retry logic failure
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred during database re-connection: {e}"
            )
        return False  # Indicate failure

    def _load_sql(self, filename: str) -> str:
        """Loads SQL query from a file in the SQL_DIR."""
        filepath = SQL_DIR / filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                sql_query = f.read()
                logger.debug(f"Loaded SQL from {filepath}")
                return sql_query
        except FileNotFoundError:
            logger.error(f"SQL file not found: {filepath}")
            raise
        except Exception as e:
            logger.exception(f"Error loading SQL file {filepath}: {e}")
            raise

    def _execute_query(
        self,
        query: str,
        params: Optional[Any] = None,
        commit: bool = False,
        fetch: bool = False,
    ) -> Optional[List[Tuple]]:
        """
        Helper method to execute a query with error handling.

        Args:
            query (str): The SQL query string.
            params (Optional[tuple]): Parameters for the query.
            commit (bool): Whether to commit the transaction (for INSERT/UPDATE/DELETE).
            fetch (bool): Whether to fetch results (for SELECT).

        Returns:
            Optional[List[Tuple]]: Results if fetch=True, otherwise None.

        Raises:
            ConnectionError: If the database connection is not available.
            Exception: If any database error occurs.
        """
        max_retries = 2  # Try original + 1 retry
        last_exception = None

        for attempt in range(1, max_retries + 1):
            if not self.conn:
                logger.warning(
                    f"Connection is None on attempt {attempt}. Attempting to establish/re-establish."
                )
                if not self._reconnect(attempt=attempt, max_attempts=max_retries):
                    # If reconnect fails definitively, raise immediately
                    raise ConnectionError(
                        "Failed to establish initial or re-establish database connection."
                    )
                # If reconnect succeeded, self.conn should now be set for the next part of the loop

            results = None
            try:
                with self.conn.cursor() as cur:
                    logger.debug(
                        f"Executing query (Attempt {attempt}): {query[:100]}... | Params: {params}"
                    )
                    if params:
                        cur.execute(query, params)
                    else:
                        cur.execute(query)
                    if fetch:
                        results = cur.fetchall()
                        logger.debug(f"Fetched {len(results)} rows.")
                        return results  # Success, exit loop and return
                    else:
                        # For DML statements (INSERT, UPDATE, DELETE), return rowcount
                        if commit:
                            self.conn.commit()
                            logger.debug("Query committed.")
                        # Return rowcount for DML statements, None for other non-fetching queries
                        return cur.rowcount if cur.rowcount is not None else None
            except s2.exceptions.InterfaceError as e:
                # Specific check for "connection closed" type errors
                # Error code 0 or specific messages might indicate this.
                # Let's be broad for InterfaceError initially.
                logger.warning(
                    f"InterfaceError on attempt {attempt}: {e}. Query: {query[:100]}..."
                )
                last_exception = e
                if attempt < max_retries:
                    logger.info("Attempting reconnect and retry...")
                    if self._reconnect(attempt=attempt, max_attempts=max_retries):
                        continue  # Go to next attempt
                    else:
                        logger.error("Reconnect failed. Aborting retries.")
                        break  # Exit loop if reconnect fails
                else:
                    logger.error("Max retries reached after InterfaceError.")
            except Exception as e:
                # Catch other potential DB errors
                logger.exception(
                    f"Non-InterfaceError executing query (Attempt {attempt}): {query[:100]}... | Error: {e}"
                )
                last_exception = e
                if commit and self.conn:  # Only rollback if conn likely exists
                    try:
                        self.conn.rollback()
                        logger.warning("Query rolled back due to non-InterfaceError.")
                    except Exception as rb_e:
                        logger.exception(f"Error during rollback: {rb_e}")
                raise  # Re-raise immediately for non-InterfaceErrors

            # If we reach here after an InterfaceError and failed reconnect/max retries
            break

        # If loop finished without success, raise the last captured exception
        logger.error(f"Query execution failed after {max_retries} attempts.")
        if last_exception:
            raise last_exception
        else:
            # Should not happen if connection failed initially, but as a fallback
            raise ConnectionError(
                "Query execution failed, unknown reason after retries."
            )

    def _execute_many(self, query: str, data_tuples: List[Tuple[Any, ...]]) -> int:
        """
        Helper method to execute a query with executemany for batching.

        Returns:
            int: The number of affected rows (or best estimate).
        """
        max_retries = 2
        last_exception = None

        if not data_tuples:
            logger.info("No data provided to _execute_many.")
            return 0

        for attempt in range(1, max_retries + 1):
            if not self.conn:
                logger.warning(
                    f"_execute_many: Connection is None on attempt {attempt}. Attempting reconnect."
                )
                if not self._reconnect(attempt=attempt, max_attempts=max_retries):
                    raise ConnectionError(
                        "Failed to establish/re-establish database connection for _execute_many."
                    )

            try:
                with self.conn.cursor() as cur:
                    logger.debug(
                        f"Executing many query (Attempt {attempt}): {query[:100]}... | Batch size: {len(data_tuples)}"
                    )
                    rowcount = cur.executemany(query, data_tuples)
                    self.conn.commit()
                    affected_rows = (
                        rowcount if rowcount is not None else len(data_tuples)
                    )
                    logger.debug(
                        f"Query committed. Affected rows (approx): {affected_rows}"
                    )
                    return affected_rows  # Success
            except s2.exceptions.InterfaceError as e:
                logger.warning(
                    f"InterfaceError on attempt {attempt} in _execute_many: {e}. Query: {query[:100]}..."
                )
                last_exception = e
                if attempt < max_retries:
                    logger.info("Attempting reconnect and retry for _execute_many...")
                    if self._reconnect(attempt=attempt, max_attempts=max_retries):
                        continue
                    else:
                        logger.error(
                            "Reconnect failed. Aborting retries for _execute_many."
                        )
                        break
                else:
                    logger.error(
                        "Max retries reached after InterfaceError in _execute_many."
                    )
            except Exception as e:
                logger.exception(
                    f"Non-InterfaceError executing many query (Attempt {attempt}): {query[:100]}... | Error: {e}"
                )
                last_exception = e
                if self.conn:
                    try:
                        self.conn.rollback()
                        logger.warning(
                            "Batch query rolled back due to non-InterfaceError."
                        )
                    except Exception as rb_e:
                        logger.exception(f"Error during rollback: {rb_e}")
                raise  # Re-raise non-InterfaceErrors immediately

            break  # Exit loop if InterfaceError and failed reconnect/max retries

        logger.error(f"_execute_many failed after {max_retries} attempts.")
        if last_exception:
            raise last_exception
        else:
            raise ConnectionError("_execute_many failed, unknown reason after retries.")

    def insert_dataframe(
        self, records: List[dict], table_name: str, replace: bool = False
    ) -> int:
        """
        Inserts a list of dictionaries (records) into the specified table.
        Automatically converts records to a Polars DataFrame and uses bulk load.

        Args:
            records (List[dict]): A list of dictionaries, where each dictionary
                                  represents a row and keys are column names.
            table_name (str): The fully qualified name of the target table.
            replace (bool): If True, use REPLACE INTO (or LOAD DATA ... REPLACE)
                            to update existing rows based on primary/unique keys.

        Returns:
            int: The number of rows affected.
        """
        if not records:
            logger.info(f"No records provided for insertion into {table_name}.")
            return 0

        # Infer columns from the first record, assuming all records have the same keys
        columns = list(records[0].keys())
        df = pl.DataFrame(records)

        logger.info(
            f"Inserting {len(records)} records into {table_name} using bulk load (replace={replace})."
        )
        return self._bulk_load_from_dataframe(df, table_name, columns, replace)

    def _bulk_load_from_dataframe(
        self,
        df: pl.DataFrame,
        table_name: str,
        columns: List[str],
        replace: bool = False,
    ) -> int:
        """
        Bulk loads data from a Polars DataFrame into a specified table
        using LOAD DATA LOCAL INFILE.

        Args:
            df (pl.DataFrame): The Polars DataFrame containing the data.
            table_name (str): The fully qualified name of the target table (e.g., 'social_media.twitter_account_stats').
            columns (List[str]): The list of column names in the DataFrame corresponding
                                 to the columns in the target table, in order.
            replace (bool): If True, use REPLACE keyword with LOAD DATA to update existing rows.

        Returns:
            int: The number of rows affected (as reported by LOAD DATA).

        Raises:
            ConnectionError: If the database connection is not available.
            Exception: If any error occurs during file writing or DB loading.
        """
        if not self.conn:
            logger.error("Database connection is not available for bulk load.")
            raise ConnectionError("Database connection is not initialized.")
        if df.is_empty():
            logger.info(f"DataFrame is empty, skipping bulk load to {table_name}.")
            return 0

        # Ensure DataFrame columns match the provided list and order
        df_ordered = df.select(columns)

        # Create a temporary file to store the CSV data in binary mode
        # Use delete=False initially to ensure the file persists until LOAD DATA is done
        tmp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False)
        csv_path = tmp_file.name
        try:
            logger.debug(
                f"Writing DataFrame to temporary CSV for bulk load: {csv_path}"
            )

            # Write DataFrame to CSV using the file path
            # Polars handles opening/closing when given a path.
            # Ensure standard CSV format (comma separated, double quotes for strings)
            df_ordered.write_csv(
                csv_path, include_header=False, separator=",", quote_char='"'
            )
            # tmp_file.close() # No need to close manually when writing via path

            # Determine if REPLACE keyword should be used
            replace_keyword = "REPLACE" if replace else ""

            # Construct the LOAD DATA LOCAL INFILE query
            # Ensure correct quoting and escaping for the LOAD DATA statement
            # Use standard CSV options matching write_csv defaults
            cols_str = ", ".join([f"`{col}`" for col in columns])  # Quote column names
            # Escape backslashes in the path for the SQL string literal
            escaped_csv_path = csv_path.replace("\\", "\\\\")
            load_sql = f"""
                LOAD DATA LOCAL INFILE '{escaped_csv_path}'
                {replace_keyword} INTO TABLE {table_name}
                FIELDS TERMINATED BY ',' ENCLOSED BY '"'
                LINES TERMINATED BY '\\n' -- Use \\n for Linux/macOS, \\r\\n for Windows if needed
                ({cols_str});
            """
            logger.debug(
                f"Executing LOAD DATA command for {table_name} from {csv_path}"
            )

            # Retry logic for the LOAD DATA execution itself
            max_retries = 2
            last_exception = None
            for attempt in range(1, max_retries + 1):
                if not self.conn:
                    logger.warning(
                        f"_bulk_load: Connection is None on attempt {attempt}. Attempting reconnect."
                    )
                    if not self._reconnect(attempt=attempt, max_attempts=max_retries):
                        raise ConnectionError(
                            "Failed to establish/re-establish database connection for _bulk_load."
                        )

                try:
                    with self.conn.cursor() as cur:
                        logger.debug(
                            f"Executing LOAD DATA (Attempt {attempt}) for {table_name} from {csv_path}"
                        )
                        affected_rows = cur.execute(load_sql)
                        self.conn.commit()
                        logger.info(
                            f"LOAD DATA LOCAL INFILE for {table_name} completed. Affected rows: {affected_rows}"
                        )
                        # Note: affected_rows from LOAD DATA might represent rows processed, not just inserted.
                        return (
                            affected_rows if affected_rows is not None else 0
                        )  # Success
                except s2.exceptions.InterfaceError as e:
                    logger.warning(
                        f"InterfaceError on attempt {attempt} during LOAD DATA for {table_name}: {e}"
                    )
                    last_exception = e
                    if attempt < max_retries:
                        logger.info("Attempting reconnect and retry for LOAD DATA...")
                        if self._reconnect(attempt=attempt, max_attempts=max_retries):
                            continue
                        else:
                            logger.error(
                                "Reconnect failed. Aborting retries for LOAD DATA."
                            )
                            break
                    else:
                        logger.error(
                            "Max retries reached after InterfaceError during LOAD DATA."
                        )
                except Exception as e:
                    logger.exception(
                        f"Non-InterfaceError during LOAD DATA (Attempt {attempt}) for table {table_name} from {csv_path}: {e}"
                    )
                    last_exception = e
                    if self.conn:
                        try:
                            self.conn.rollback()
                            logger.warning(
                                "LOAD DATA transaction rolled back due to non-InterfaceError."
                            )
                        except Exception as rb_e:
                            logger.exception(f"Error during LOAD DATA rollback: {rb_e}")
                    raise  # Re-raise non-InterfaceErrors immediately

                break  # Exit loop if InterfaceError and failed reconnect/max retries

            logger.error(
                f"LOAD DATA failed after {max_retries} attempts for table {table_name}."
            )
            if last_exception:
                raise last_exception
            else:
                raise ConnectionError("LOAD DATA failed, unknown reason after retries.")
        finally:
            # Clean up the temporary file manually since delete=False
            if "csv_path" in locals() and os.path.exists(csv_path):
                try:
                    os.remove(csv_path)
                    logger.debug(f"Removed temporary CSV file: {csv_path}")
                except OSError as unlink_e:
                    logger.error(
                        f"Error removing temporary CSV file {csv_path}: {unlink_e}"
                    )

    def __enter__(self):
        """Enter context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, ensuring connection closure"""
        self.close_connection()
