import os

SWARM_MANIFEST = {
    # ... (Batches 1-12 preserved) ...
    "batch_01_foundation": [("grass_bandwidth", "websocket"), ("helium_iot", "chain"), ("helium_mobile", "chain"), ("hivemapper_dash", "api"), ("render_gpu", "api")],
    "batch_02_physical_sky": [("wingbits_adsb", "api"), ("weatherxm_local", "api"), ("geodnet_space", "api"), ("purpleair_sensor", "api"), ("sensor_community", "json")],
    "batch_03_physical_grid": [("ercot_texas", "scraper"), ("caiso_california", "api"), ("eia_gas_storage", "api"), ("eia_oil_inventory", "api"), ("smart_meter_amr", "sdr")],
    "batch_04_financial": [("solana_fees", "rpc"), ("birdeye_whales", "api"), ("coingecko_vol", "api"), ("deribit_options", "api"), ("binance_orderbook", "websocket")],
    "batch_05_social_alpha": [("twitter_cashtags", "scraper"), ("discord_sentiment", "bot"), ("github_commits", "api"), ("shopify_inventory", "scraper"), ("silencio_noise", "proxy")],
    "batch_06_mobility": [("dimo_vehicle", "api"), ("natix_traffic", "api"), ("waze_incidents", "scraper"), ("tpms_traffic", "sdr"), ("rail_aei_tags", "sdr")],
    "batch_07_deep_helius": [("helius_das_mints", "rpc"), ("helius_priority_fees", "rpc"), ("helius_smart_money", "webhook"), ("helius_nft_metadata", "api"), ("helius_tps_variance", "rpc")],
    "batch_08_deep_defi": [("birdeye_token_security", "api"), ("birdeye_wallet_history", "api"), ("birdeye_new_listings", "api"), ("birdeye_liquidity_burn", "api"), ("birdeye_trending_flow", "api")],
    "batch_09_deep_market": [("coingecko_dev_activity", "api"), ("coingecko_exchange_vol", "api"), ("coingecko_global_dominance", "api"), ("coingecko_derivatives", "api"), ("coingecko_category_flow", "api")],
    "batch_10_deep_physical": [("purpleair_pm25_industrial", "api"), ("wingbits_squawk_codes", "api"), ("weatherxm_solar_irradiance", "api"), ("dimo_battery_health", "api"), ("hivemapper_road_class", "api")],
    "batch_11_deep_social": [("reddit_sub_growth", "scraper"), ("discord_active_users", "bot"), ("twitter_list_sentiment", "scraper"), ("gov_contract_awards", "scraper"), ("job_board_listings", "scraper")],
    "batch_12_firehose": [("helius_global_stream", "websocket"), ("birdeye_price_stream", "websocket"), ("birdeye_trade_stream", "websocket"), ("jito_mempool_sniper", "websocket"), ("binance_l2_depth", "websocket")],
    # ... (Batches 15-26 assumed present) ...
    
    # --- NEW: BATCH 27 - GLOBAL FIREHOSE ---
    "batch_27_global_firehose": [
        ("polygon_stocks_stream", "websocket"),
        ("polygon_forex_stream", "websocket"),
        ("polygon_crypto_stream", "websocket"),
        ("alpaca_market_stream", "websocket"),
        ("twelvedata_indices", "websocket")
    ]
}

BASE_TEMPLATE = """import asyncio
import json
import logging
import os
import sys
import time
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from collectors.base import KairosCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("{class_name}")

class {class_name}(KairosCollector):
    def __init__(self):
        super().__init__("{project_name}")

    def collect(self):
        logger.info("📡 STARTED: {project_name}")
        while True:
            time.sleep(3600)

if __name__ == "__main__":
    agent = {class_name}()
    agent.collect()
"""

def build_swarm():
    base_path = "collectors"
    for batch, targets in SWARM_MANIFEST.items():
        batch_dir = os.path.join(base_path, batch)
        os.makedirs(batch_dir, exist_ok=True)
        with open(os.path.join(batch_dir, "__init__.py"), "w") as f: f.write("")
        for project, source in targets:
            file_name = f"{project}.py"
            file_path = os.path.join(batch_dir, file_name)
            class_name = "".join(x.title() for x in project.split("_"))
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write(BASE_TEMPLATE.format(class_name=class_name, project_name=project, source_type=source))
                print(f"✅ Generated: {file_path}")

if __name__ == "__main__":
    build_swarm()
