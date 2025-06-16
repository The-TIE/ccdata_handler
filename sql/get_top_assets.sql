-- Get top assets by 30-day spot quote volume in USD (most recent data per asset)
WITH RankedAssetMarketData AS (
    SELECT
        asset_id,
        spot_moving_30_day_quote_volume_usd,
        ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY snapshot_ts DESC) as rn
    FROM market.cc_asset_market_data
)
SELECT
    ca.symbol
FROM market.cc_assets ca
JOIN RankedAssetMarketData ramd ON ca.asset_id = ramd.asset_id
WHERE ramd.rn = 1
ORDER BY ramd.spot_moving_30_day_quote_volume_usd DESC
LIMIT %s;