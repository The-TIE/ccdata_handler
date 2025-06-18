SELECT
    exchange_internal_name,
    mapped_instrument_symbol,
    last_trade_datetime,
    first_trade_datetime
FROM
    market.cc_instruments_futures
WHERE
    exchange_internal_name IN %s
    AND has_trades = TRUE
    AND instrument_status_on_exchange IN %s;