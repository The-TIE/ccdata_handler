import os
import difflib
from datetime import datetime, timezone
from src.db.connection import DbConnectionManager
from src.db.utils import deduplicate_table
from src.logger_config import setup_logger

# Configure logging using the centralized setup
script_name = os.path.splitext(os.path.basename(__file__))[0]
log_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    f"{script_name}.log",
)
logger = setup_logger(__name__, log_to_console=True, log_file_path=log_file_path)

def normalize(s):
    return s.lower().replace(" ", "").replace("-", "").replace("_", "") if s else ""

def map_assets_to_coin_uid(
    project_assets,  # List of dicts from market.cc_assets + alt_ids
    coins,           # List of dicts from production.coins
    min_fuzzy_ratio=0.85
):
    cg_to_uid = {c.get("coingecko_id"): c["coin_uid"] for c in coins if c.get("coingecko_id")}
    cmc_to_uid = {c.get("coinmarketcap_id"): c["coin_uid"] for c in coins if c.get("coinmarketcap_id")}
    ticker_to_uid = {c.get("ticker"): c["coin_uid"] for c in coins if c.get("ticker")}
    name_to_uid = {normalize(c.get("name")): c["coin_uid"] for c in coins if c.get("name")}

    results = []
    for asset in project_assets:
        asset_id = asset.get("asset_id")
        symbol = asset.get("symbol")
        name = asset.get("name")
        alt_ids = asset.get("alt_ids", {})
        cg_id = alt_ids.get("cg_id")
        cmc_id = alt_ids.get("cmc_id")

        # 1. Try direct external ID match
        if cg_id and cg_id in cg_to_uid:
            results.append({
                "asset_id": asset_id,
                "symbol": symbol,
                "coin_uid": cg_to_uid[cg_id],
                "match_type": "coingecko_id",
                "match_score": 1.0,
                "mapped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
            continue
        if cmc_id and cmc_id in cmc_to_uid:
            results.append({
                "asset_id": asset_id,
                "symbol": symbol,
                "coin_uid": cmc_to_uid[cmc_id],
                "match_type": "coinmarketcap_id",
                "match_score": 1.0,
                "mapped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
            continue

        # 2. Try symbol match
        if symbol and symbol in ticker_to_uid:
            results.append({
                "asset_id": asset_id,
                "symbol": symbol,
                "coin_uid": ticker_to_uid[symbol],
                "match_type": "symbol",
                "match_score": 1.0,
                "mapped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
            continue

        # 3. Try name match (normalized)
        norm_name = normalize(name)
        if norm_name and norm_name in name_to_uid:
            results.append({
                "asset_id": asset_id,
                "symbol": symbol,
                "coin_uid": name_to_uid[norm_name],
                "match_type": "name",
                "match_score": 1.0,
                "mapped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
            continue

        # 4. Fuzzy match on name
        best_score = 0
        best_uid = None
        for coin in coins:
            coin_name = coin.get("name")
            if not coin_name:
                continue
            score = difflib.SequenceMatcher(None, norm_name, normalize(coin_name)).ratio()
            if score > best_score:
                best_score = score
                best_uid = coin["coin_uid"]
        if best_score >= min_fuzzy_ratio:
            results.append({
                "asset_id": asset_id,
                "symbol": symbol,
                "coin_uid": best_uid,
                "match_type": "fuzzy_name",
                "match_score": best_score,
                "mapped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            results.append({
                "asset_id": asset_id,
                "symbol": symbol,
                "coin_uid": None,
                "match_type": "unmatched",
                "match_score": best_score,
                "mapped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
    return results

def fetch_assets_and_alt_ids(db):
    # Fetch assets
    asset_rows = db._execute_query(
        "SELECT asset_id, symbol, name FROM market.cc_assets", fetch=True
    )
    assets = {row[0]: {"asset_id": row[0], "symbol": row[1], "name": row[2]} for row in asset_rows}
    # Fetch alt ids
    alt_id_rows = db._execute_query(
        "SELECT asset_id, cg_id, cmc_id FROM market.cc_asset_alternative_ids", fetch=True
    )
    for row in alt_id_rows:
        asset_id, cg_id, cmc_id = row
        if asset_id in assets:
            assets[asset_id]["alt_ids"] = {"cg_id": cg_id, "cmc_id": cmc_id}
    # Fill missing alt_ids
    for asset in assets.values():
        if "alt_ids" not in asset:
            asset["alt_ids"] = {}
    return list(assets.values())

def fetch_coins(db):
    coin_rows = db._execute_query(
        "SELECT coin_uid, ticker, name, coingecko_id, coinmarketcap_id FROM production.coins", fetch=True
    )
    coins = []
    for row in coin_rows:
        coins.append({
            "coin_uid": row[0],
            "ticker": row[1],
            "name": row[2],
            "coingecko_id": row[3],
            "coinmarketcap_id": row[4]
        })
    return coins

def main():
    logger.info("Starting asset-to-coin_uid mapping process.")
    db = DbConnectionManager()
    try:
        logger.info("Fetching project assets and alt IDs from market.cc_assets and market.cc_asset_alternative_ids...")
        project_assets = fetch_assets_and_alt_ids(db)
        logger.info(f"Fetched {len(project_assets)} project assets.")

        logger.info("Fetching coins from production.coins...")
        coins = fetch_coins(db)
        logger.info(f"Fetched {len(coins)} coins from production.coins.")

        logger.info("Performing asset-to-coin_uid mapping...")
        mapping = map_assets_to_coin_uid(project_assets, coins)
        mapped_count = sum(1 for row in mapping if row["coin_uid"])
        unmatched_count = sum(1 for row in mapping if not row["coin_uid"])
        logger.info(f"Mapping complete. {mapped_count} assets mapped, {unmatched_count} unmatched.")

        # Only insert mappings with a coin_uid
        to_insert = [row for row in mapping if row["coin_uid"]]
        if to_insert:
            logger.info(f"Inserting {len(to_insert)} mappings into market.cc_asset_coin_uid_map...")
            db.insert_dataframe(to_insert, "market.cc_asset_coin_uid_map", replace=True)
            # logger.info("Deduplicating market.cc_asset_coin_uid_map...")
            # deduplicate_table(db, "market.cc_asset_coin_uid_map", ["asset_id"], "mapped_at")
            # logger.info("Deduplication complete.")
        else:
            logger.warning("No mappings found to insert.")
    except Exception as e:
        logger.exception(f"An error occurred during asset-to-coin_uid mapping: {e}")
    finally:
        db.close_connection()
        logger.info("Asset-to-coin_uid mapping process finished.")

if __name__ == "__main__":
    main()