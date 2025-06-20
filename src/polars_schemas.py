import polars as pl

def get_futures_ohlcv_schema() -> dict:
    """
    Returns the polars schema for futures OHLCV data.
    """
    return {
        "datetime": pl.Datetime(time_unit="us", time_zone="UTC"),
        "market": pl.Utf8,
        "instrument": pl.Utf8,
        "mapped_instrument": pl.Utf8,
        "type": pl.Utf8,
        "index_underlying": pl.Utf8,
        "quote_currency": pl.Utf8,
        "settlement_currency": pl.Utf8,
        "contract_currency": pl.Utf8,
        "denomination_type": pl.Utf8,
        "open": pl.Float64,
        "high": pl.Float64,
        "low": pl.Float64,
        "close": pl.Float64,
        "number_of_contracts": pl.Float64,
        "volume": pl.Float64,
        "quote_volume": pl.Float64,
        "volume_buy": pl.Float64,
        "quote_volume_buy": pl.Float64,
        "volume_sell": pl.Float64,
        "quote_volume_sell": pl.Float64,
        "volume_unknown": pl.Float64,
        "quote_volume_unknown": pl.Float64,
        "total_trades": pl.Int64,
        "total_trades_buy": pl.Int64,
        "total_trades_sell": pl.Int64,
        "total_trades_unknown": pl.Int64,
        "first_trade_timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
        "last_trade_timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
        "first_trade_price": pl.Float64,
        "high_trade_price": pl.Float64,
        "high_trade_timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
        "low_trade_price": pl.Float64,
        "low_trade_timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
        "last_trade_price": pl.Float64,
        "collected_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }

def get_futures_funding_rate_schema() -> dict:
    """
    Returns the polars schema for futures funding rate data.
    """
    return {
        "datetime": pl.Datetime(time_unit="us", time_zone="UTC"),
        "market": pl.Utf8,
        "instrument": pl.Utf8,
        "mapped_instrument": pl.Utf8,
        "type": pl.Utf8,
        "index_underlying": pl.Utf8,
        "quote_currency": pl.Utf8,
        "settlement_currency": pl.Utf8,
        "contract_currency": pl.Utf8,
        "denomination_type": pl.Utf8,
        "interval_ms": pl.Int64,
        "open_fr": pl.Float64,
        "high_fr": pl.Float64,
        "low_fr": pl.Float64,
        "close_fr": pl.Float64,
        "total_funding_rate_updates": pl.Int64,
        "collected_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }

def get_futures_open_interest_schema() -> dict:
    """
    Returns the polars schema for futures open interest data.
    """
    return {
        "datetime": pl.Datetime(time_unit="us", time_zone="UTC"),
        "market": pl.Utf8,
        "instrument": pl.Utf8,
        "mapped_instrument": pl.Utf8,
        "type": pl.Utf8,
        "index_underlying": pl.Utf8,
        "quote_currency": pl.Utf8,
        "settlement_currency": pl.Utf8,
        "contract_currency": pl.Utf8,
        "denomination_type": pl.Utf8,
        "open_oi_contracts": pl.Float64,
        "high_oi_contracts": pl.Float64,
        "low_oi_contracts": pl.Float64,
        "close_oi_contracts": pl.Float64,
        "open_oi_quote": pl.Float64,
        "high_oi_quote": pl.Float64,
        "low_oi_quote": pl.Float64,
        "close_oi_quote": pl.Float64,
        "open_mark_price": pl.Float64,
        "high_oi_mark_price": pl.Float64,
        "high_mark_price": pl.Float64,
        "high_mark_price_oi": pl.Float64,
        "high_quote_mark_price": pl.Float64,
        "low_oi_mark_price": pl.Float64,
        "low_mark_price": pl.Float64,
        "low_mark_price_oi": pl.Float64,
        "low_quote_mark_price": pl.Float64,
        "close_mark_price": pl.Float64,
        "total_open_interest_updates": pl.Int64,
        "collected_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    }