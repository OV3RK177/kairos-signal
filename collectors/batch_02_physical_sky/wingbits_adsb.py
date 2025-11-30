import requests
import time
import sys
import os
import logging
sys.path.append(os.getcwd())
from collectors.base import KairosCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenSky")

class WingbitsAdsb(KairosCollector):
    def __init__(self):
        super().__init__("wingbits_adsb")

    def collect(self):
        # PIVOT: Using OpenSky Network (No Key Required for anon access)
        url = "https://opensky-network.org/api/states/all"
        logger.info("📡 OPENSKY: INITIALIZED (Bypassing Wingbits Auth)")
        
        while True:
            print("⏳ Scanning Global Airspace (OpenSky)...")
            try:
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    # OpenSky returns a list of states (planes)
                    states = data.get("states", [])
                    count = len(states) if states else 0
                    
                    self.send_data("sky_activity", count, meta={"provider": "opensky"})
                    print(f"✈️  OPENSKY: {count} Live Aircraft Tracked | 🟢 200 OK")
                else:
                    print(f"⚠️ API STATUS: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ CONNECTION ERROR: {e}")
            
            # OpenSky rate limit for anon is slower, sleep 2 mins to be safe
            time.sleep(120)

if __name__ == "__main__":
    WingbitsAdsb().collect()
