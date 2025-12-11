import requests
import clickhouse_connect
import time
import json
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)

def scan_social_pressure():
    print("📡 SOCIAL RADAR ONLINE: Tracking CoinGecko Trending...")
    while True:
        try:
            # CoinGecko Trending (The 7 most searched coins on Earth right now)
            url = "https://api.coingecko.com/api/v3/search/trending"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                coins = data.get('coins', [])
                
                batch = []
                now = datetime.now(timezone.utc)
                
                for i, item in enumerate(coins):
                    coin = item['item']
                    name = coin['slug'].upper().replace('-', '_')
                    # Score: Rank 1 = 100 hype, Rank 7 = 14 hype
                    hype_score = 100 - (i * 12)
                    
                    # Log Metric: SOCIAL_SOLANA, SOCIAL_BITCOIN, etc.
                    batch.append([now, f"SOCIAL_{name}", 'hype_score', float(hype_score)])
                    
                    # Also log the raw rank
                    batch.append([now, f"SOCIAL_{name}", 'trending_rank', float(i + 1)])

                if batch:
                    client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                    print(f"👀 Captured Top 7 Trending Coins (Leader: {coins[0]['item']['slug']})")
            
            # Rate limit is loose, but let's be safe. Check every 5 mins.
            time.sleep(300)
            
        except Exception as e:
            print(f"Social Radar Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    scan_social_pressure()
