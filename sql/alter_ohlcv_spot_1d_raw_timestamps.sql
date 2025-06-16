-- Create a new temporary table with DATETIME columns for timestamps
CREATE TABLE market.cc_ohlcv_spot_1d_raw_new (
    `datetime` DATETIME NOT NULL,
    `exchange` VARCHAR(255) NOT NULL,
    `symbol_unmapped` VARCHAR(255) NOT NULL,
    `symbol` VARCHAR(255),
    `base` VARCHAR(255),
    `quote` VARCHAR(255),
    `base_id` BIGINT,
    `quote_id` BIGINT,
    `transform_function` VARCHAR(255),
    `open` DOUBLE,
    `high` DOUBLE,
    `low` DOUBLE,
    `close` DOUBLE,
    `first_trade_timestamp` DATETIME, -- Changed from BIGINT
    `last_trade_timestamp` DATETIME,  -- Changed from BIGINT
    `first_trade_price` DOUBLE,
    `high_trade_price` DOUBLE,
    `high_trade_timestamp` DATETIME, -- Changed from BIGINT
    `low_trade_price` DOUBLE,
    `low_trade_timestamp` DATETIME,  -- Changed from BIGINT
    `last_trade_price` DOUBLE,
    `total_trades` BIGINT,
    `total_trades_buy` BIGINT,
    `total_trades_sell` BIGINT,
    `total_trades_unknown` BIGINT,
    `volume` DOUBLE,
    `quote_volume` DOUBLE,
    `volume_buy` DOUBLE,
    `quote_volume_buy` DOUBLE,
    `volume_sell` DOUBLE,
    `quote_volume_sell` DOUBLE,
    `volume_unknown` DOUBLE,
    `quote_volume_unknown` DOUBLE,
    `collected_at` DATETIME NOT NULL,
    SHARD KEY (`datetime`, `exchange`, `symbol`),
    SORT KEY (`datetime`, `exchange`, `symbol`)
);

-- Insert data from the old table into the new table, converting timestamps
INSERT INTO market.cc_ohlcv_spot_1d_raw_new (
    `datetime`,
    `exchange`,
    `symbol_unmapped`,
    `symbol`,
    `base`,
    `quote`,
    `base_id`,
    `quote_id`,
    `transform_function`,
    `open`,
    `high`,
    `low`,
    `close`,
    `first_trade_timestamp`,
    `last_trade_timestamp`,
    `first_trade_price`,
    `high_trade_price`,
    `high_trade_timestamp`,
    `low_trade_price`,
    `low_trade_timestamp`,
    `last_trade_price`,
    `total_trades`,
    `total_trades_buy`,
    `total_trades_sell`,
    `total_trades_unknown`,
    `volume`,
    `quote_volume`,
    `volume_buy`,
    `quote_volume_buy`,
    `volume_sell`,
    `quote_volume_sell`,
    `volume_unknown`,
    `quote_volume_unknown`,
    `collected_at`
)
SELECT
    `datetime`,
    `exchange`,
    `symbol_unmapped`,
    `symbol`,
    `base`,
    `quote`,
    `base_id`,
    `quote_id`,
    `transform_function`,
    `open`,
    `high`,
    `low`,
    `close`,
    FROM_UNIXTIME(`first_trade_timestamp`), -- Convert BIGINT to DATETIME
    FROM_UNIXTIME(`last_trade_timestamp`),  -- Convert BIGINT to DATETIME
    `first_trade_price`,
    `high_trade_price`,
    FROM_UNIXTIME(`high_trade_timestamp`), -- Convert BIGINT to DATETIME
    `low_trade_price`,
    FROM_UNIXTIME(`low_trade_timestamp`),  -- Convert BIGINT to DATETIME
    `last_trade_price`,
    `total_trades`,
    `total_trades_buy`,
    `total_trades_sell`,
    `total_trades_unknown`,
    `volume`,
    `quote_volume`,
    `volume_buy`,
    `quote_volume_buy`,
    `volume_sell`,
    `quote_volume_sell`,
    `volume_unknown`,
    `quote_volume_unknown`,
    `collected_at`
FROM market.cc_ohlcv_spot_1d_raw;

-- Drop the old table
DROP TABLE market.cc_ohlcv_spot_1d_raw;

-- Rename the new table to the original table name
ALTER TABLE market.cc_ohlcv_spot_1d_raw_new RENAME TO cc_ohlcv_spot_1d_raw;