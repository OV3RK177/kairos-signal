import requests
import logging
from datetime import datetime
from .base import BaseCollector
from config.limits import RATE_LIMITS
import time

class DeepNetworkCollector(BaseCollector):
    def __init__(self):
        super().__init__("deep_networks")
        self.session = requests.Session()
        self.headers = {"User-Agent": "KairosSignal/1.0"}

    def fetch_weatherxm_stats(self):
        """
        Source: WeatherXM Public API
        Endpoint: https://api.weatherxm.com/api/v1/network/stats
        """
        url = "https://api.weatherxm.com/api/v1/network/stats"
        ts = datetime.now()
        metrics = []
        
        try:
            time.sleep(RATE_LIMITS["weatherxm"])
            resp = self.session.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                stations = data.get('total_stations', 0)
                if stations:
                    metrics.append([ts, 'weatherxm', 'total_stations', int(stations)])
                    print(f" > weatherxm: {stations} stations")
        except Exception as e:
            self.log.error(f"WeatherXM Fail: {e}")
            
        return metrics

    def run(self):
        self.log.info("Starting Deep Network Scan...")
        batch = []
        
        # Helium Legacy API (api.helium.io) is DEAD. Removed.
        # We rely on Helius (Phase 3) for HNT data now.
        
        # WeatherXM
        batch.extend(self.fetch_weatherxm_stats())
        
        if batch:
            self.insert_batch(batch)
            self.log.info(f"✅ Deep Networks: Injected {len(batch)} metrics.")

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    DeepNetworkCollector().run()
