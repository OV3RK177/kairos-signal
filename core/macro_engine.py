import ccxt
import clickhouse_connect
import psycopg2
import requests
import json
import time
import threading
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'kairos') 

# FAST LANE: Kraken (US-Friendly) -> ClickHouse
def run_kraken_stream():
    print("🚀 [FAST] KRAKEN FIREHOSE ONLINE")
    client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
    exchange = ccxt.kraken({'enableRateLimit': True})
    
    while True:
        try:
            tickers = exchange.fetch_tickers()
            sorted_tickers = sorted(tickers.values(), key=lambda x: x.get('quoteVolume', 0) or 0, reverse=True)
            top_100 = sorted_tickers[:100]
            
            batch = []
            now = datetime.now(timezone.utc)
            
            for t in top_100:
                symbol = t['symbol'].replace('/', '_')
                price = t.get('last')
                vol = t.get('quoteVolume')
                if price:
                    batch.append([now, symbol, 'price_usd', float(price)])
                if vol:
                    batch.append([now, symbol, 'volume_24h', float(vol)])
            
            if batch:
                client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                print(f"⚡ [FAST] Flushed {len(batch)} ticks to ClickHouse.")
            
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ Kraken Error: {e}")
            time.sleep(5)

# SLOW LANE: CoinGecko (DePIN) -> Postgres
def run_depin_poller():
    print("🌍 [SLOW] DEPIN WIDE-NET ONLINE")
    urls = [
        "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&category=depin&order=market_cap_desc&per_page=100&page=1&sparkline=false",
        "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,solana,matic-network,binancecoin&vs_currency=usd"
    ]
    
    while True:
        try:
            conn = psycopg2.connect(host=PG_HOST, database="kairos_meta", user="doadmin", password=PG_PASS)
            cur = conn.cursor()
            count = 0
            now = datetime.now(timezone.utc)
            
            for url in urls:
                data = requests.get(url, timeout=30).json()
                if isinstance(data, list):
                    for item in data:
                        cur.execute(
                            "INSERT INTO live_metrics (time, project, metric, value, raw_data) VALUES (%s, %s, %s, %s, %s)",
                            (now, item['id'], 'price_usd', item['current_price'], json.dumps(item))
                        )
                        count += 1
                time.sleep(2)
            
            conn.commit()
            conn.close()
            print(f"✅ [SLOW] Saved {count} DePIN prices to Postgres.")
            time.sleep(120)
        except Exception as e:
            print(f"❌ Postgres Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    t1 = threading.Thread(target=run_kraken_stream)
    t2 = threading.Thread(target=run_depin_poller)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
