import requests
import logging
from datetime import datetime
from .base import BaseCollector
import os
import time

class MacroBatchCollector(BaseCollector):
    def __init__(self):
        super().__init__("macro_batch")
        self.session = requests.Session()
        # Ensure these are in your local .env
        self.fred_key = os.getenv("FRED_API_KEY")
        self.github_token = os.getenv("GITHUB_ACCESS_TOKEN")

    def fetch_fred_series(self, series_id, metric_name):
        if not self.fred_key: 
            return []
        
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.fred_key,
            "file_type": "json",
            "limit": 1,
            "sort_order": "desc"
        }
        
        metrics = []
        try:
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("observations", [])
                if data:
                    val = float(data[0]["value"])
                    ts = datetime.now()
                    metrics.append([ts, "global_macro", metric_name, val])
                    print(f" > FRED {metric_name}: {val}")
        except Exception as e:
            self.log.error(f"FRED {series_id} Fail: {e}")
            
        return metrics

    def fetch_github_activity(self, owner, repo):
        if not self.github_token: 
            return []
        
        url = f"https://api.github.com/repos/{owner}/{repo}/stats/participation"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        metrics = []
        try:
            resp = self.session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "all" in data and len(data["all"]) > 0:
                    commits_last_week = data["all"][-1]
                    slug = f"{owner}_{repo}".lower().replace("-", "_")
                    metrics.append([datetime.now(), slug, "github_commits_weekly", int(commits_last_week)])
                    print(f" > GitHub {slug}: {commits_last_week} commits")
        except Exception as e:
            self.log.error(f"GitHub {repo} Fail: {e}")
            
        return metrics

    def run(self):
        self.log.info("Starting Macro/Social Sweep...")
        batch = []
        
        # 1. Economic Data (FRED)
        batch.extend(self.fetch_fred_series("FEDFUNDS", "fed_interest_rate"))
        batch.extend(self.fetch_fred_series("CPIAUCSL", "cpi_inflation_index"))
        
        # 2. Developer Activity (GitHub)
        repos = [
            ("helium", "helium-core"),
            ("hivemapper", "hivemapper-dashcam"),
            ("render-foundation", "render-token"),
            ("dimo-network", "dimo-node")
        ]
        
        for owner, repo in repos:
            time.sleep(1) # Polite delay
            batch.extend(self.fetch_github_activity(owner, repo))
            
        if batch:
            self.insert_batch(batch)
            self.log.info(f"✅ Macro: Injected {len(batch)} metrics.")

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    MacroBatchCollector().run()
