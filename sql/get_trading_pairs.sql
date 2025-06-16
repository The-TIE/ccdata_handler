-- Get trading pairs for specified assets on specified exchanges
SELECT
    cis.exchange_internal_name,
    cis.base_asset_symbol,
    cis.quote_asset_symbol
FROM market.cc_instruments_spot cis
JOIN market.cc_assets ca ON cis.base_asset_id = ca.asset_id
WHERE cis.exchange_internal_name IN %s
  AND cis.base_asset_symbol IN %s
  AND cis.instrument_status_on_exchange = 'ACTIVE'; -- Only fetch active instruments