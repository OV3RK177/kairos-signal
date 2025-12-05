import requests
import logging
from datetime import datetime
from .base import BaseCollector
from key_manager import key_manager
from config.limits import RATE_LIMITS
import time

class PhysicalBatchCollector(BaseCollector):
    def __init__(self):
        super().__init__("physical_batch")
        self.session = requests.Session()

    def fetch_purpleair(self):
        """Tier 2: Air Quality Sensor Network"""
        api_key = key_manager.get_next("purpleair")
        if not api_key: return []
        
        url = "https://api.purpleair.com/v1/sensors"
        # Just get a count to save data credits (fields=pk)
        params = {"fields": "name", "location_type": 0} 
        metrics = []
        
        try:
            time.sleep(RATE_LIMITS["purpleair"])
            resp = self.session.get(url, headers={"X-API-Key": api_key}, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("data", []))
                if count > 0:
                    ts = datetime.now()
                    metrics.append([ts, "purpleair", "active_sensors", count])
                    print(f" > purpleair: {count} sensors online")
            else:
                self.log.warning(f"PurpleAir {resp.status_code}: {resp.text[:50]}")
        except Exception as e:
            self.log.error(f"PurpleAir Fail: {e}")
            
        return metrics

    def fetch_flightaware(self):
        """Tier 2: Global Aviation (DePIN adjacent)"""
        api_key = key_manager.get_next("flightaware")
        if not api_key: return []
        
        # Get global flight count snapshot
        url = "https://aeroapi.flightaware.com/aeroapi/flights/count"
        metrics = []
        
        try:
            time.sleep(RATE_LIMITS["flightaware"])
            resp = self.session.get(url, headers={"x-apikey": api_key}, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                total = data.get("num_flights", 0)
                metrics.append([datetime.now(), "global_aviation", "flights_airborne", total])
                print(f" > flightaware: {total} flights airborne")
        except Exception as e:
            self.log.error(f"FlightAware Fail: {e}")
            
        return metrics

    def run(self):
        self.log.info("Starting Physical Reality Scan...")
        batch = []
        
        # 1. Air Quality
        batch.extend(self.fetch_purpleair())
        
        # 2. Aviation
        batch.extend(self.fetch_flightaware())
        
        # 3. DIMO (Vehicle Telemetry - Placeholder for Auth)
        # DIMO usually requires OAuth flows which are complex for this batch script
        # We rely on DePINscan for DIMO counts for now unless you have a raw API key.
        
        if batch:
            self.insert_batch(batch)
            self.log.info(f"✅ Physical: Injected {len(batch)} reality metrics.")

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    PhysicalBatchCollector().run()
