import os
import logging
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from src.data_api.asset_api_client import CcdataAssetApiClient
from src.db.connection import DbConnectionManager
from src.logger_config import setup_logger
from src.db.utils import to_mysql_datetime, deduplicate_table
from src.rate_limit_tracker import record_rate_limit_status

# Load environment variables from .env file
load_dotenv()

# Configure logging using the centralized setup
script_name = os.path.splitext(os.path.basename(__file__))[0]
log_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    f"{script_name}.log",
)
logger = setup_logger(__name__, log_to_console=True, log_file_path=log_file_path)


def fetch_asset_data(asset_client, page_size=100):
    """Fetch all asset data from the API, paginated."""
    page = 1
    assets_data = []
    total_assets = None
    while True:
        logger.info(f"Fetching asset top list - Page: {page}")
        response = asset_client.get_top_list_general(
            page=page,
            page_size=page_size,
            groups=[
                "ID",
                "BASIC",
                "CLASSIFICATION",
                "DESCRIPTION_SUMMARY",
                "PRICE",
                "MKT_CAP",
                "VOLUME",
            ],
        )
        if not response or "Data" not in response:
            break
        page_assets = response["Data"]
        assets_data.extend(page_assets)
        if total_assets is None:
            total_assets = response.get("TotalCount", len(page_assets))
        if len(page_assets) < page_size or (page * page_size) >= total_assets:
            break
        page += 1
    logger.info(f"Fetched {len(assets_data)} assets.")
    return assets_data


def transform_asset_data(assets_data):
    """Transform raw asset data into rows for each table."""
    now = datetime.now(timezone.utc)
    assets_to_insert = []
    asset_alt_ids_to_insert = []
    asset_industries_to_insert = []
    asset_consensus_mechanisms_to_insert = []
    asset_consensus_algorithm_types_to_insert = []
    asset_hashing_algorithm_types_to_insert = []
    asset_previous_symbols_to_insert = []
    asset_market_data_to_insert = []

    for asset in assets_data:
        current_ts = now

        # cc_assets
        assets_to_insert.append(
            {
                "asset_id": asset.get("ID"),
                "symbol": asset.get("SYMBOL"),
                "name": asset.get("NAME"),
                "uri": asset.get("URI"),
                "asset_type": asset.get("ASSET_TYPE"),
                "cc_internal_type": asset.get("TYPE"),
                "id_legacy": asset.get("ID_LEGACY"),
                "id_parent_asset": asset.get("ID_PARENT_ASSET"),
                "id_asset_issuer": asset.get("ID_ASSET_ISSUER"),
                "asset_issuer_name": asset.get("ASSET_ISSUER_NAME"),
                "parent_asset_symbol": asset.get("PARENT_ASSET_SYMBOL"),
                "cc_created_on": to_mysql_datetime(asset.get("CREATED_ON")),
                "cc_updated_on": to_mysql_datetime(asset.get("UPDATED_ON")),
                "public_notice": asset.get("PUBLIC_NOTICE"),
                "logo_url": asset.get("LOGO_URL"),
                "launch_date": to_mysql_datetime(asset.get("LAUNCH_DATE")),
                "description_summary": asset.get("ASSET_DESCRIPTION_SUMMARY"),
                "decimal_points": asset.get("ASSET_DECIMAL_POINTS"),
                "symbol_glyph": asset.get("ASSET_SYMBOL_GLYPH"),
                "created_at": to_mysql_datetime(current_ts),
                "updated_at": to_mysql_datetime(current_ts),
            }
        )

        # cc_asset_alternative_ids
        for alt_id in asset.get("ASSET_ALTERNATIVE_IDS", []) or []:
            asset_alt_ids_to_insert.append(
                {
                    "asset_id": asset.get("ID"),
                    "id_source_name": alt_id.get("NAME"),
                    "alternative_id_value": alt_id.get("ID"),
                    "created_at": to_mysql_datetime(current_ts),
                    "updated_at": to_mysql_datetime(current_ts),
                }
            )

        # cc_asset_industries_map
        for industry in asset.get("ASSET_INDUSTRIES", []) or []:
            asset_industries_to_insert.append(
                {
                    "asset_id": asset.get("ID"),
                    "industry_name": industry.get("ASSET_INDUSTRY"),
                    "justification": industry.get("JUSTIFICATION"),
                    "created_at": to_mysql_datetime(current_ts),
                    "updated_at": to_mysql_datetime(current_ts),
                }
            )

        # cc_asset_consensus_mechanisms_map
        for mechanism in asset.get("CONSENSUS_MECHANISMS", []) or []:
            asset_consensus_mechanisms_to_insert.append(
                {
                    "asset_id": asset.get("ID"),
                    "mechanism_name": mechanism.get("NAME"),
                    "created_at": to_mysql_datetime(current_ts),
                    "updated_at": to_mysql_datetime(current_ts),
                }
            )

        # cc_asset_consensus_algorithm_types_map
        for algo_type in asset.get("CONSENSUS_ALGORITHM_TYPES", []) or []:
            asset_consensus_algorithm_types_to_insert.append(
                {
                    "asset_id": asset.get("ID"),
                    "algorithm_name": algo_type.get("NAME"),
                    "created_at": to_mysql_datetime(current_ts),
                    "updated_at": to_mysql_datetime(current_ts),
                }
            )

        # cc_asset_hashing_algorithm_types_map
        for hashing_algo in asset.get("HASHING_ALGORITHM_TYPES", []) or []:
            asset_hashing_algorithm_types_to_insert.append(
                {
                    "asset_id": asset.get("ID"),
                    "algorithm_name": hashing_algo.get("NAME"),
                    "created_at": to_mysql_datetime(current_ts),
                    "updated_at": to_mysql_datetime(current_ts),
                }
            )

        # cc_asset_previous_symbols_map
        for prev_symbol in asset.get("PREVIOUS_ASSET_SYMBOLS", []) or []:
            if isinstance(prev_symbol, dict):
                symbol_val = prev_symbol.get("SYMBOL") or json.dumps(
                    prev_symbol, ensure_ascii=False
                )
            elif isinstance(prev_symbol, list):
                symbol_val = json.dumps(prev_symbol, ensure_ascii=False)
            else:
                symbol_val = str(prev_symbol)
            asset_previous_symbols_to_insert.append(
                {
                    "asset_id": asset.get("ID"),
                    "previous_symbol": symbol_val,
                    "created_at": to_mysql_datetime(current_ts),
                    "updated_at": to_mysql_datetime(current_ts),
                }
            )

        # cc_asset_market_data (append only)
        price_usd_last_update_ts = asset.get("PRICE_USD_LAST_UPDATE_TS")
        if price_usd_last_update_ts:
            snapshot_ts = datetime.fromtimestamp(
                price_usd_last_update_ts, tz=timezone.utc
            )
        else:
            snapshot_ts = None
        asset_market_data_to_insert.append(
            {
                "asset_id": asset.get("ID"),
                "symbol": asset.get("SYMBOL"),
                "price_usd": asset.get("PRICE_USD"),
                "price_usd_last_update_ts": to_mysql_datetime(snapshot_ts),
                "created_at": to_mysql_datetime(current_ts),
                "updated_at": to_mysql_datetime(current_ts),
            }
        )

    return {
        "assets": assets_to_insert,
        "alt_ids": asset_alt_ids_to_insert,
        "industries": asset_industries_to_insert,
        "consensus_mechanisms": asset_consensus_mechanisms_to_insert,
        "consensus_algorithm_types": asset_consensus_algorithm_types_to_insert,
        "hashing_algorithm_types": asset_hashing_algorithm_types_to_insert,
        "previous_symbols": asset_previous_symbols_to_insert,
        "market_data": asset_market_data_to_insert,
    }


def insert_asset_data(db_manager, data):
    """Insert transformed data into the database."""
    if data["assets"]:
        db_manager.insert_dataframe(data["assets"], "market.cc_assets", replace=True)
    if data["alt_ids"]:
        db_manager.insert_dataframe(
            data["alt_ids"], "market.cc_asset_alternative_ids", replace=True
        )
    if data["industries"]:
        db_manager.insert_dataframe(
            data["industries"], "market.cc_asset_industries_map", replace=True
        )
    if data["consensus_mechanisms"]:
        db_manager.insert_dataframe(
            data["consensus_mechanisms"],
            "market.cc_asset_consensus_mechanisms_map",
            replace=True,
        )
    if data["consensus_algorithm_types"]:
        db_manager.insert_dataframe(
            data["consensus_algorithm_types"],
            "market.cc_asset_consensus_algorithm_types_map",
            replace=True,
        )
    if data["hashing_algorithm_types"]:
        db_manager.insert_dataframe(
            data["hashing_algorithm_types"],
            "market.cc_asset_hashing_algorithm_types_map",
            replace=True,
        )
    if data["previous_symbols"]:
        db_manager.insert_dataframe(
            data["previous_symbols"],
            "market.cc_asset_previous_symbols_map",
            replace=True,
        )
    if data["market_data"]:
        db_manager.insert_dataframe(
            data["market_data"], "market.cc_asset_market_data", replace=False
        )


def deduplicate_all_tables(db_manager):
    """Deduplicate all relevant tables after ingestion."""
    deduplicate_table(db_manager, "market.cc_assets", ["asset_id"], "updated_at")
    deduplicate_table(
        db_manager,
        "market.cc_asset_alternative_ids",
        ["asset_id", "id_source_name"],
        "updated_at",
    )
    deduplicate_table(
        db_manager,
        "market.cc_asset_industries_map",
        ["asset_id", "industry_name"],
        "updated_at",
    )
    deduplicate_table(
        db_manager,
        "market.cc_asset_consensus_mechanisms_map",
        ["asset_id", "mechanism_name"],
        "updated_at",
    )
    deduplicate_table(
        db_manager,
        "market.cc_asset_consensus_algorithm_types_map",
        ["asset_id", "algorithm_name"],
        "updated_at",
    )
    deduplicate_table(
        db_manager,
        "market.cc_asset_hashing_algorithm_types_map",
        ["asset_id", "algorithm_name"],
        "updated_at",
    )
    deduplicate_table(
        db_manager,
        "market.cc_asset_previous_symbols_map",
        ["asset_id", "previous_symbol"],
        "updated_at",
    )


def ingest_asset_data():
    """Orchestrate the asset data ingestion pipeline."""
    logger.info("Starting asset data ingestion process.")
    record_rate_limit_status("ingest_asset_data", "pre")

    api_key = os.getenv("CCDATA_API_KEY")
    if not api_key:
        logger.error("CCDATA_API_KEY environment variable not set. Exiting.")
        return

    asset_client = CcdataAssetApiClient(api_key=api_key)
    db_manager = None

    try:
        db_manager = DbConnectionManager()
        assets_data = fetch_asset_data(asset_client)
        transformed = transform_asset_data(assets_data)
        insert_asset_data(db_manager, transformed)
    except Exception as e:
        logger.exception(f"An error occurred during asset data ingestion: {e}")
    finally:
        if db_manager:
            deduplicate_all_tables(db_manager)
            db_manager.close_connection()
        logger.info("Asset data ingestion process finished.")
    record_rate_limit_status("ingest_asset_data", "post")


if __name__ == "__main__":
    logger.info("Attempting to ingest asset data...")
    # ingest_asset_data()
    db_manager = DbConnectionManager()
    deduplicate_all_tables(db_manager=db_manager)
