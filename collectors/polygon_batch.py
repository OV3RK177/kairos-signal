import requests
import logging
from datetime import datetime
from .base import BaseCollector

class PolygonChainCollector(BaseCollector):
    def __init__(self):
        super().__init__("polygon_chain")
        self.session = requests.Session()
        self.url = "https://polygon-rpc.com"

    def fetch_stats(self):
        metrics = []
        ts = datetime.now()
        
        # Batch Request for Efficiency
        payload = [
            {"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1},
            {"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":2}
        ]
        
        try:
            resp = self.session.post(self.url, json=payload, timeout=10)
            if resp.status_code == 200:
                results = resp.json()
                
                # Gas Price
                gas_hex = results[0].get("result")
                if gas_hex:
                    gas_gwei = int(gas_hex, 16) / 1e9
                    metrics.append([ts, "polygon_network", "gas_price_gwei", gas_gwei])
                    
                # Block Height
                block_hex = results[1].get("result")
                if block_hex:
                    block_num = int(block_hex, 16)
                    metrics.append([ts, "polygon_network", "block_height", block_num])
                    
                print(f" > polygon_chain: Gas {gas_gwei:.2f} Gwei | Block {block_num}")
        except Exception as e:
            self.log.error(f"Polygon RPC Fail: {e}")
            
        return metrics

    def run(self):
        self.log.info("Scanning Polygon Network...")
        batch = self.fetch_stats()
        if batch:
            self.insert_batch(batch)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    PolygonChainCollector().run()
