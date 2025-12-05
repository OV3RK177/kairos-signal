import requests
import logging
from datetime import datetime
from .base import BaseCollector

class InfrastructureBatchCollector(BaseCollector):
    def __init__(self):
        super().__init__("infrastructure_batch")
        self.session = requests.Session()

    def fetch_akash(self):
        # Source: gpu_collector.py
        url = "https://akash-api.polkachu.com/akash/market/v1beta4/leases/list"
        metrics = []
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Active Leases (Compute Demand)
                total = int(data.get('pagination', {}).get('total', 0))
                metrics.append([datetime.now(), "akash_network", "active_leases", total])
                print(f" > akash: {total} active leases")
        except Exception as e:
            self.log.error(f"Akash Fail: {e}")
        return metrics

    def fetch_flux(self):
        # Source: collector.py
        url = "https://api.runonflux.io/daemon/viewdeterministiczelnodelist"
        metrics = []
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                count = len(data)
                metrics.append([datetime.now(), "flux", "total_nodes", count])
                print(f" > flux: {count} nodes online")
        except Exception as e:
            self.log.error(f"Flux Fail: {e}")
        return metrics

    def fetch_mysterium(self):
        # Source: collector.py
        url = "https://discovery.mysterium.network/api/v3/proposals"
        metrics = []
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                count = len(data)
                metrics.append([datetime.now(), "mysterium", "active_nodes", count])
                print(f" > mysterium: {count} nodes online")
        except Exception as e:
            self.log.error(f"Mysterium Fail: {e}")
        return metrics

    def fetch_dimo(self):
        # Source: collector.py (GraphQL)
        url = "https://identity-api.dimo.zone/query"
        query = {'query': "query { vehicles (first: 1) { totalCount } }"}
        metrics = []
        try:
            resp = self.session.post(url, json=query, timeout=10)
            if resp.status_code == 200:
                count = resp.json()['data']['vehicles']['totalCount']
                metrics.append([datetime.now(), "dimo", "connected_vehicles", int(count)])
                print(f" > dimo: {count} vehicles connected")
        except Exception as e:
            self.log.error(f"DIMO Fail: {e}")
        return metrics

    def run(self):
        self.log.info("Starting Infrastructure Batch (Proven Endpoints)...")
        batch = []
        batch.extend(self.fetch_akash())
        batch.extend(self.fetch_flux())
        batch.extend(self.fetch_mysterium())
        batch.extend(self.fetch_dimo())
        
        if batch:
            self.insert_batch(batch)
            self.log.info(f"✅ Infrastructure: Injected {len(batch)} metrics.")

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    InfrastructureBatchCollector().run()
