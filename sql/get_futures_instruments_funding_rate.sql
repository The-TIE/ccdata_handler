SELECT
  exchange_internal_name,
  mapped_instrument_symbol,
  last_funding_rate_update_datetime
FROM market.cc_instruments_futures
WHERE
  exchange_internal_name IN %s AND
  instrument_status_on_exchange IN %s AND
  has_funding_rate_updates = TRUE;