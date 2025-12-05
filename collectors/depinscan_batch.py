import requests
import logging
from datetime import datetime
from .base import BaseCollector
import time

# Fallback to standard project list if metrics endpoint fails
API_URL = "https://api.depinscan.io/v1/projects"

class DePINScanCollector(BaseCollector):
    def __init__(self):
        super().__init__("depinscan_batch")
        self.session = requests.Session()

    def fetch_all(self):
        metrics = []
        ts = datetime.now()
        try:
            resp = self.session.get(API_URL, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                # Check for 'data' wrapper
                projects = data.get('data', data) if isinstance(data, dict) else data
                
                for project in projects:
                    slug = project.get("slug")
                    devices = project.get("total_devices")
                    if devices:
                        metrics.append([ts, slug.replace("-", "_"), "active_devices", int(devices)])
                        
                self.log.info(f"Scanned {len(projects)} projects.")
            else:
                self.log.warning(f"DePINscan API: {resp.status_code}")
        except Exception as e:
            self.log.error(f"Scan Fail: {e}")
        return metrics

    def run(self):
        self.log.info("Starting DePINscan Swarm...")
        batch = self.fetch_all()
        if batch:
            self.insert_batch(batch)
            print(f"\n✅ DePINscan: Ingested {len(batch)} metrics.")

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    DePINScanCollector().run()
