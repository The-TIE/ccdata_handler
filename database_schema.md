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

This table stores various alternative IDs for assets.

| Column Name           | Type                                          | Nullable | Description                               |
|-----------------------|-----------------------------------------------|----------|-------------------------------------------|
| `asset_id`            | `BIGINT`                                      | NO       | Foreign key to `market.cc_assets`.        |
| `id_source_name`      | `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | Source name of the alternative ID.        |
| `alternative_id_value`| `VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci` | NO       | Value of the alternative ID.              |
| `created_at`          | `DATETIME`                                    | NO       | Local record creation timestamp.          |
| `updated_at`          | `DATETIME`                                    | NO       | Local record update timestamp.            |

**Primary Key:** (`asset_id`, `id_source_name`, `alternative_id_value`)
**Shard Key:** (`asset_id`)
**Sort Key:** (`asset_id`, `id_source_name`)

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