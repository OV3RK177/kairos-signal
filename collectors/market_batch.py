import requests
import logging
from datetime import datetime
from .base import BaseCollector
from key_manager import key_manager
from config.mappings import SOLANA_MINTS

BASE_URL = "https://public-api.birdeye.so/defi/price"

class MarketBatchCollector(BaseCollector):
    def __init__(self):
        super().__init__("market_batch")

    def fetch_price(self, slug, address):
        api_key = key_manager.get_next("birdeye")
        if not api_key: return None
        
        headers = {
            "X-API-KEY": api_key,
            "accept": "application/json",
            "x-chain": "solana"
        }
        
        ts = datetime.now()
        try:
            url = f"{BASE_URL}?address={address}"
            resp = requests.get(url, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    price = data.get("data", {}).get("value")
                    if price:
                        print(f" > {slug}: ${price}")
                        return [ts, slug, "price_usd", float(price)]
            else:
                self.log.warning(f"Birdeye {slug}: {resp.status_code}")
                
        except Exception as e:
            self.log.error(f"Price Error {slug}: {e}")
        return None

    def run(self):
        self.log.info("Running Market Sweep...")
        batch = []
        # Use the verified SOLANA_MINTS from mappings
        for slug, addr in SOLANA_MINTS.items():
            row = self.fetch_price(slug, addr)
            if row: batch.append(row)
        
        self.insert_batch(batch)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    MarketBatchCollector().run()
