import requests
import logging
import time
from datetime import datetime
from .base import BaseCollector
from key_manager import key_manager
from config.limits import RATE_LIMITS
from config.mappings import SOLANA_MINTS

class SolanaBatchCollector(BaseCollector):
    def __init__(self):
        super().__init__("solana_batch")
        self.session = requests.Session()
        # YOUR DEDICATED ENDPOINT
        self.rpc_url = "https://moina-y1zh44-fast-mainnet.helius-rpc.com"

    def get_asset_das(self, slug, mint):
        metrics = []
        ts = datetime.now()
        
        # DAS API Payload
        payload = {
            "jsonrpc": "2.0",
            "id": "kairos-swarmlink",
            "method": "getAsset",
            "params": {
                "id": mint
            }
        }
        
        try:
            # Using your dedicated URL directly (No extra API key param needed usually for these subdomains)
            resp = self.session.post(self.rpc_url, json=payload, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json().get('result', {})
                
                # 1. Token Info (Supply)
                token_info = data.get('token_info', {})
                supply = token_info.get('supply')
                decimals = token_info.get('decimals')
                
                if supply and decimals:
                    real_supply = float(supply) / (10 ** int(decimals))
                    metrics.append([ts, slug, "onchain_supply", real_supply])
                    
                    # Price often comes in DAS enriched data
                    price_info = token_info.get('price_info', {})
                    price = price_info.get('price_per_token')
                    if price:
                         metrics.append([ts, slug, "helius_price", float(price)])
                         print(f" > {slug}: ${price:.2f} (Supply: {real_supply:,.0f})")
                    else:
                         print(f" > {slug}: Supply {real_supply:,.0f}")

            else:
                self.log.warning(f"Helius Error {slug}: {resp.status_code}")
                
        except Exception as e:
            self.log.error(f"Error {slug}: {e}")
            
        return metrics

    def run(self):
        self.log.info(f"Starting Solana Forensics (Target: {self.rpc_url[:20]}...)...")
        total_batch = []
        
        for slug, mint in SOLANA_MINTS.items():
            # Helius dedicated usually handles higher rates, but we keep it safe
            time.sleep(0.2) 
            data = self.get_asset_das(slug, mint)
            total_batch.extend(data)
            
        self.insert_batch(total_batch)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    SolanaBatchCollector().run()
