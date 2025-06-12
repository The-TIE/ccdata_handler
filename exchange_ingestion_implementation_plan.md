# Revised Plan (Iteration 5 - Final): Focused Exchange Data Ingestion with Refined Tables

**Core Principles:**
1.  **Separate Tables per Source/Entity:**
    *   `market.cc_exchanges_general`
    *   `market.cc_exchange_spot_details`
    *   `market.cc_instruments_spot`
2.  **No Raw JSON (where practical).**
3.  **Single Spot API Endpoint:** `/spot/v1/markets/instruments`.

---

**Phase 1: Database Schema Design**
*   **Objective:** Define the `market.cc_exchanges_general`, `market.cc_exchange_spot_details`, and `market.cc_instruments_spot` tables with refined column names and types.
*   **Note on SingleStore Keys:** Logical keys guide `SHARD KEY` and `SORT KEY` selection.

*   **Task 1.1: `market.cc_exchanges_general` Table Structure**
    *   Source: `/data/exchanges/general` endpoint.
    *   Logical Primary Key: `exchange_api_id` (VARCHAR).
    *   Logical Unique Key: `internal_name` (VARCHAR).
    *   **Columns:**
        *   `exchange_api_id` (VARCHAR, PK)
        *   `name` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci)
        *   `internal_name` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, UNIQUE)
        *   `api_url_path` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci)
        *   `logo_url_path` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci)
        *   `item_types` (JSON)
        *   `centralization_type` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci)
        *   `grade_points` (DOUBLE)
        *   `grade` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci)
        *   `grade_points_legal` (DOUBLE)
        *   `grade_points_kyc_risk` (DOUBLE)
        *   `grade_points_team` (DOUBLE)
        *   `grade_points_data_provision` (DOUBLE)
        *   `grade_points_asset_quality` (DOUBLE)
        *   `grade_points_market_quality` (DOUBLE)
        *   `grade_points_security` (DOUBLE)
        *   `grade_points_neg_reports_penalty` (DOUBLE)
        *   `affiliate_url` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci)
        *   `country` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci)
        *   `has_orderbook` (BOOLEAN)
        *   `has_trades` (BOOLEAN)
        *   `description` (TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci)
        *   `full_address` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci)
        *   `is_sponsored` (BOOLEAN)
        *   `is_recommended` (BOOLEAN)
        *   `rating_avg` (DOUBLE)
        *   `rating_total_users` (INT)
        *   `sort_order` (INT)
        *   `total_volume_24h_usd` (DOUBLE)
        *   `created_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)
        *   `updated_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)
    *   Suggested SHARD KEY: `internal_name`.
    *   Suggested SORT KEY: `internal_name`, `name`.

*   **Task 1.2: `market.cc_exchange_spot_details` Table Structure (Refined)**
    *   Source: Exchange-level data from `/spot/v1/markets/instruments` response.
    *   Logical Primary Key: `exchange_internal_name` (VARCHAR).
    *   Logical Foreign Key: `exchange_internal_name` references `market.cc_exchanges_general.internal_name`.
    *   **Columns (Refined):**
        *   `exchange_internal_name` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, PK, FK)
        *   `api_exchange_type` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, from `TYPE` field)
        *   `exchange_status` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, from `EXCHANGE_STATUS`)
        *   `mapped_instruments_total` (INT, from `MAPPED_INSTRUMENTS_TOTAL`)
        *   `unmapped_instruments_total` (INT, from `UNMAPPED_INSTRUMENTS_TOTAL`)
        *   `instruments_active_count` (INT, from `INSTRUMENT_STATUS.ACTIVE`)
        *   `instruments_ignored_count` (INT, from `INSTRUMENT_STATUS.IGNORED`)
        *   `instruments_retired_count` (INT, from `INSTRUMENT_STATUS.RETIRED`)
        *   `instruments_expired_count` (INT, from `INSTRUMENT_STATUS.EXPIRED`)
        *   `instruments_retired_unmapped_count` (INT, from `INSTRUMENT_STATUS.RETIRED_UNMAPPED`)
        *   `total_trades_exchange_level` (BIGINT, from `TOTAL_TRADES_SPOT` at exchange level)
        *   `has_orderbook_l2_snapshots` (BOOLEAN, from `HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED`)
        *   `api_data_retrieved_datetime` (DATETIME, ingestion script sets this to mark data freshness from API call)
        *   `created_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)
        *   `updated_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)
    *   Suggested SHARD KEY: `exchange_internal_name`.
    *   Suggested SORT KEY: `exchange_internal_name`.

*   **Task 1.3: `market.cc_instruments_spot` Table Structure (Refined)**
    *   Source: Instrument-level data from `/spot/v1/markets/instruments` response.
    *   Logical Primary Key: Composite (`exchange_internal_name`, `mapped_instrument_symbol`).
    *   Logical Foreign Keys: `exchange_internal_name` -> `market.cc_exchange_spot_details`; `base_asset_id`, `quote_asset_id` -> `market.cc_assets`.
    *   **Columns (Refined):**
        *   `exchange_internal_name` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, Part of PK, FK)
        *   `mapped_instrument_symbol` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, Part of PK)
        *   `api_instrument_type` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, from `TYPE` field)
        *   `instrument_status_on_exchange` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, from `INSTRUMENT_STATUS`)
        *   `exchange_instrument_symbol_raw` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, from `INSTRUMENT`)
        *   `base_asset_symbol` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, from `INSTRUMENT_MAPPING.BASE`)
        *   `base_asset_id` (BIGINT, from `INSTRUMENT_MAPPING.BASE_ID`)
        *   `quote_asset_symbol` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, from `INSTRUMENT_MAPPING.QUOTE`)
        *   `quote_asset_id` (BIGINT, from `INSTRUMENT_MAPPING.QUOTE_ID`)
        *   `transform_function` (VARCHAR CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, from `INSTRUMENT_MAPPING.TRANSFORM_FUNCTION`)
        *   `instrument_mapping_created_datetime` (DATETIME, converted from `INSTRUMENT_MAPPING.CREATED_ON`)
        *   `has_trades` (BOOLEAN, from `HAS_TRADES_SPOT`)
        *   `first_trade_datetime` (DATETIME, converted from `FIRST_TRADE_SPOT_TIMESTAMP`)
        *   `last_trade_datetime` (DATETIME, converted from `LAST_TRADE_SPOT_TIMESTAMP`)
        *   `total_trades_instrument_level` (BIGINT, from `TOTAL_TRADES_SPOT` at instrument level)
        *   `created_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)
        *   `updated_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)
    *   Suggested SHARD KEY: `exchange_internal_name`, `mapped_instrument_symbol`.
    *   Suggested SORT KEY: `exchange_internal_name`, `mapped_instrument_symbol`, `last_trade_datetime DESC`.

*   **Task 1.4: Update [`sql/create_schema.sql`](sql/create_schema.sql)**
    *   Add/Update `CREATE TABLE` statements for the three tables with refined columns and types. Ensure `CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` for all relevant string columns.

*   **Task 1.5: Update [`database_schema.md`](database_schema.md)**
    *   Add/Update markdown table definitions.

---

**Phase 2: API Client Enhancements**
*   **Task 2.1: Review [`src/min_api/general_info_api_client.py`](src/min_api/general_info_api_client.py)**
*   **Task 2.2: Enhance [`src/data_api/spot_api_client.py`](src/data_api/spot_api_client.py)** (Implement `get_spot_market_instruments`)

---

**Phase 3: Ingestion Script Development**
*   **Task 3.1: Create `scripts/ingest_exchanges_general.py`**
    *   Maps to `market.cc_exchanges_general` columns.

*   **Task 3.2: Create `scripts/ingest_spot_exchange_instrument_data.py`**
    *   Parses `/spot/v1/markets/instruments` response.
    *   Populates `market.cc_exchange_spot_details` (with refined columns, setting `api_data_retrieved_datetime`).
    *   Populates `market.cc_instruments_spot` (with refined columns, converting Unix timestamps from API to DATETIME for `instrument_mapping_created_datetime`, `first_trade_datetime`, `last_trade_datetime`).

---

**Phase 4: Scheduling**
*   **Task 4.1: `scheduling/ingest_exchanges_general.sh`**
*   **Task 4.2: `scheduling/ingest_spot_exchange_instrument_data.sh`**

---

**Phase 5: Testing and Validation**