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