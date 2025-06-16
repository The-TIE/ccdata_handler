# Spot Data Ingestion Changes Plan

This document outlines the plan to modify the spot data ingestion process, including schema changes, updating ingestion logic to use database lookups, addressing data duplication, and updating version control tracking.

## Objectives

1.  Use `DATETIME` instead of `BIGINT` for all timestamp columns in the `market.cc_ohlcv_spot_1d_raw` table, including migrating existing data.
2.  Reference asset and exchange tables in the database instead of calling the API to get relevant exchanges and pairs for ingestion.
3.  Investigate and handle the retrieval and storage of duplicate data, using the `db.utils` deduplication function if necessary.
4.  Remove `egg-info` files from version control tracking.

## Detailed Plan

1.  **Schema Modification and Data Migration:**
    *   Create a new temporary table with the same structure as `market.cc_ohlcv_spot_1d_raw`, but with the `first_trade_timestamp`, `last_trade_timestamp`, `high_trade_timestamp`, and `low_trade_timestamp` columns defined as `DATETIME`.
    *   Write a script to read data from the original `market.cc_ohlcv_spot_1d_raw` table, convert the `BIGINT` timestamp values in the specified columns to `DATETIME` objects, and insert the converted data into the new temporary table.
    *   Drop the original `market.cc_ohlcv_spot_1d_raw` table.
    *   Rename the temporary table to `market.cc_ohlcv_spot_1d_raw`.
    *   Update the [`database_schema.md`](database_schema.md) file to reflect the final schema with `DATETIME` columns for the timestamp fields.

2.  **Update Ingestion Scripts (Use Database for Exchanges/Pairs):**
    *   Modify the [`scripts/ingest_ohlcv_spot_1d_top_pairs.py`](scripts/ingest_ohlcv_spot_1d_top_pairs.py) script:
        *   Remove the existing functions `get_qualified_exchanges` and `get_trading_pairs_for_assets_on_exchanges` which currently fetch data from the API.
        *   Implement new functions that query the database tables (`market.cc_exchanges_general`, `market.cc_instruments_spot`, and `market.cc_assets`) to retrieve the list of qualified exchanges and trading pairs based on the criteria (e.g., exchange rating 'BB' or better, top assets by volume).
        *   Update the `main` function to call these new database query functions to get the list of exchanges and pairs to process.
    *   Review [`scripts/ingest_daily_ohlcv_spot_data.py`](scripts/ingest_daily_ohlcv_spot_data.py) to confirm it takes market and instrument as arguments and does not fetch lists of exchanges/pairs from the API internally.

    *Conceptual Data Flow Change:*
    ```mermaid
    graph TD
        A[Old: API Calls for Exchanges/Pairs] --> B{scripts/ingest_ohlcv_spot_1d_top_pairs.py}
        C[New: Database Tables<br/>market.cc_exchanges_general<br/>market.cc_instruments_spot<br/>market.cc_assets] --> B
        B --> D[Fetch OHLCV Data from API]
        D --> E[Process Data]
        E --> F[Insert into market.cc_ohlcv_spot_1d_raw]
    ```

3.  **Investigate and Handle Data Duplication:**
    *   Investigate the root cause of data duplication during the ingestion process. Analyze how data is fetched, processed, and inserted into `market.cc_ohlcv_spot_1d_raw` to identify potential sources of duplicates, considering the primary key (`datetime`, `exchange`, `symbol`) and the use of `replace=True` in `db.insert_dataframe`.
    *   Utilize the existing `db.utils.deduplicate_table` function as a cleanup mechanism to remove existing duplicates from the `market.cc_ohlcv_spot_1d_raw` table. The recommended key columns for deduplication are `datetime`, `exchange`, and `symbol_unmapped`, using `collected_at` as the column to determine the latest record. This deduplication process can be run periodically as a maintenance task.

4.  **Update `.gitignore`:**
    *   Add a new line to the `.gitignore` file to ignore the `src/*.egg-info/` directory and its contents, preventing these build artifacts from being tracked in version control.