CREATE DATABASE IF NOT EXISTS `market`;

CREATE TABLE
    IF NOT EXISTS `market`.`cc_ohlcv_spot_1d_raw` (
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
        `first_trade_timestamp` BIGINT,
        `last_trade_timestamp` BIGINT,
        `first_trade_price` DOUBLE,
        `high_trade_price` DOUBLE,
        `high_trade_timestamp` BIGINT,
        `low_trade_price` DOUBLE,
        `low_trade_timestamp` BIGINT,
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
        `collected_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        SHARD KEY (`datetime`, `exchange`, `symbol`),
        SORT KEY (`datetime`, `exchange`, `symbol`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_ohlcv_spot_indices_1d_raw` (
        `unit` VARCHAR(255),
        `datetime` DATETIME NOT NULL,
        `type` VARCHAR(255),
        `market` VARCHAR(255) NOT NULL,
        `asset` VARCHAR(255) NOT NULL,
        `quote` VARCHAR(255),
        `open` DOUBLE,
        `high` DOUBLE,
        `low` DOUBLE,
        `close` DOUBLE,
        `first_message_timestamp` BIGINT,
        `last_message_timestamp` BIGINT,
        `first_message_value` DOUBLE,
        `high_message_value` DOUBLE,
        `high_message_timestamp` BIGINT,
        `low_message_value` DOUBLE,
        `low_message_timestamp` BIGINT,
        `last_message_value` DOUBLE,
        `total_index_updates` BIGINT,
        `volume` DOUBLE,
        `quote_volume` DOUBLE,
        `volume_top_tier` DOUBLE,
        `quote_volume_top_tier` DOUBLE,
        `volume_direct` DOUBLE,
        `quote_volume_direct` DOUBLE,
        `volume_top_tier_direct` DOUBLE,
        `quote_volume_top_tier_direct` DOUBLE,
        `collected_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        SHARD KEY (`datetime`, `market`, `asset`),
        SORT KEY (`datetime`, `market`, `asset`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_assets` (
        `asset_id` BIGINT NOT NULL,
        `symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `uri` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `asset_type` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `cc_internal_type` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `id_legacy` BIGINT NOT NULL,
            `id_parent_asset` BIGINT,
            `id_asset_issuer` BIGINT,
            `asset_issuer_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `parent_asset_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `cc_created_on` DATETIME NOT NULL,
            `cc_updated_on` DATETIME NOT NULL,
            `public_notice` TEXT CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `logo_url` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `launch_date` DATETIME,
            `description_summary` TEXT CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `decimal_points` INT,
            `symbol_glyph` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            SHARD KEY (`asset_id`),
            SORT KEY (`symbol`, `asset_id`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_asset_alternative_ids` (
        `asset_id` BIGINT NOT NULL,
        `id_source_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `alternative_id_value` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            PRIMARY KEY (
                `asset_id`,
                `id_source_name`,
                `alternative_id_value`
            ),
            SHARD KEY (`asset_id`),
            SORT KEY (`asset_id`, `id_source_name`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_asset_industries_map` (
        `asset_id` BIGINT NOT NULL,
        `industry_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `justification` TEXT CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            PRIMARY KEY (`asset_id`, `industry_name`),
            SHARD KEY (`asset_id`),
            SORT KEY (`asset_id`, `industry_name`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_asset_consensus_mechanisms_map` (
        `asset_id` BIGINT NOT NULL,
        `mechanism_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            PRIMARY KEY (`asset_id`, `mechanism_name`),
            SHARD KEY (`asset_id`),
            SORT KEY (`asset_id`, `mechanism_name`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_asset_consensus_algorithm_types_map` (
        `asset_id` BIGINT NOT NULL,
        `algorithm_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `description` TEXT CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            PRIMARY KEY (`asset_id`, `algorithm_name`),
            SHARD KEY (`asset_id`),
            SORT KEY (`asset_id`, `algorithm_name`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_asset_hashing_algorithm_types_map` (
        `asset_id` BIGINT NOT NULL,
        `algorithm_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            PRIMARY KEY (`asset_id`, `algorithm_name`),
            SHARD KEY (`asset_id`),
            SORT KEY (`asset_id`, `algorithm_name`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_asset_previous_symbols_map` (
        `asset_id` BIGINT NOT NULL,
        `previous_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            PRIMARY KEY (`asset_id`, `previous_symbol`),
            SHARD KEY (`asset_id`),
            SORT KEY (`asset_id`, `previous_symbol`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_asset_market_data` (
        `asset_id` BIGINT NOT NULL,
        `snapshot_ts` DATETIME NOT NULL,
        `price_usd` DOUBLE,
        `price_usd_source` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `mkt_cap_penalty` DOUBLE,
            `circulating_mkt_cap_usd` DOUBLE,
            `total_mkt_cap_usd` DOUBLE,
            `spot_moving_24_hour_quote_volume_top_tier_usd` DOUBLE,
            `spot_moving_24_hour_quote_volume_usd` DOUBLE,
            `spot_moving_7_day_quote_volume_top_tier_usd` DOUBLE,
            `spot_moving_7_day_quote_volume_usd` DOUBLE,
            `spot_moving_30_day_quote_volume_top_tier_usd` DOUBLE,
            `spot_moving_30_day_quote_volume_usd` DOUBLE,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            SHARD KEY (`asset_id`),
            SORT KEY (`asset_id`, `snapshot_ts` DESC)
    );