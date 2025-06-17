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

DROP TABLE IF EXISTS `market`.`cc_asset_alternative_ids`;

CREATE TABLE
    IF NOT EXISTS `market`.`cc_asset_alternative_ids` (
        `asset_id` BIGINT NOT NULL,
        `cmc_id` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `cg_id` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `isin_id` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `valor_id` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `dti_id` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `chain_id` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            PRIMARY KEY (`asset_id`),
            SHARD KEY (`asset_id`),
            SORT KEY (`asset_id`)
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

CREATE TABLE
    IF NOT EXISTS `market`.`cc_exchanges_general` (
        `exchange_api_id` VARCHAR(255) NOT NULL,
        `name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `internal_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL UNIQUE,
            `api_url_path` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `logo_url_path` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `item_types` JSON,
            `centralization_type` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `grade_points` DOUBLE,
            `grade` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `grade_points_legal` DOUBLE,
            `grade_points_kyc_risk` DOUBLE,
            `grade_points_team` DOUBLE,
            `grade_points_data_provision` DOUBLE,
            `grade_points_asset_quality` DOUBLE,
            `grade_points_market_quality` DOUBLE,
            `grade_points_security` DOUBLE,
            `grade_points_neg_reports_penalty` DOUBLE,
            `affiliate_url` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `country` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `has_orderbook` BOOLEAN,
            `has_trades` BOOLEAN,
            `description` TEXT CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `full_address` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `is_sponsored` BOOLEAN,
            `is_recommended` BOOLEAN,
            `rating_avg` DOUBLE,
            `rating_total_users` INT,
            `sort_order` INT,
            `total_volume_24h_usd` DOUBLE,
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            SHARD KEY (`internal_name`),
            SORT KEY (`internal_name`, `name`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_exchange_spot_details` (
        `exchange_internal_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `api_exchange_type` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `exchange_status` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `mapped_instruments_total` INT,
            `unmapped_instruments_total` INT,
            `instruments_active_count` INT,
            `instruments_ignored_count` INT,
            `instruments_retired_count` INT,
            `instruments_expired_count` INT,
            `instruments_retired_unmapped_count` INT,
            `total_trades_exchange_level` BIGINT,
            `has_orderbook_l2_snapshots` BOOLEAN,
            `api_data_retrieved_datetime` DATETIME,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            SHARD KEY (`exchange_internal_name`),
            SORT KEY (`exchange_internal_name`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_instruments_spot` (
        `exchange_internal_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `mapped_instrument_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `api_instrument_type` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `instrument_status_on_exchange` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `exchange_instrument_symbol_raw` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `base_asset_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `base_asset_id` BIGINT,
            `quote_asset_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `quote_asset_id` BIGINT,
            `transform_function` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `instrument_mapping_created_datetime` DATETIME,
            `has_trades` BOOLEAN,
            `first_trade_datetime` DATETIME,
            `last_trade_datetime` DATETIME,
            `total_trades_instrument_level` BIGINT,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            PRIMARY KEY (
                `exchange_internal_name`,
                `mapped_instrument_symbol`
            ),
            SHARD KEY (
                `exchange_internal_name`,
                `mapped_instrument_symbol`
            ),
            SORT KEY (
                `exchange_internal_name`,
                `mapped_instrument_symbol`,
                `last_trade_datetime` DESC
            )
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_rate_limit_status` (
        `timestamp` DATETIME NOT NULL,
        `use_case` VARCHAR(255) NOT NULL,
        `record_timing` VARCHAR(10) NOT NULL,
        `api_key_used_second` INT,
        `api_key_used_minute` INT,
        `api_key_used_hour` INT,
        `api_key_used_day` INT,
        `api_key_used_month` INT,
        `api_key_max_second` INT,
        `api_key_max_minute` INT,
        `api_key_max_hour` INT,
        `api_key_max_day` INT,
        `api_key_max_month` INT,
        `api_key_remaining_second` INT,
        `api_key_remaining_minute` INT,
        `api_key_remaining_hour` INT,
        `api_key_remaining_day` INT,
        `api_key_remaining_month` INT,
        `auth_key_used_second` INT,
        `auth_key_used_minute` INT,
        `auth_key_used_hour` INT,
        `auth_key_used_day` INT,
        `auth_key_used_month` INT,
        `auth_key_max_second` INT,
        `auth_key_max_minute` INT,
        `auth_key_max_hour` INT,
        `auth_key_max_day` INT,
        `auth_key_max_month` INT,
        `auth_key_remaining_second` INT,
        `auth_key_remaining_minute` INT,
        `auth_key_remaining_hour` INT,
        `auth_key_remaining_day` INT,
        `auth_key_remaining_month` INT,
        SHARD KEY (`timestamp`),
        SORT KEY (`timestamp`, `use_case`)
    );

CREATE TABLE
    IF NOT EXISTS `market`.`cc_exchanges_futures_details` (
        `exchange_internal_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `api_exchange_type` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `exchange_status` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `mapped_instruments_total` INT,
            `unmapped_instruments_total` INT,
            `instruments_active_count` INT,
            `instruments_ignored_count` INT,
            `instruments_retired_count` INT,
            `instruments_expired_count` INT,
            `instruments_retired_unmapped_count` INT,
            `total_trades_exchange_level` BIGINT,
            `total_open_interest_updates` BIGINT,
            `total_funding_rate_updates` BIGINT,
            `has_orderbook_l2_snapshots` BOOLEAN,
            `api_data_retrieved_datetime` DATETIME,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            SHARD KEY (`exchange_internal_name`),
            SORT KEY (`exchange_internal_name`)
    );

DROP TABLE IF EXISTS `market`.`cc_instruments_futures`;
CREATE TABLE
    `market`.`cc_instruments_futures` (
        `exchange_internal_name` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `mapped_instrument_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
            `api_instrument_type` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `instrument_status_on_exchange` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `exchange_instrument_symbol_raw` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `index_underlying_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `index_underlying_id` BIGINT,
            `quote_currency_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `quote_currency_id` BIGINT,
            `settlement_currency_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `settlement_currency_id` BIGINT,
            `contract_currency_symbol` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `contract_currency_id` BIGINT,
            `denomination_type` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `transform_function` VARCHAR(255) CHARACTER
        SET
            utf8mb4 COLLATE utf8mb4_general_ci,
            `instrument_mapping_created_datetime` DATETIME,
            `has_trades` BOOLEAN,
            `first_trade_datetime` DATETIME,
            `last_trade_datetime` DATETIME,
            `total_trades_instrument_level` BIGINT,
            `has_funding_rate_updates` BOOLEAN,
            `first_funding_rate_update_datetime` DATETIME,
            `last_funding_rate_update_datetime` DATETIME,
            `total_funding_rate_updates` BIGINT,
            `has_open_interest_updates` BOOLEAN,
            `first_open_interest_update_datetime` DATETIME,
            `last_open_interest_update_datetime` DATETIME,
            `total_open_interest_updates` BIGINT,
            `contract_expiration_datetime` DATETIME,
            `created_at` DATETIME NOT NULL,
            `updated_at` DATETIME NOT NULL,
            PRIMARY KEY (
                `exchange_internal_name`,
                `mapped_instrument_symbol`
            ),
            SHARD KEY (
                `exchange_internal_name`,
                `mapped_instrument_symbol`
            ),
            SORT KEY (
                `exchange_internal_name`,
                `mapped_instrument_symbol`,
                `last_trade_datetime` DESC
            )
    );

CREATE TABLE IF NOT EXISTS market.cc_asset_coin_uid_map (
   asset_id BIGINT NOT NULL,
   symbol VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
   coin_uid VARCHAR(256) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
   match_type VARCHAR(32) NOT NULL,
   match_score DOUBLE NOT NULL,
   mapped_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (asset_id)
);