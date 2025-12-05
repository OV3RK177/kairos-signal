import requests
import logging
import time
from datetime import datetime
from .base import BaseCollector
from key_manager import key_manager
from config.limits import RATE_LIMITS

# TARGETS (The Hit List)
TARGETS = {
    "helium": "hutyX5Y9u8rogzXBJ28Y1nazBv1s8tq7e9b4Q3jE2",
    "hivemapper": "4vMsoUT2BWatFweudnQM1xedRLfJgJ7hswhcpz4xgBTy",
    "render": "rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof",
    "shdw_drive": "2e1wdyNhfsgM2uyHYmhqkhDwiyGe1saE7E5x5X8Q",
}

class SolanaBatchCollector(BaseCollector):
    def __init__(self):
        super().__init__("solana_batch")
        self.session = requests.Session()

    def get_onchain_activity(self, slug, program_id):
        # SWARM: Rotate Key
        api_key = key_manager.get_next("helius")
        if not api_key: return []

        url = f"https://api.helius.xyz/v0/token-metadata?api-key={api_key}"
        metrics = []
        ts = datetime.now()
        
        try:
            resp = self.session.post(url, json={"mintAccounts": [program_id]}, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list):
                    info = data[0].get('onChainAccountInfo', {}).get('accountInfo', {}).get('data', {}).get('parsed', {}).get('info', {})
                    
                    supply = info.get('supply')
                    decimals = info.get('decimals')
                    if supply and decimals:
                        val = float(supply) / (10 ** int(decimals))
                        metrics.append([ts, slug, "onchain_supply", val])
                        # Alive signal
                        metrics.append([ts, slug, "contract_responsive", 1.0])
                        print(f" > {slug}: Supply {val:,.0f}")
            else:
                self.log.warning(f"{slug}: HTTP {resp.status_code}")

        except Exception as e:
            self.log.error(f"Error {slug}: {e}")
            
        return metrics

    def run(self):
        self.log.info(f"Starting Swarm Batch on {len(TARGETS)} targets...")
        total_batch = []
        
        for slug, pid in TARGETS.items():
            # Throttle respecting the LIMITS config
            time.sleep(RATE_LIMITS["helius"]) 
            data = self.get_onchain_activity(slug, pid)
            total_batch.extend(data)
            
        self.insert_batch(total_batch)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s')
    SolanaBatchCollector().run()
