-- Get top trading pairs ordered by volume or activity
SELECT
    cis.exchange_internal_name as market,
    CONCAT(cis.base_asset_symbol, '-', cis.quote_asset_symbol) as instrument
FROM market.cc_instruments_spot cis
JOIN market.cc_assets ca ON cis.base_asset_id = ca.asset_id
WHERE cis.instrument_status_on_exchange = 'ACTIVE'
ORDER BY ca.asset_id ASC  -- Simple ordering by asset_id for now
LIMIT %s;