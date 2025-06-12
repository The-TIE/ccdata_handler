# Plan: Ingesting and Storing Instrument & Exchange Mappings

This document outlines the plan for setting up processes to ingest and store mappings for financial instruments and exchanges, primarily using CryptoCompare APIs.

## Phase 1: Database Schema Design

The proposed database schema consists of several tables, designed to normalize data from the APIs and avoid storing structured information in JSON blobs where feasible. All table names will be prepended with `market.cc_`.

**Note on Character Sets:** All `VARCHAR` and `TEXT` columns in SingleStore should explicitly use `CHARACTER SET utf8mb4` (and an appropriate collation like `COLLATE utf8mb4_unicode_ci` or `utf8mb4_general_ci`) to ensure full Unicode support, including emojis and special symbols. This is a specific requirement for DDL generation.

### Core Tables:

1.  **`market.cc_assets` Table:** Stores general information about each unique asset.
2.  **`market.cc_asset_alternative_ids` Table:** Stores various alternative IDs for assets.
3.  **`market.cc_asset_industries_map` Table:** Maps assets to their industries.
4.  **`market.cc_asset_consensus_mechanisms_map` Table:** Maps assets to their consensus mechanisms.
5.  **`market.cc_asset_consensus_algorithm_types_map` Table:** Maps assets to their consensus algorithm types.
6.  **`market.cc_asset_hashing_algorithm_types_map` Table:** Maps assets to their hashing algorithm types.
7.  **`market.cc_asset_previous_symbols_map` Table:** Maps assets to their previous symbols.
8.  **`market.cc_asset_market_data` Table:** Stores time-series market data (price, market cap, volume) for assets.
9.  **`market.cc_exchanges` Table:** Stores information about each exchange.
10. **`market.cc_instruments` Table:** The core mapping table for exchange-specific trading pairs.

### Detailed Table Definitions:

*   **`market.cc_assets` Table:**
    *   `asset_id` (BIGINT, from `ID`)
    *   `symbol` (VARCHAR, from `SYMBOL`)
    *   `name` (VARCHAR, from `NAME`)
    *   `uri` (VARCHAR, from `URI`)
    *   `asset_type` (VARCHAR, from `ASSET_TYPE`)
    *   `cc_internal_type` (VARCHAR, from `TYPE`)
    *   `id_legacy` (BIGINT, from `ID_LEGACY`)
    *   `id_parent_asset` (BIGINT nullable, from `ID_PARENT_ASSET`)
    *   `id_asset_issuer` (BIGINT nullable, from `ID_ASSET_ISSUER`)
    *   `asset_issuer_name` (VARCHAR nullable, from `ASSET_ISSUER_NAME`)
    *   `parent_asset_symbol` (VARCHAR nullable, from `PARENT_ASSET_SYMBOL`)
    *   `cc_created_on` (DATETIME, from converted `CREATED_ON` timestamp)
    *   `cc_updated_on` (DATETIME, from converted `UPDATED_ON` timestamp)
    *   `public_notice` (TEXT nullable, from `PUBLIC_NOTICE`)
    *   `logo_url` (VARCHAR nullable, from `LOGO_URL`)
    *   `launch_date` (DATETIME nullable, from converted `LAUNCH_DATE` timestamp)
    *   `description_summary` (TEXT nullable, from `ASSET_DESCRIPTION_SUMMARY`)
    *   `decimal_points` (INT nullable, from `ASSET_DECIMAL_POINTS`)
    *   `symbol_glyph` (VARCHAR nullable, from `ASSET_SYMBOL_GLYPH`)
    *   `created_at` (DATETIME, local record creation timestamp)
    *   `updated_at` (DATETIME, local record update timestamp)
    *   -- Logical Primary Key: `asset_id`
    *   -- Logical Unique Key: `symbol`
    *   -- Logical Foreign Key: `id_parent_asset` references `market.cc_assets(asset_id)`
    *   -- Suggested SingleStore SHARD KEY: `asset_id`
    *   -- Suggested SingleStore SORT KEY: `symbol`, `asset_id`

*   **`market.cc_asset_alternative_ids` Table:**
    *   `asset_id` (BIGINT, NOT NULL, references `market.cc_assets.asset_id`)
    *   `id_source_name` (VARCHAR, NOT NULL, from `ASSET_ALTERNATIVE_IDS[].NAME`)
    *   `alternative_id_value` (VARCHAR, NOT NULL, from `ASSET_ALTERNATIVE_IDS[].ID`)
    *   `created_at` (DATETIME, NOT NULL)
    *   `updated_at` (DATETIME, NOT NULL)
    *   -- Logical Primary Key: (`asset_id`, `id_source_name`, `alternative_id_value`)
    *   -- Logical Foreign Key: `asset_id` references `market.cc_assets(asset_id)`
    *   -- Logical Unique Key: (`asset_id`, `id_source_name`, `alternative_id_value`)
    *   -- Suggested SingleStore SHARD KEY: `asset_id`
    *   -- Suggested SingleStore SORT KEY: `asset_id`, `id_source_name`

*   **`market.cc_asset_industries_map` Table:**
    *   `asset_id` (BIGINT, NOT NULL, references `market.cc_assets.asset_id`)
    *   `industry_name` (VARCHAR, NOT NULL, from `ASSET_INDUSTRIES[].ASSET_INDUSTRY`)
    *   `justification` (TEXT nullable, from `ASSET_INDUSTRIES[].JUSTIFICATION`)
    *   `created_at` (DATETIME, NOT NULL)
    *   `updated_at` (DATETIME, NOT NULL)
    *   -- Logical Primary Key: (`asset_id`, `industry_name`)
    *   -- Logical Foreign Key: `asset_id` references `market.cc_assets(asset_id)`
    *   -- Logical Unique Key: (`asset_id`, `industry_name`)
    *   -- Suggested SingleStore SHARD KEY: `asset_id`
    *   -- Suggested SingleStore SORT KEY: `asset_id`, `industry_name`

*   **`market.cc_asset_consensus_mechanisms_map` Table:**
    *   `asset_id` (BIGINT, NOT NULL, references `market.cc_assets.asset_id`)
    *   `mechanism_name` (VARCHAR, NOT NULL, from `CONSENSUS_MECHANISMS[].NAME`)
    *   `created_at` (DATETIME, NOT NULL)
    *   `updated_at` (DATETIME, NOT NULL)
    *   -- Logical Primary Key: (`asset_id`, `mechanism_name`)
    *   -- Logical Foreign Key: `asset_id` references `market.cc_assets(asset_id)`
    *   -- Logical Unique Key: (`asset_id`, `mechanism_name`)
    *   -- Suggested SingleStore SHARD KEY: `asset_id`
    *   -- Suggested SingleStore SORT KEY: `asset_id`, `mechanism_name`

*   **`market.cc_asset_consensus_algorithm_types_map` Table:**
    *   `asset_id` (BIGINT, NOT NULL, references `market.cc_assets.asset_id`)
    *   `algorithm_name` (VARCHAR, NOT NULL, from `CONSENSUS_ALGORITHM_TYPES[].NAME`)
    *   `description` (TEXT nullable, from `CONSENSUS_ALGORITHM_TYPES[].DESCRIPTION`)
    *   `created_at` (DATETIME, NOT NULL)
    *   `updated_at` (DATETIME, NOT NULL)
    *   -- Logical Primary Key: (`asset_id`, `algorithm_name`)
    *   -- Logical Foreign Key: `asset_id` references `market.cc_assets(asset_id)`
    *   -- Logical Unique Key: (`asset_id`, `algorithm_name`)
    *   -- Suggested SingleStore SHARD KEY: `asset_id`
    *   -- Suggested SingleStore SORT KEY: `asset_id`, `algorithm_name`

*   **`market.cc_asset_hashing_algorithm_types_map` Table:**
    *   `asset_id` (BIGINT, NOT NULL, references `market.cc_assets.asset_id`)
    *   `algorithm_name` (VARCHAR, NOT NULL, from `HASHING_ALGORITHM_TYPES[].NAME`)
    *   `created_at` (DATETIME, NOT NULL)
    *   `updated_at` (DATETIME, NOT NULL)
    *   -- Logical Primary Key: (`asset_id`, `algorithm_name`)
    *   -- Logical Foreign Key: `asset_id` references `market.cc_assets(asset_id)`
    *   -- Logical Unique Key: (`asset_id`, `algorithm_name`)
    *   -- Suggested SingleStore SHARD KEY: `asset_id`
    *   -- Suggested SingleStore SORT KEY: `asset_id`, `algorithm_name`

*   **`market.cc_asset_previous_symbols_map` Table:** (If `PREVIOUS_ASSET_SYMBOLS` is an array)
    *   `asset_id` (BIGINT, NOT NULL, references `market.cc_assets.asset_id`)
    *   `previous_symbol` (VARCHAR, NOT NULL)
    *   `created_at` (DATETIME, NOT NULL)
    *   `updated_at` (DATETIME, NOT NULL)
    *   -- Logical Primary Key: (`asset_id`, `previous_symbol`)
    *   -- Logical Foreign Key: `asset_id` references `market.cc_assets(asset_id)`
    *   -- Logical Unique Key: (`asset_id`, `previous_symbol`)
    *   -- Suggested SingleStore SHARD KEY: `asset_id`
    *   -- Suggested SingleStore SORT KEY: `asset_id`, `previous_symbol`

*   **`market.cc_asset_market_data` Table:**
    *   `asset_id` (BIGINT, NOT NULL, Foreign Key to `market.cc_assets.asset_id`)
    *   `snapshot_ts` (DATETIME, NOT NULL, from converted `PRICE_USD_LAST_UPDATE_TS`)
    *   `price_usd` (DOUBLE nullable, from `PRICE_USD`)
    *   `price_usd_source` (VARCHAR nullable, from `PRICE_USD_SOURCE`)
    *   `mkt_cap_penalty` (DOUBLE nullable, from `MKT_CAP_PENALTY`)
    *   `circulating_mkt_cap_usd` (DOUBLE nullable, from `CIRCULATING_MKT_CAP_USD`)
    *   `total_mkt_cap_usd` (DOUBLE nullable, from `TOTAL_MKT_CAP_USD`)
    *   `spot_moving_24_hour_quote_volume_top_tier_usd` (DOUBLE nullable)
    *   `spot_moving_24_hour_quote_volume_usd` (DOUBLE nullable)
    *   `spot_moving_7_day_quote_volume_top_tier_usd` (DOUBLE nullable)
    *   `spot_moving_7_day_quote_volume_usd` (DOUBLE nullable)
    *   `spot_moving_30_day_quote_volume_top_tier_usd` (DOUBLE nullable)
    *   `spot_moving_30_day_quote_volume_usd` (DOUBLE nullable)
    *   `created_at` (DATETIME, local record creation timestamp)
    *   `updated_at` (DATETIME, local record update timestamp)
    *   -- Logical Primary Key: (`asset_id`, `snapshot_ts`)
    *   -- Logical Foreign Key: `asset_id` references `market.cc_assets(asset_id)`
    *   -- Suggested SingleStore SHARD KEY: `asset_id`
    *   -- Suggested SingleStore SORT KEY: (`asset_id`, `snapshot_ts DESC`)

*   **`market.cc_exchanges` Table:**
    *   `exchange_id` (VARCHAR, from `/data/exchanges/general` `InternalName` or a consistent identifier)
    *   `name` (VARCHAR, from `/data/exchanges/general` `Name`)
    *   `url` (VARCHAR nullable, from `/data/exchanges/general` `Url`)
    *   `logo_url` (VARCHAR nullable, from `/data/exchanges/general` `LogoUrl`)
    *   `country` (VARCHAR nullable, from `/data/exchanges/general` `Country`)
    *   `status` (VARCHAR nullable, from `/spot/v1/markets` `EXCHANGE_STATUS`)
    *   `mapped_instruments_total` (INT nullable, from `/spot/v1/markets` `MAPPED_INSTRUMENTS_TOTAL`)
    *   `unmapped_instruments_total` (INT nullable, from `/spot/v1/markets` `UNMAPPED_INSTRUMENTS_TOTAL`)
    *   `has_orderbook_l2_snapshots` (BOOLEAN nullable, from `/spot/v1/markets` `HAS_ORDERBOOK_L2_MINUTE_SNAPSHOTS_ENABLED`)
    *   `created_at` (DATETIME)
    *   `updated_at` (DATETIME)
    *   `raw_general_info_json` (TEXT nullable, Full JSON from `/data/exchanges/general` for this exchange)
    *   `raw_market_info_json` (TEXT nullable, Full JSON from `/spot/v1/markets` for this exchange)
    *   -- Logical Primary Key: `exchange_id`
    *   -- Logical Unique Key: `name`
    *   -- Suggested SingleStore SHARD KEY: `exchange_id` (if high cardinality) or distribute globally if it's a small reference table.
    *   -- Suggested SingleStore SORT KEY: `name`, `exchange_id`

*   **`market.cc_instruments` Table:**
    *   `instrument_pk` (BIGINT, auto-incrementing if supported, or use composite key)
    *   `exchange_id` (VARCHAR, references `market.cc_exchanges.exchange_id`)
    *   `exchange_instrument_symbol` (VARCHAR, Raw exchange symbol from Spot API `INSTRUMENT`)
    *   `mapped_instrument_symbol` (VARCHAR, Standardized symbol from Spot API `MAPPED_INSTRUMENT`)
    *   `base_asset_id` (BIGINT, references `market.cc_assets.asset_id`, from Spot API `INSTRUMENT_MAPPING.BASE_ID`)
    *   `quote_asset_id` (BIGINT, references `market.cc_assets.asset_id`, from Spot API `INSTRUMENT_MAPPING.QUOTE_ID`)
    *   `status` (VARCHAR, Instrument status on exchange from Spot API `INSTRUMENT_STATUS`)
    *   `first_trade_ts` (BIGINT nullable, from Spot API `FIRST_TRADE_SPOT_TIMESTAMP`)
    *   `last_trade_ts` (BIGINT nullable, from Spot API `LAST_TRADE_SPOT_TIMESTAMP`)
    *   `exchange_specific_details_json` (TEXT nullable, from `INSTRUMENT_EXTERNAL_DATA` in `/spot/v1/latest/instrument/metadata`)
    *   `created_at` (DATETIME)
    *   `updated_at` (DATETIME)
    *   -- Logical Primary Key: `instrument_pk` (or composite `exchange_id`, `mapped_instrument_symbol`)
    *   -- Logical Foreign Key: `exchange_id` references `market.cc_exchanges(exchange_id)`
    *   -- Logical Foreign Key: `base_asset_id` references `market.cc_assets(asset_id)`
    *   -- Logical Foreign Key: `quote_asset_id` references `market.cc_assets(asset_id)`
    *   -- Logical Unique Key: (`exchange_id`, `mapped_instrument_symbol`)
    *   -- Logical Unique Key: (`exchange_id`, `exchange_instrument_symbol`)
    *   -- Suggested SingleStore SHARD KEY: `exchange_id`, `mapped_instrument_symbol` (or `base_asset_id`, `quote_asset_id` depending on query patterns)
    *   -- Suggested SingleStore SORT KEY: `exchange_id`, `mapped_instrument_symbol`, `first_trade_ts`

## Phase 2: Ingestion Process Design

The ingestion process will involve calling several CryptoCompare API endpoints:

1.  **Asset Ingestion (Discovery & Core Metadata):**
    *   **Endpoint:** [`/asset/v1/top/list`](references/data_api/asset_api_spec.md:334)
    *   **Action:**
        *   Call with `groups` parameter set to `ID,BASIC,CLASSIFICATION,DESCRIPTION_SUMMARY,PRICE,MKT_CAP,VOLUME`.
        *   Iterate through all pages to retrieve all assets.
        *   Populate `market.cc_assets` table and its related mapping tables (`market.cc_asset_alternative_ids`, `market.cc_asset_industries_map`, etc.) from the `ID,BASIC,CLASSIFICATION,DESCRIPTION_SUMMARY` groups in the response.
        *   Populate the `market.cc_asset_market_data` table from the `PRICE,MKT_CAP,VOLUME` groups in the response, converting the `PRICE_USD_LAST_UPDATE_TS` field to a `DATETIME` for the `snapshot_ts` column. The ingestion script will also convert `CREATED_ON`, `UPDATED_ON`, and `LAUNCH_DATE` Unix timestamps from the API to `DATETIME` for the `market.cc_assets` table.
    *   **Frequency:** Periodically (e.g., daily) to discover new assets and update existing ones, and to capture new market data snapshots.

2.  **Exchange Ingestion:**
    *   **Endpoint 1:** [`/data/exchanges/general`](references/min_api/general_info_api_spec.md:5) (from Min-API)
    *   **Endpoint 2:** [`/spot/v1/markets`](references/data_api/spot_api_spec.md:990) (from Data API)
    *   Populate/update `market.cc_exchanges` table.

3.  **Instruments (Trading Pairs) Ingestion:**
    *   **Step 3a: Discover Tradable Pairs on Exchanges:**
        *   **Endpoint:** [`/data/v4/all/exchanges`](references/min_api/general_info_api_spec.md:68) (from Min-API)
    *   **Step 3b: Get Detailed Mapped Metadata for Discovered Pairs:**
        *   **Endpoint:** [`/spot/v1/markets/instruments`](references/data_api/spot_api_spec.md:1025) (from Data API)
    *   **Step 3c: (Optional Enrichment) Get Exchange-Specific Instrument Details:**
        *   **Endpoint:** [`/spot/v1/latest/instrument/metadata`](references/data_api/spot_api_spec.md:940) (from Data API)
    *   Populate/update `market.cc_instruments` table, linking to `market.cc_assets` and `market.cc_exchanges`.

## Key Considerations

*   **API Rate Limiting:** Implement respectful polling and error handling for API rate limits.
*   **Data Freshness:** Define appropriate update frequencies for each data type.
*   **Error Handling & Logging:** Implement robust mechanisms for handling API errors, network issues, and unexpected data.
*   **Idempotency:** Ensure ingestion scripts are idempotent.
*   **Configuration:** Store API keys and other configurations securely.
*   **Dependencies:** Asset ingestion should ideally run before instrument ingestion to ensure `asset_id`s are available for foreign key references.
*   **SingleStore Keys:** While traditional PK/FK/UK constraints are not enforced by SingleStore for transactional integrity, they are crucial for defining `SHARD KEY` (for data distribution) and `SORT KEY` (for query performance). The logical keys noted should guide these choices.

This plan aims for an efficient initial load of core mapping data, with options for deeper enrichment where necessary, and utilizes a more granular, normalized schema for asset data suitable for SingleStore.