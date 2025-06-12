import json
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def get_table_columns(db_manager, table):
    """Return a list of column names for the given table, excluding 'rn'."""
    sql = f"SHOW COLUMNS FROM {table}"
    cols = db_manager._execute_query(sql, fetch=True)
    return [row[0] for row in cols if row[0] != "rn"]


def to_mysql_datetime(val):
    """Convert various datetime/timestamp types to MySQL DATETIME string."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    if isinstance(val, str):
        # Try parsing common formats
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(val, fmt).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
        # If already in correct format, return as is
        if len(val) >= 19 and val[4] == "-" and val[13] == ":":
            return val[:19]
    raise ValueError(f"Cannot convert {val!r} to MySQL DATETIME")


def deduplicate_table(db_manager, table, key_cols, latest_col):
    """
    Deduplicate a SingleStore columnstore table, keeping only the latest row per key.
    Args:
        db_manager: database connection manager
        table (str): fully qualified table name (e.g., market.cc_assets)
        key_cols (list of str): columns to use as the unique key
        latest_col (str): column to use for "latest" (e.g., updated_at)
    """
    logger.info(f"Deduplicating {table} on keys {key_cols} by {latest_col}...")
    partition_by = ", ".join(key_cols)
    select_columns = get_table_columns(db_manager, table)
    select_cols = ", ".join(select_columns)
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table}_deduped AS
    SELECT {select_cols}
    FROM (
      SELECT {select_cols},
             ROW_NUMBER() OVER (PARTITION BY {partition_by} ORDER BY {latest_col} DESC) AS rn
      FROM {table}
    ) t
    WHERE rn = 1
    """
    drop_sql = f"DROP TABLE {table};"
    alter_sql = f"ALTER TABLE {table}_deduped RENAME TO {table.split('.')[-1]};"
    try:
        db_manager._execute_query(create_sql, commit=True)
        db_manager._execute_query(drop_sql, commit=True)
        db_manager._execute_query(alter_sql, commit=True)
        logger.info(f"Deduplication of {table} completed successfully.")
    except Exception as e:
        logger.error(f"Deduplication of {table} failed: {e}")
