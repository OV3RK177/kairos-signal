"""
Kairos Signal Collector for: Grass (Deep Data)
Version: 3.1 (Auth Fix + Helius Debug)
"""

import os
import requests
import logging
from datetime import datetime
import clickhouse_connect
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- CONFIGURATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Keys
GRASS_MINT_ADDRESS = "GrsAkJuP6DRbU37D2HgaNrABsS4Pc3724d6nGy5X3b3h"
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
# Clean the token just in case
raw_token = os.getenv("GRASS_AUTH_TOKEN", "").strip()
# Ensure Bearer prefix exists
GRASS_AUTH_TOKEN = raw_token if raw_token.startswith("Bearer ") else f"Bearer {raw_token}"

GRASS_API_ENDPOINT = "https://api.grass.io/retrieveUser" 
HELIUS_REST_URL = f"https://api.helius.xyz/v0/token-metadata?api-key={HELIUS_API_KEY}"

# DB
DB_HOST = 'localhost'
DB_PORT = 8123
DB_USER = 'default'
DB_PASS = 'kairos'

class GrassCollector:
    def __init__(self):
        self.slug = "grass"
        self.session = self._init_session()
        self.client = self._init_db()

    def _init_session(self):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session

    def _init_db(self):
        try:
            client = clickhouse_connect.get_client(host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASS)
            client.command('SELECT 1')
            return client
        except Exception as e:
            logging.critical(f"DB Fail: {e}")
            raise

    def fetch_operational(self):
        # Header construction with explicit Bearer
        headers = {
            "Authorization": GRASS_AUTH_TOKEN, 
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = self.session.get(GRASS_API_ENDPOINT, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if "result" in data and "data" in data["result"]:
                return data["result"]["data"]
            logging.error(f"Grass Unexpected Format: {data.keys()}")
        except Exception as e:
            logging.error(f"Grass Fetch Error: {e}")
        return None

    def fetch_financial(self):
        if not HELIUS_API_KEY: return None
        try:
            resp = self.session.post(HELIUS_REST_URL, json={"mintAccounts": [GRASS_MINT_ADDRESS]}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data and isinstance(data, list):
                return data[0]
            logging.error(f"Helius Unexpected Format: {data}")
        except Exception as e:
            logging.error(f"Helius Fetch Error: {e}")
        return None

    def run(self):
        logging.info("Starting Collection...")
        op_data = self.fetch_operational()
        fin_data = self.fetch_financial()
        
        batch = []
        ts = datetime.now()

        # 1. Process Operational
        if op_data:
            # logging.info(f"Grass Data: {op_data.keys()}") # Debug if needed
            if "totalPoints" in op_data:
                batch.append([ts, self.slug, "total_points", float(op_data["totalPoints"])])
            if "totalUptime" in op_data:
                uptime = float(op_data["totalUptime"])
                batch.append([ts, self.slug, "total_uptime_ms", uptime])
                batch.append([ts, self.slug, "total_uptime_hours", uptime / 1000 / 3600])
        
        # 2. Process Financial
        if fin_data:
            try:
                # Safe navigation to avoid NoneType crash
                on_chain = fin_data.get('onChainAccountInfo') or {}
                account_info = on_chain.get('accountInfo') or {}
                data_obj = account_info.get('data') or {}
                parsed = data_obj.get('parsed') or {}
                info = parsed.get('info') or {}
                
                supply = info.get('supply')
                decimals = info.get('decimals')
                
                if supply is not None and decimals is not None:
                    real_supply = float(supply) / (10 ** int(decimals))
                    batch.append([ts, self.slug, "total_supply", real_supply])
                else:
                    logging.warning(f"Helius Missing Supply/Decimals. Dump: {fin_data}")
            except Exception as e:
                logging.error(f"Helius Parse Error: {e}")

        # 3. Insert
        if batch:
            self.client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
            logging.info(f"SUCCESS: Inserted {len(batch)} metrics.")
            for row in batch:
                print(f" > {row[2]}: {row[3]}")
        else:
            logging.warning("Zero data collected.")

if __name__ == "__main__":
    GrassCollector().run()
