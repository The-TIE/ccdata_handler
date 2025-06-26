import os
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import argparse
import time
import logging

from src.logger_config import setup_logger, LOG_DIR
from src.db.connection import DbConnectionManager
from src.db.utils import deduplicate_table, ensure_utc_datetime
from src.data_api.futures_api_client import CcdataFuturesApiClient
from src.rate_limit_tracker import record_rate_limit_status
from src.utils import get_end_of_previous_period, map_interval_to_unit
from src.polars_schemas import (
    get_futures_ohlcv_schema,
    get_futures_funding_rate_schema,
    get_futures_open_interest_schema,
)

logger = setup_logger(
    __name__,
    log_file_path=os.path.join(LOG_DIR, "futures_ingestor.log"),
)


class FuturesIngestor:
    """
    A centralized class for ingesting various types of futures data (OHLCV, Funding Rate, Open Interest).
    It handles common logic for argument parsing, database interaction, API calls, and data mapping.
    """

    # Configuration for different data types
    CONFIG = {
        "ohlcv": {
            "api_method": "get_futures_historical_ohlcv",
            "db_table_template": "market.cc_futures_ohlcv_{interval}",
            "get_instruments_sql": "get_futures_instruments.sql",
            "last_update_col": "last_trade_datetime",
            "first_update_col": "first_trade_datetime",
            "max_limit_per_call": {"1d": 5000, "1h": 2000, "1m": 2000},
            "record_mapper": "_map_ohlcv_record",
            "deduplicate_latest_col": "collected_at",
            "schema_getter": get_futures_ohlcv_schema,
        },
        "funding-rate": {
            "api_method": "get_futures_historical_funding_rate_ohlc",
            "db_table_template": "market.cc_futures_funding_rate_ohlc_{interval}",
            "get_instruments_sql": "get_futures_instruments_funding_rate.sql",
            "last_update_col": "last_funding_rate_update_datetime",
            "first_update_col": "first_funding_rate_update_datetime",
            "max_limit_per_call": {"1d": 5000, "1h": 2000, "1m": 2000},
            "record_mapper": "_map_funding_rate_record",
            "deduplicate_latest_col": "collected_at",
            "schema_getter": get_futures_funding_rate_schema,
        },
        "open-interest": {
            "api_method": "get_futures_historical_oi_ohlc",
            "db_table_template": "market.cc_futures_open_interest_ohlc_{interval}",
            "get_instruments_sql": "get_futures_instruments_open_interest.sql",
            "last_update_col": "last_open_interest_update_datetime",
            "first_update_col": "first_open_interest_update_datetime",
            "max_limit_per_call": {"1d": 5000, "1h": 2000, "1m": 2000},
            "record_mapper": "_map_open_interest_record",
            "deduplicate_latest_col": "collected_at",
            "schema_getter": get_futures_open_interest_schema,
        },
    }

    def __init__(self, data_type: str, interval: str):
        logger.debug(
            f"FuturesIngestor initialized with data_type: {data_type}, interval: '{interval}'"
        )
        if data_type not in self.CONFIG:
            raise ValueError(f"Unsupported data_type: {data_type}")
        if interval not in ["1d", "1h", "1m"]:
            raise ValueError(f"Unsupported interval: {interval}")

        self.data_type_config = self.CONFIG[data_type]
        self.data_type = data_type
        self.interval = interval
        self.db_connection = DbConnectionManager()
        self.futures_api_client = CcdataFuturesApiClient()
        self.table_name = self.data_type_config["db_table_template"].format(
            interval=interval
        )
        self.record_mapper = getattr(self, self.data_type_config["record_mapper"])
        self.max_limit_per_call = self.data_type_config["max_limit_per_call"][
            self.interval
        ]
        self.schema_getter = self.data_type_config["schema_getter"]

    def _get_all_futures_exchanges(self) -> List[str]:
        """
        Fetches all futures exchanges from the database using a SQL script.
        Returns a list of exchange internal names.
        """
        try:
            query = self.db_connection._load_sql("get_all_futures_exchanges.sql")
            logger.info("Fetching all futures exchanges from database...")
            results = self.db_connection._execute_query(query, fetch=True)
            if results:
                exchanges = [row[0] for row in results]
                logger.info(f"Found {len(exchanges)} futures exchanges in database.")
                return exchanges
            else:
                logger.warning("No futures exchanges found in database.")
                return []
        except FileNotFoundError:
            logger.error("SQL script 'get_all_futures_exchanges.sql' not found.")
            return []
        except Exception as e:
            logger.error(f"Error fetching all futures exchanges from database: {e}")
            return []

    def _get_futures_instruments_from_db(
        self, exchanges: List[str], instrument_statuses: List[str]
    ) -> List[tuple]:
        """
        Fetches futures instruments for the given exchanges and statuses from the database.
        Returns a list of (exchange_internal_name, mapped_instrument_symbol, last_update_datetime, first_update_datetime, instrument_status) tuples.
        """
        if not exchanges:
            logger.warning("Exchanges list is empty, returning no futures instruments.")
            return []

        try:
            query = self.db_connection._load_sql(
                self.data_type_config["get_instruments_sql"]
            )
            params = (tuple(exchanges), tuple(instrument_statuses))

            logger.info(
                f"Fetching futures instruments for exchanges: {exchanges} with statuses: {instrument_statuses}..."
            )
            results = self.db_connection._execute_query(
                query, params=params, fetch=True
            )
            if results:
                instruments = []
                for row in results:
                    # Dynamically get the last and first update datetimes based on config
                    last_update_dt = ensure_utc_datetime(row[2])
                    first_update_dt = ensure_utc_datetime(row[3])
                    instrument_status = row[4]
                    instruments.append(
                        (
                            row[0],
                            row[1],
                            last_update_dt,
                            first_update_dt,
                            instrument_status,
                        )
                    )
                logger.info(
                    f"Found {len(instruments)} futures instruments in database."
                )
                return instruments
            else:
                logger.warning(
                    "No futures instruments found in database for the given criteria."
                )
                return []
        except FileNotFoundError:
            logger.error(
                f"SQL script '{self.data_type_config['get_instruments_sql']}' not found."
            )
            return []
        except Exception as e:
            logger.error(f"Error fetching futures instruments from database: {e}")
            return []

    def _get_last_ingested_datetime(
        self, market: str, mapped_instrument: str
    ) -> Optional[datetime]:
        """
        Retrieves the latest datetime for a given market and mapped instrument from the database.
        """
        query = f"""
            SELECT MAX(datetime)
            FROM {self.table_name}
            WHERE market = %s AND mapped_instrument = %s;
        """
        try:
            result = self.db_connection._execute_query(
                query, params=(market, mapped_instrument), fetch=True
            )
            if result and result[0] and result[0][0]:
                return result[0][0].replace(tzinfo=timezone.utc)
            return None
        except Exception as e:
            logger.error(
                f"Error getting last ingested datetime for {market}-{mapped_instrument} from {self.table_name}: {e}"
            )
            return None

    def _map_ohlcv_record(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Maps a raw OHLCV API entry to a standardized record."""
        return {
            "datetime": datetime.fromtimestamp(entry["TIMESTAMP"], tz=timezone.utc),
            "market": entry.get("MARKET"),
            "instrument": entry.get("INSTRUMENT"),
            "mapped_instrument": entry.get("MAPPED_INSTRUMENT"),
            "type": entry.get("TYPE"),
            "index_underlying": entry.get("INDEX_UNDERLYING"),
            "quote_currency": entry.get("QUOTE_CURRENCY"),
            "settlement_currency": entry.get("SETTLEMENT_CURRENCY"),
            "contract_currency": entry.get("CONTRACT_CURRENCY"),
            "denomination_type": entry.get("DENOMINATION_TYPE"),
            "open": entry.get("OPEN"),
            "high": entry.get("HIGH"),
            "low": entry.get("LOW"),
            "close": entry.get("CLOSE"),
            "number_of_contracts": entry.get("NUMBER_OF_CONTRACTS"),
            "volume": entry.get("VOLUME"),
            "quote_volume": entry.get("QUOTE_VOLUME"),
            "volume_buy": entry.get("VOLUME_BUY"),
            "quote_volume_buy": entry.get("QUOTE_VOLUME_BUY"),
            "volume_sell": entry.get("VOLUME_SELL"),
            "quote_volume_sell": entry.get("QUOTE_VOLUME_SELL"),
            "volume_unknown": entry.get("VOLUME_UNKNOWN"),
            "quote_volume_unknown": entry.get("QUOTE_VOLUME_UNKNOWN"),
            "total_trades": entry.get("TOTAL_TRADES"),
            "total_trades_buy": entry.get("TOTAL_TRADES_BUY"),
            "total_trades_sell": entry.get("TOTAL_TRADES_SELL"),
            "total_trades_unknown": entry.get("TOTAL_TRADES_UNKNOWN"),
            "first_trade_timestamp": (
                datetime.fromtimestamp(
                    entry.get("FIRST_TRADE_TIMESTAMP"), tz=timezone.utc
                )
                if entry.get("FIRST_TRADE_TIMESTAMP") is not None
                else None
            ),
            "last_trade_timestamp": (
                datetime.fromtimestamp(
                    entry.get("LAST_TRADE_TIMESTAMP"), tz=timezone.utc
                )
                if entry.get("LAST_TRADE_TIMESTAMP") is not None
                else None
            ),
            "first_trade_price": entry.get("FIRST_TRADE_PRICE"),
            "high_trade_price": entry.get("HIGH_TRADE_PRICE"),
            "high_trade_timestamp": (
                datetime.fromtimestamp(
                    entry.get("HIGH_TRADE_TIMESTAMP"), tz=timezone.utc
                )
                if entry.get("HIGH_TRADE_TIMESTAMP") is not None
                else None
            ),
            "low_trade_price": entry.get("LOW_TRADE_PRICE"),
            "low_trade_timestamp": (
                datetime.fromtimestamp(
                    entry.get("LOW_TRADE_TIMESTAMP"), tz=timezone.utc
                )
                if entry.get("LOW_TRADE_TIMESTAMP") is not None
                else None
            ),
            "last_trade_price": entry.get("LAST_TRADE_PRICE"),
            "collected_at": datetime.now(timezone.utc),
        }

    def _map_funding_rate_record(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Maps a raw Funding Rate API entry to a standardized record."""
        return {
            "datetime": datetime.fromtimestamp(entry["TIMESTAMP"], tz=timezone.utc),
            "market": entry.get("MARKET"),
            "instrument": entry.get("INSTRUMENT"),
            "mapped_instrument": entry.get("MAPPED_INSTRUMENT"),
            "type": entry.get("TYPE"),
            "index_underlying": entry.get("INDEX_UNDERLYING"),
            "quote_currency": entry.get("QUOTE_CURRENCY"),
            "settlement_currency": entry.get("SETTLEMENT_CURRENCY"),
            "contract_currency": entry.get("CONTRACT_CURRENCY"),
            "denomination_type": entry.get("DENOMINATION_TYPE"),
            "interval_ms": entry.get("INTERVAL_MS"),
            "open_fr": entry.get("OPEN"),
            "high_fr": entry.get("HIGH"),
            "low_fr": entry.get("LOW"),
            "close_fr": entry.get("CLOSE"),
            "total_funding_rate_updates": entry.get("TOTAL_FUNDING_RATE_UPDATES"),
            "collected_at": datetime.now(timezone.utc),
        }

    def _map_open_interest_record(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Maps a raw Open Interest API entry to a standardized record."""
        return {
            "datetime": datetime.fromtimestamp(entry["TIMESTAMP"], tz=timezone.utc),
            "market": entry.get("MARKET"),
            "instrument": entry.get("INSTRUMENT"),
            "mapped_instrument": entry.get("MAPPED_INSTRUMENT"),
            "type": entry.get("TYPE"),
            "index_underlying": entry.get("INDEX_UNDERLYING"),
            "quote_currency": entry.get("QUOTE_CURRENCY"),
            "settlement_currency": entry.get("SETTLEMENT_CURRENCY"),
            "contract_currency": entry.get("CONTRACT_CURRENCY"),
            "denomination_type": entry.get("DENOMINATION_TYPE"),
            "open_oi_contracts": entry.get("OPEN_SETTLEMENT"),
            "high_oi_contracts": entry.get("HIGH_SETTLEMENT"),
            "low_oi_contracts": entry.get("LOW_SETTLEMENT"),
            "close_oi_contracts": entry.get("CLOSE_SETTLEMENT"),
            "open_oi_quote": entry.get("OPEN_QUOTE"),
            "high_oi_quote": entry.get("HIGH_QUOTE"),
            "low_oi_quote": entry.get("LOW_QUOTE"),
            "close_oi_quote": entry.get("CLOSE_QUOTE"),
            "open_mark_price": entry.get("OPEN_MARK_PRICE"),
            "high_oi_mark_price": entry.get("HIGH_SETTLEMENT_MARK_PRICE"),
            "high_mark_price": entry.get("HIGH_MARK_PRICE"),
            "high_mark_price_oi": entry.get("HIGH_MARK_PRICE_SETTLEMENT"),
            "high_quote_mark_price": entry.get("HIGH_QUOTE_MARK_PRICE"),
            "low_oi_mark_price": entry.get("LOW_SETTLEMENT_MARK_PRICE"),
            "low_mark_price": entry.get("LOW_MARK_PRICE"),
            "low_mark_price_oi": entry.get("LOW_MARK_PRICE_SETTLEMENT"),
            "low_quote_mark_price": entry.get("LOW_QUOTE_MARK_PRICE"),
            "close_mark_price": entry.get("CLOSE_MARK_PRICE"),
            "total_open_interest_updates": entry.get("TOTAL_OPEN_INTEREST_UPDATES"),
            "collected_at": datetime.now(timezone.utc),
        }

    def ingest_data_for_instrument(
        self,
        market: str,
        mapped_instrument: str,
        last_update_datetime: Optional[datetime],
        first_update_datetime: Optional[datetime],
        instrument_status: str,
    ):
        """
        Fetches historical data for a specific futures instrument and ingests it into the database.
        Handles backfilling and live ingestion by paginating through available data.
        """
        last_datetime_in_db = self._get_last_ingested_datetime(
            market, mapped_instrument
        )

        today_utc = datetime.now(timezone.utc)
        end_of_previous_period = get_end_of_previous_period(
            today_utc, map_interval_to_unit(self.interval)
        )

        # Determine the start date for fetching
        if last_datetime_in_db:
            start_date_to_fetch = last_datetime_in_db + timedelta(
                **{map_interval_to_unit(self.interval): 1}
            )
            logger.info(
                f"Continuing ingestion for {mapped_instrument} on {market} from {start_date_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            )
        else:
            if first_update_datetime:
                start_date_to_fetch = first_update_datetime
                logger.info(
                    f"No existing data for {mapped_instrument} on {market}. Backfilling from first update datetime: {start_date_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')}."
                )
            else:
                # Fallback to 2 years ago if first_update_datetime is not available
                two_years_ago = datetime.now(timezone.utc) - timedelta(
                    days=self.max_limit_per_call
                )
                start_date_to_fetch = datetime.combine(
                    two_years_ago.date(), datetime.min.time(), tzinfo=timezone.utc
                )
                logger.info(
                    f"No existing data for {mapped_instrument} on {market} and no first update datetime. Backfilling from {start_date_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')}."
                )

        # Determine the effective end timestamp for fetching
        if instrument_status == "ACTIVE":
            effective_to_ts_dt = end_of_previous_period
        else:
            effective_to_ts_dt = (
                last_update_datetime if last_update_datetime else end_of_previous_period
            )

        current_to_ts = int(effective_to_ts_dt.timestamp())

        while True:
            # Calculate the number of periods between start_date_to_fetch and effective_to_ts_dt
            if self.interval == "1d":
                delta_periods = (
                    effective_to_ts_dt.date() - start_date_to_fetch.date()
                ).days
            elif self.interval == "1h":
                delta_periods = int(
                    (effective_to_ts_dt - start_date_to_fetch).total_seconds() / 3600
                )
            elif self.interval == "1m":
                delta_periods = int(
                    (effective_to_ts_dt - start_date_to_fetch).total_seconds() / 60
                )
            else:
                raise ValueError(
                    f"Unsupported interval for delta_periods: {self.interval}"
                )

            if delta_periods < 0:
                logger.info(
                    f"No new data to fetch for {mapped_instrument} on {market}. Already up to date or future date requested."
                )
                break

            limit = min(delta_periods + 1, self.max_limit_per_call)

            batch_to_ts_dt = start_date_to_fetch + timedelta(
                **{map_interval_to_unit(self.interval): limit - 1}
            )

            batch_to_ts = int(batch_to_ts_dt.timestamp())
            if batch_to_ts > current_to_ts:
                batch_to_ts = current_to_ts

            logger.info(
                f"Fetching batch for {mapped_instrument} on {market} from {start_date_to_fetch.strftime('%Y-%m-%d %H:%M:%S UTC')} to {datetime.fromtimestamp(batch_to_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} (limit={limit})."
            )

            try:
                api_call_method = getattr(
                    self.futures_api_client, self.data_type_config["api_method"]
                )
                data = api_call_method(
                    interval=map_interval_to_unit(self.interval),
                    market=market,
                    instrument=mapped_instrument,
                    to_ts=batch_to_ts,
                    limit=limit,
                )

                if data and data.get("Data"):
                    records = []
                    for entry in data["Data"]:
                        entry_datetime = datetime.fromtimestamp(
                            entry["TIMESTAMP"], tz=timezone.utc
                        )
                        if (
                            not last_datetime_in_db
                            or entry_datetime > last_datetime_in_db
                        ):
                            records.append(self.record_mapper(entry))

                    if records:
                        schema = self.schema_getter() if self.schema_getter else None
                        self.db_connection.insert_dataframe(
                            records, self.table_name, replace=True, schema=schema
                        )
                        logger.info(
                            f"Successfully ingested {len(records)} {self.data_type} records for {mapped_instrument} on {market}."
                        )
                        last_datetime_in_db = max(records, key=lambda x: x["datetime"])[
                            "datetime"
                        ]
                    else:
                        logger.info(
                            f"No new {self.data_type} data to ingest for {mapped_instrument} on {market} in this batch."
                        )

                    # Always advance start_date_to_fetch to avoid re-fetching the same data
                    start_date_to_fetch = batch_to_ts_dt + timedelta(
                        **{map_interval_to_unit(self.interval): 1}
                    )

                else:
                    logger.warning(
                        f"No data received for {mapped_instrument} on {market} for this batch."
                    )

                # Break if start_date_to_fetch has passed the effective_to_ts_dt
                if start_date_to_fetch > effective_to_ts_dt:
                    logger.info(
                        f"Finished ingesting data for {mapped_instrument} on {market}. Reached effective_to_ts_dt."
                    )
                    break
            except Exception as e:
                logger.error(
                    f"Error ingesting {self.data_type} data for {mapped_instrument} on {market}: {e}"
                )
                break

            # Prepare for the next batch
            start_date_to_fetch = datetime.fromtimestamp(
                batch_to_ts, tz=timezone.utc
            ) + timedelta(**{map_interval_to_unit(self.interval): 1})

            if start_date_to_fetch > today_utc:
                break

            if last_datetime_in_db and start_date_to_fetch <= last_datetime_in_db:
                logger.info(
                    f"Reached end of available new data for {mapped_instrument} on {market}."
                )
                break

    def run_ingestion(
        self,
        exchanges: Optional[List[str]],
        instruments: Optional[List[str]],
        instrument_statuses: List[str],
        deduplicate: bool = False,
    ):
        """
        Main method to run the data ingestion process.
        """
        logger.info(
            f"Attempting to ingest {self.data_type} futures data for interval {self.interval}..."
        )
        record_rate_limit_status(
            f"ingest_{self.data_type}_futures_{self.interval}", "pre"
        )

        # Determine exchanges to process
        if exchanges:
            exchanges_to_process = [e.strip() for e in exchanges]
            logger.info(f"Processing user-specified exchanges: {exchanges_to_process}")
        else:
            exchanges_to_process = self._get_all_futures_exchanges()
            if not exchanges_to_process:
                logger.error(
                    "Failed to retrieve futures exchanges from database. Aborting."
                )
                return

        # Determine instruments to process
        instruments_to_process = []
        if instruments:
            user_specified_instruments = [
                instrument.strip() for instrument in instruments
            ]
            for exchange in exchanges_to_process:
                fetched_instruments = self._get_futures_instruments_from_db(
                    [exchange], instrument_statuses
                )
                for inst in fetched_instruments:
                    if inst[1] in user_specified_instruments:
                        instruments_to_process.append(inst)

            if not instruments_to_process:
                logger.error(
                    "No user-specified futures instruments found in the database for the given criteria. Aborting."
                )
                return
            logger.info(
                f"Processing user-specified instruments: {instruments_to_process}"
            )
        else:
            instruments_to_process = self._get_futures_instruments_from_db(
                exchanges_to_process, instrument_statuses
            )
            if not instruments_to_process:
                logger.error(
                    "No futures instruments found for the given criteria. Aborting."
                )
                return

        for (
            market,
            mapped_instrument,
            last_update_dt,
            first_update_dt,
            instrument_status,
        ) in instruments_to_process:
            self.ingest_data_for_instrument(
                market,
                mapped_instrument,
                last_update_dt,
                first_update_dt,
                instrument_status,
            )
            time.sleep(0.1)

        # Add deduplication step after ingestion
        key_cols = ["datetime", "market", "mapped_instrument"]
        latest_col = self.data_type_config["deduplicate_latest_col"]
        if deduplicate:
            logger.info(f"De-duplicating {self.table_name}...")
            deduplicate_table(self.db_connection, self.table_name, key_cols, latest_col)
            logger.info("De-duplication Complete")

        self.db_connection.close_connection()
        logger.info(
            f"{self.data_type} futures data ingestion for interval {self.interval} completed."
        )
        record_rate_limit_status(
            f"ingest_{self.data_type}_futures_{self.interval}", "post"
        )
