# Database Schema

## Table: `market.cc_ohlcv_spot_1d_raw`

This table stores daily Open, High, Low, Close, and Volume (OHLCV) data for spot cryptocurrency instruments from CryptoCompare.

| Column Name           | Type         | Nullable | Description                                     |
|-----------------------|--------------|----------|-------------------------------------------------|
| `datetime`            | `DATETIME`   | NO       | The timestamp of the OHLCV data (daily).        |
| `exchange`            | `VARCHAR(255)`| NO       | The exchange where the data originated.         |
| `symbol_unmapped`     | `VARCHAR(255)`| NO       | The unmapped instrument symbol (e.g., `BTC-USDT`).|
| `symbol`              | `VARCHAR(255)`| YES      | The mapped instrument symbol.                   |
| `base`                | `VARCHAR(255)`| YES      | The base asset symbol (e.g., `BTC`).            |
| `quote`               | `VARCHAR(255)`| YES      | The quote asset symbol (e.g., `USD`).           |
| `base_id`             | `BIGINT`     | YES      | Internal ID for the base asset.                 |
| `quote_id`            | `BIGINT`     | YES      | Internal ID for the quote asset.                |
| `transform_function`  | `VARCHAR(255)`| YES      | Function applied to transform the data.         |
| `open`                | `DOUBLE`     | YES      | The opening price for the period.               |
| `high`                | `DOUBLE`     | YES      | The highest price for the period.               |
| `low`                 | `DOUBLE`     | YES      | The lowest price for the period.                |
| `close`               | `DOUBLE`     | YES      | The closing price for the period.               |
| `first_trade_timestamp`| `BIGINT`     | YES      | Unix timestamp of the first trade in the period.|
| `last_trade_timestamp`| `BIGINT`     | YES      | Unix timestamp of the last trade in the period. |
| `first_trade_price`   | `DOUBLE`     | YES      | Price of the first trade in the period.         |
| `high_trade_price`    | `DOUBLE`     | YES      | Price of the highest trade in the period.       |
| `high_trade_timestamp`| `BIGINT`     | YES      | Timestamp of the highest trade in the period.   |
| `low_trade_price`     | `DOUBLE`     | YES      | Price of the lowest trade in the period.        |
| `low_trade_timestamp` | `BIGINT`     | YES      | Timestamp of the lowest trade in the period.    |
| `last_trade_price`    | `DOUBLE`     | YES      | Price of the last trade in the period.          |
| `total_trades`        | `BIGINT`     | YES      | Total number of trades in the period.           |
| `total_trades_buy`    | `BIGINT`     | YES      | Total number of buy trades.                     |
| `total_trades_sell`   | `BIGINT`     | YES      | Total number of sell trades.                    |
| `total_trades_unknown`| `BIGINT`     | YES      | Total number of unknown trades.                 |
| `volume`              | `DOUBLE`     | YES      | Volume in base asset.                           |
| `quote_volume`        | `DOUBLE`     | YES      | Volume in quote asset.                          |
| `volume_buy`          | `DOUBLE`     | YES      | Buy volume in base asset.                       |
| `quote_volume_buy`    | `DOUBLE`     | YES      | Buy volume in quote asset.                      |
| `volume_sell`         | `DOUBLE`     | YES      | Sell volume in base asset.                      |
| `quote_volume_sell`   | `DOUBLE`     | YES      | Sell volume in quote asset.                     |
| `volume_unknown`      | `DOUBLE`     | YES      | Unknown volume in base asset.                   |
| `quote_volume_unknown`| `DOUBLE`     | YES      | Unknown volume in quote asset.                  |
| `collected_at`        | `DATETIME`   | NO       | Timestamp when the data was collected.          |

**Shard Key:** (`datetime`, `exchange`, `symbol`)
**Sort Key:** (`datetime`, `exchange`, `symbol`)

## Table: `market.cc_ohlcv_spot_indices_1d_raw`

This table stores daily Open, High, Low, Close, and Volume (OHLCV) data for cryptocurrency indices from CryptoCompare.

| Column Name           | Type             | Nullable | Description                                     |
|-----------------------|------------------|----------|-------------------------------------------------|
| `unit`                | `VARCHAR(255)`   | YES      | The unit of the OHLCV data (e.g., `DAY`).       |
| `datetime`            | `DATETIME`       | NO       | The timestamp of the OHLCV data.                |
| `type`                | `VARCHAR(255)`   | YES      | The type of data.                               |
| `market`              | `VARCHAR(255)`   | NO       | The index family (e.g., `cadli`).               |
| `asset`               | `VARCHAR(255)`   | NO       | The asset symbol (e.g., `BTC`).                 |
| `quote`               | `VARCHAR(255)`   | YES      | The quote asset symbol (e.g., `USD`).           |
| `open`                | `DOUBLE`         | YES      | The opening price for the period.               |
| `high`                | `DOUBLE`         | YES      | The highest price for the period.               |
| `low`                 | `DOUBLE`         | YES      | The lowest price for the period.                |
| `close`               | `DOUBLE`         | YES      | The closing price for the period.               |
| `first_message_timestamp`| `BIGINT`      | YES      | Unix timestamp of the first message in the period.|
| `last_message_timestamp`| `BIGINT`      | YES      | Unix timestamp of the last message in the period. |
| `first_message_value` | `DOUBLE`         | YES      | Value of the first message in the period.       |
| `high_message_value`  | `DOUBLE`         | YES      | Value of the highest message in the period.     |
| `high_message_timestamp`| `BIGINT`      | YES      | Timestamp of the highest message in the period. |
| `low_message_value`   | `DOUBLE`         | YES      | Value of the lowest message in the period.      |
| `low_message_timestamp`| `BIGINT`      | YES      | Timestamp of the lowest message in the period.  |
| `last_message_value`  | `DOUBLE`         | YES      | Value of the last message in the period.        |
| `total_index_updates` | `BIGINT`      | YES      | Total number of index updates in the period.    |
| `volume`              | `DOUBLE`         | YES      | Volume in base asset.                           |
| `quote_volume`        | `DOUBLE`         | YES      | Volume in quote asset.                          |
| `volume_top_tier`     | `DOUBLE`         | YES      | Top tier volume in base asset.                  |
| `quote_volume_top_tier`| `DOUBLE`         | YES      | Top tier volume in quote asset.                 |
| `volume_direct`       | `DOUBLE`         | YES      | Direct volume in base asset.                    |
| `quote_volume_direct` | `DOUBLE`         | YES      | Direct volume in quote asset.                   |
| `volume_top_tier_direct`| `DOUBLE`         | YES      | Top tier direct volume in base asset.           |
| `quote_volume_top_tier_direct`| `DOUBLE`         | YES      | Top tier direct volume in quote asset.          |
| `collected_at`        | `DATETIME`       | NO       | Timestamp when the data was collected.          |

**Shard Key:** (`datetime`, `market`, `asset`)
**Sort Key:** (`datetime`, `market`, `asset`)

## Table: `market.cc_assets`

This table stores general information about each unique asset.

| Column Name           | Type                                          | Nullable | Description                               |
|-----------------------|-----------------------------------------------|----------|-------------------------------------------|
| `asset_id`            | `BIGINT`                                      | NO       | Unique identifier for the asset.          |
| `symbol`              | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | The symbol of the asset.                  |
| `name`                | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | The name of the asset.                    |
| `uri`                 | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | URI for the asset.                        |
| `asset_type`          | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | Type of asset.                            |
| `cc_internal_type`    | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | CryptoCompare internal type.              |
| `id_legacy`           | `BIGINT`                                      | NO       | Legacy ID.                                |
| `id_parent_asset`     | `BIGINT`                                      | YES      | Parent asset ID.                          |
| `id_asset_issuer`     | `BIGINT`                                      | YES      | Asset issuer ID.                          |
| `asset_issuer_name`   | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Name of the asset issuer.                 |
| `parent_asset_symbol` | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Symbol of the parent asset.               |
| `cc_created_on`       | `DATETIME`                                    | NO       | CryptoCompare creation timestamp (converted from Unix ts). |
| `cc_updated_on`       | `DATETIME`                                    | NO       | CryptoCompare update timestamp (converted from Unix ts).   |
| `public_notice`       | `TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Public notice for the asset.              |
| `logo_url`            | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | URL of the asset logo.                    |
| `launch_date`         | `DATETIME`                                    | YES      | Launch date (converted from Unix ts).       |
| `description_summary` | `TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Summary of the asset description.         |
| `decimal_points`      | `INT`                                         | YES      | Decimal points for the asset.             |
| `symbol_glyph`        | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Glyph for the asset symbol.               |
| `created_at`          | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`          | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Shard Key:** (`asset_id`)
**Sort Key:** (`symbol`, `asset_id`)

## Table: `market.cc_asset_alternative_ids`

This table stores various alternative IDs for assets, with each source having its own column.

| Column Name           | Type                                          | Nullable | Description                               |
|-----------------------|-----------------------------------------------|----------|-------------------------------------------|
| `asset_id`            | `BIGINT`                                      | NO       | Foreign key to `market.cc_assets`.        |
| `cmc_id`              | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | CoinMarketCap ID.                         |
| `cg_id`               | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | CoinGecko ID.                             |
| `isin_id`             | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | International Securities Identification Number. |
| `valor_id`            | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Valor ID.                                 |
| `dti_id`              | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Digital Token Identifier.                 |
| `chain_id`            | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Blockchain Chain ID.                      |
| `created_at`          | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`          | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Primary Key:** (`asset_id`)
**Shard Key:** (`asset_id`)
**Sort Key:** (`asset_id`)

## Table: `market.cc_asset_industries_map`

This table maps assets to their industries.

| Column Name           | Type                                          | Nullable | Description                               |
|-----------------------|-----------------------------------------------|----------|-------------------------------------------|
| `asset_id`            | `BIGINT`                                      | NO       | Foreign key to `market.cc_assets`.        |
| `industry_name`       | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | Name of the industry.                     |
| `justification`       | `TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Justification for the industry mapping.   |
| `created_at`          | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`          | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Primary Key:** (`asset_id`, `industry_name`)
**Shard Key:** (`asset_id`)
**Sort Key:** (`asset_id`, `industry_name`)

## Table: `market.cc_asset_consensus_mechanisms_map`

This table maps assets to their consensus mechanisms.

| Column Name           | Type                                          | Nullable | Description                               |
|-----------------------|-----------------------------------------------|----------|-------------------------------------------|
| `asset_id`            | `BIGINT`                                      | NO       | Foreign key to `market.cc_assets`.        |
| `mechanism_name`      | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | Name of the consensus mechanism.          |
| `created_at`          | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`          | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Primary Key:** (`asset_id`, `mechanism_name`)
**Shard Key:** (`asset_id`)
**Sort Key:** (`asset_id`, `mechanism_name`)

## Table: `market.cc_asset_consensus_algorithm_types_map`

This table maps assets to their consensus algorithm types.

| Column Name           | Type                                          | Nullable | Description                               |
|-----------------------|-----------------------------------------------|----------|-------------------------------------------|
| `asset_id`            | `BIGINT`                                      | NO       | Foreign key to `market.cc_assets`.        |
| `algorithm_name`      | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | Name of the consensus algorithm.          |
| `description`         | `TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Description of the algorithm.             |
| `created_at`          | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`          | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Primary Key:** (`asset_id`, `algorithm_name`)
**Shard Key:** (`asset_id`)
**Sort Key:** (`asset_id`, `algorithm_name`)

## Table: `market.cc_asset_hashing_algorithm_types_map`

This table maps assets to their hashing algorithm types.

| Column Name           | Type                                          | Nullable | Description                               |
|-----------------------|-----------------------------------------------|----------|-------------------------------------------|
| `asset_id`            | `BIGINT`                                      | NO       | Foreign key to `market.cc_assets`.        |
| `algorithm_name`      | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | Name of the hashing algorithm.            |
| `created_at`          | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`          | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Primary Key:** (`asset_id`, `algorithm_name`)
**Shard Key:** (`asset_id`)
**Sort Key:** (`asset_id`, `algorithm_name`)

## Table: `market.cc_asset_previous_symbols_map`

This table maps assets to their previous symbols.

| Column Name           | Type                                          | Nullable | Description                               |
|-----------------------|-----------------------------------------------|----------|-------------------------------------------|
| `asset_id`            | `BIGINT`                                      | NO       | Foreign key to `market.cc_assets`.        |
| `previous_symbol`     | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | Previous symbol of the asset.             |
| `created_at`          | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`          | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Primary Key:** (`asset_id`, `previous_symbol`)
**Shard Key:** (`asset_id`)
**Sort Key:** (`asset_id`, `previous_symbol`)

## Table: `market.cc_asset_market_data`

This table stores time-series market data (price, market cap, volume) for assets.

| Column Name                                   | Type                                          | Nullable | Description                                                                 |
|-----------------------------------------------|-----------------------------------------------|----------|-----------------------------------------------------------------------------|
| `asset_id`                                    | `BIGINT`                                      | NO       | Foreign key to `market.cc_assets.asset_id`.                                 |
| `snapshot_ts`                                 | `DATETIME`                                    | NO       | Timestamp of data snapshot (converted from API's `PRICE_USD_LAST_UPDATE_TS`). |
| `price_usd`                                   | `DOUBLE`                                      | YES      | Current price in USD.                                                       |
| `price_usd_source`                            | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Source of the USD price.                                                    |
| `mkt_cap_penalty`                             | `DOUBLE`                                      | YES      | Market cap penalty.                                                         |
| `circulating_mkt_cap_usd`                     | `DOUBLE`                                      | YES      | Circulating market cap in USD.                                              |
| `total_mkt_cap_usd`                           | `DOUBLE`                                      | YES      | Total market cap in USD.                                                    |
| `spot_moving_24_hour_quote_volume_top_tier_usd` | `DOUBLE`                                      | YES      | 24-hour spot quote volume (top tier) in USD.                                |
| `spot_moving_24_hour_quote_volume_usd`          | `DOUBLE`                                      | YES      | 24-hour spot quote volume in USD.                                           |
| `spot_moving_7_day_quote_volume_top_tier_usd`   | `DOUBLE`                                      | YES      | 7-day spot quote volume (top tier) in USD.                                  |
| `spot_moving_7_day_quote_volume_usd`            | `DOUBLE`                                      | YES      | 7-day spot quote volume in USD.                                             |
| `spot_moving_30_day_quote_volume_top_tier_usd`  | `DOUBLE`                                      | YES      | 30-day spot quote volume (top tier) in USD.                                 |
| `spot_moving_30_day_quote_volume_usd`           | `DOUBLE`                                      | YES      | 30-day spot quote volume in USD.                                            |
| `created_at`                                  | `DATETIME`                                    | NO       | Local record creation timestamp.                                            |
| `updated_at`                                  | `DATETIME`                                    | NO       | Local record update timestamp.                                              |

**Primary Key:** (`asset_id`, `snapshot_ts`)
**Shard Key:** `asset_id`
**Sort Key:** (`asset_id`, `snapshot_ts DESC`)

## Table: `market.cc_exchanges_general`

This table stores general information about cryptocurrency exchanges from CryptoCompare.

| Column Name           | Type                                          | Nullable | Description                               |
|-----------------------|-----------------------------------------------|----------|-------------------------------------------|
| `exchange_api_id`     | `VARCHAR(255)`                                | NO       | Unique identifier for the exchange from the API. |
| `name`                | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | The display name of the exchange.         |
| `internal_name`       | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | CryptoCompare's internal name for the exchange (e.g., `kraken`). |
| `api_url_path`        | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | API URL path for the exchange.            |
| `logo_url_path`       | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | URL path to the exchange's logo.          |
| `item_types`          | `JSON`                                        | YES      | JSON array of item types supported by the exchange. |
| `centralization_type` | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Type of centralization (e.g., `CENTRALIZED`). |
| `grade_points`        | `DOUBLE`                                      | YES      | Overall grade points.                     |
| `grade`               | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Overall grade (e.g., `A+`).               |
| `grade_points_legal`  | `DOUBLE`                                      | YES      | Grade points for legal aspects.           |
| `grade_points_kyc_risk`| `DOUBLE`                                      | YES      | Grade points for KYC risk.                |
| `grade_points_team`   | `DOUBLE`                                      | YES      | Grade points for team quality.            |
| `grade_points_data_provision`| `DOUBLE`                               | YES      | Grade points for data provision.          |
| `grade_points_asset_quality`| `DOUBLE`                               | YES      | Grade points for asset quality.           |
| `grade_points_market_quality`| `DOUBLE`                               | YES      | Grade points for market quality.          |
| `grade_points_security`| `DOUBLE`                                      | YES      | Grade points for security.                |
| `grade_points_neg_reports_penalty`| `DOUBLE`                         | YES      | Penalty points for negative reports.      |
| `affiliate_url`       | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Affiliate URL for the exchange.           |
| `country`             | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Country of operation.                     |
| `has_orderbook`       | `BOOLEAN`                                     | YES      | Indicates if the exchange has an orderbook. |
| `has_trades`          | `BOOLEAN`                                     | YES      | Indicates if the exchange has trades.     |
| `description`         | `TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Description of the exchange.              |
| `full_address`        | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Full address of the exchange.             |
| `is_sponsored`        | `BOOLEAN`                                     | YES      | Indicates if the exchange is sponsored.   |
| `is_recommended`      | `BOOLEAN`                                     | YES      | Indicates if the exchange is recommended. |
| `rating_avg`          | `DOUBLE`                                      | YES      | Average user rating.                      |
| `rating_total_users`  | `INT`                                         | YES      | Total number of users who rated.          |
| `sort_order`          | `INT`                                         | YES      | Sort order for display.                   |
| `total_volume_24h_usd`| `DOUBLE`                                      | YES      | Total 24-hour volume in USD.              |
| `created_at`          | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`          | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Primary Key:** (`exchange_api_id`)
**Shard Key:** (`internal_name`)
**Sort Key:** (`internal_name`, `name`)

## Table: `market.cc_exchange_spot_details`

This table stores spot market-specific details for exchanges from CryptoCompare's `/spot/v1/markets/instruments` endpoint.

| Column Name                   | Type                                          | Nullable | Description                                     |
|-------------------------------|-----------------------------------------------|----------|-------------------------------------------------|
| `exchange_internal_name`      | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | CryptoCompare's internal name for the exchange (e.g., `kraken`). Foreign key to `market.cc_exchanges_general.internal_name`. |
| `api_exchange_type`           | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | The type of exchange as reported by the API (`TYPE` field). |
| `exchange_status`             | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | The operational status of the exchange (`EXCHANGE_STATUS`). |
| `mapped_instruments_total`    | `INT`                                         | YES      | Total count of mapped instruments on the exchange. |
| `unmapped_instruments_total`  | `INT`                                         | YES      | Total count of unmapped instruments on the exchange. |
| `instruments_active_count`    | `INT`                                         | YES      | Number of active instruments.                   |
| `instruments_ignored_count`   | `INT`                                         | YES      | Number of ignored instruments.                  |
| `instruments_retired_count`   | `INT`                                         | YES      | Number of retired instruments.                  |
| `instruments_expired_count`   | `INT`                                         | YES      | Number of expired instruments.                  |
| `instruments_retired_unmapped_count`| `INT`                                   | YES      | Number of retired unmapped instruments.         |
| `total_trades_exchange_level` | `BIGINT`                                      | YES      | Total spot trades at the exchange level.        |
| `has_orderbook_l2_snapshots`  | `BOOLEAN`                                     | YES      | Indicates if the exchange has L2 minute snapshots enabled. |
| `api_data_retrieved_datetime` | `DATETIME`                                    | YES      | Timestamp when this specific API data was retrieved. |
| `created_at`                  | `DATETIME`                                    | NO       | Local record creation timestamp.                |
| `updated_at`                  | `DATETIME`                                    | NO       | Local record update timestamp.                  |

**Primary Key:** (`exchange_internal_name`)
**Shard Key:** (`exchange_internal_name`)
**Sort Key:** (`exchange_internal_name`)

## Table: `market.cc_instruments_spot`

This table stores details for individual spot market instruments from CryptoCompare's `/spot/v1/markets/instruments` endpoint.

| Column Name                       | Type                                          | Nullable | Description                               |
|-----------------------------------|-----------------------------------------------|----------|-------------------------------------------|
| `exchange_internal_name`          | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | CryptoCompare's internal name for the exchange. Part of PK, FK to `market.cc_exchange_spot_details`. |
| `mapped_instrument_symbol`        | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | The mapped instrument symbol (e.g., `BTC-USD`). Part of PK. |
| `api_instrument_type`             | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | The type of instrument as reported by the API (`TYPE` field). |
| `instrument_status_on_exchange`   | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | The status of the instrument on the exchange (`INSTRUMENT_STATUS`). |
| `exchange_instrument_symbol_raw`  | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | The raw instrument symbol on the exchange (`INSTRUMENT`). |
| `base_asset_symbol`               | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | The base asset symbol (e.g., `BTC`).      |
| `base_asset_id`                   | `BIGINT`                                      | YES      | Internal ID for the base asset. FK to `market.cc_assets`. |
| `quote_asset_symbol`              | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | The quote asset symbol (e.g., `USD`).     |
| `quote_asset_id`                  | `BIGINT`                                      | YES      | Internal ID for the quote asset. FK to `market.cc_assets`. |
| `transform_function`              | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | YES      | Function applied to transform the instrument data. |
| `instrument_mapping_created_datetime`| `DATETIME`                                 | YES      | Timestamp when the instrument mapping was created (converted from Unix ts). |
| `has_trades`                      | `BOOLEAN`                                     | YES      | Indicates if the instrument has trades.   |
| `first_trade_datetime`            | `DATETIME`                                    | YES      | Timestamp of the first trade for this instrument (converted from Unix ts). |
| `last_trade_datetime`             | `DATETIME`                                    | YES      | Timestamp of the last trade for this instrument (converted from Unix ts). |
| `total_trades_instrument_level`   | `BIGINT`                                      | YES      | Total spot trades for this instrument.    |
| `created_at`                      | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`                      | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Primary Key:** (`exchange_internal_name`, `mapped_instrument_symbol`)
**Shard Key:** (`exchange_internal_name`, `mapped_instrument_symbol`)
**Sort Key:** (`exchange_internal_name`, `mapped_instrument_symbol`, `last_trade_datetime DESC`)

## Table: `market.cc_rate_limit_status`

This table stores information about the API rate limit status.

| Column Name           | Type         | Nullable | Description                               |
|-----------------------|--------------|----------|-------------------------------------------|
| `timestamp`           | `DATETIME`   | NO       | The timestamp when the rate limit data was recorded. |
| `use_case`            | `VARCHAR(255)`| NO       | The use case or script making the API call. |
| `record_timing`       | `VARCHAR(10)`| NO       | Indicates if the data was recorded 'pre' or 'post' API call. |
| `api_key_used_second` | `INT`        | YES      | API key usage in the current second.      |
| `api_key_used_minute` | `INT`        | YES      | API key usage in the current minute.      |
| `api_key_used_hour`   | `INT`        | YES      | API key usage in the current hour.        |
| `api_key_used_day`    | `INT`        | YES      | API key usage in the current day.         |
| `api_key_used_month`  | `INT`        | YES      | API key usage in the current month.       |
| `api_key_max_second`  | `INT`        | YES      | API key max limit per second.             |
| `api_key_max_minute`  | `INT`        | YES      | API key max limit per minute.             |
| `api_key_max_hour`    | `INT`        | YES      | API key max limit per hour.               |
| `api_key_max_day`     | `INT`        | YES      | API key max limit per day.                |
| `api_key_max_month`   | `INT`        | YES      | API key max limit per month.              |
| `api_key_remaining_second`| `INT`    | YES      | API key remaining calls in the current second. |
| `api_key_remaining_minute`| `INT`    | YES      | API key remaining calls in the current minute. |
| `api_key_remaining_hour`| `INT`      | YES      | API key remaining calls in the current hour. |
| `api_key_remaining_day`| `INT`       | YES      | API key remaining calls in the current day. |
| `api_key_remaining_month`| `INT`     | YES      | API key remaining calls in the current month. |
| `auth_key_used_second`| `INT`        | YES      | Auth key usage in the current second.     |
| `auth_key_used_minute`| `INT`        | YES      | Auth key usage in the current minute.     |
| `auth_key_used_hour`  | `INT`        | YES      | Auth key usage in the current hour.       |
| `auth_key_used_day`   | `INT`        | YES      | Auth key usage in the current day.        |
| `auth_key_used_month` | `INT`        | YES      | Auth key usage in the current month.      |
| `auth_key_max_second` | `INT`        | YES      | Auth key max limit per second.            |
| `auth_key_max_minute` | `INT`        | YES      | Auth key max limit per minute.            |
| `auth_key_max_hour`   | `INT`        | YES      | Auth key max limit per hour.              |
| `auth_key_max_day`    | `INT`        | YES      | Auth key max limit per day.               |
| `auth_key_max_month`  | `INT`        | YES      | Auth key max limit per month.             |
| `auth_key_remaining_second`| `INT`   | YES      | Auth key remaining calls in the current second. |
| `auth_key_remaining_minute`| `INT`   | YES      | Auth key remaining calls in the current minute. |
| `auth_key_remaining_hour`| `INT`     | YES      | Auth key remaining calls in the current hour. |
| `auth_key_remaining_day`| `INT`      | YES      | Auth key remaining calls in the current day. |
| `auth_key_remaining_month`| `INT`    | YES      | Auth key remaining calls in the current month. |

**Shard Key:** (`timestamp`)
**Sort Key:** (`timestamp`, `use_case`)