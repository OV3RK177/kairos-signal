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

    def fetch_helium_stats(self):
        """
        Source: Helium Blockchain API (Free)
        Endpoint: https://api.helium.io/v1/stats
        """
        url = "https://api.helium.io/v1/stats"
        ts = datetime.now()
        metrics = []
        
        try:
            # Respect Rate Limit (10 req/sec)
            time.sleep(RATE_LIMITS["helium_public"])
            
            resp = self.session.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('data', {})
                counts = data.get('counts', {})
                
                # Hotspots
                if 'hotspots' in counts:
                    metrics.append([ts, 'helium', 'active_hotspots', int(counts['hotspots'])])
                
                # Blocks (Liveness)
                if 'blocks' in counts:
                    metrics.append([ts, 'helium', 'block_height', int(counts['blocks'])])
                    
                # Token Supply (Circulating)
                supply = data.get('token_supply', 0)
                if supply:
                    metrics.append([ts, 'helium', 'circulating_supply', float(supply)])
                    
                print(f" > helium: {counts.get('hotspots')} hotspots")
            else:
                self.log.warning(f"Helium API: {resp.status_code}")
                
        except Exception as e:
            self.log.error(f"Helium Fail: {e}")
            
        return metrics

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
                
                # Total Stations
                stations = data.get('total_stations', 0)
                if stations:
                    metrics.append([ts, 'weatherxm', 'total_stations', int(stations)])
                
                # Active Stations (claimed)
                claimed = data.get('claimed_stations', 0)
                if claimed:
                    metrics.append([ts, 'weatherxm', 'claimed_stations', int(claimed)])
                    
                print(f" > weatherxm: {stations} stations")
            else:
                self.log.warning(f"WeatherXM API: {resp.status_code}")
                
        except Exception as e:
            self.log.error(f"WeatherXM Fail: {e}")
            
        return metrics

    def run(self):
        self.log.info("Starting Deep Network Scan...")
        batch = []
        
        # 1. Helium (The King of DePIN)
        batch.extend(self.fetch_helium_stats())
        
        # 2. WeatherXM (The Environment Layer)
        batch.extend(self.fetch_weatherxm_stats())
        
        if batch:
            self.insert_batch(batch)
            self.log.info(f"✅ Deep Networks: Injected {len(batch)} metrics.")

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    DeepNetworkCollector().run()
