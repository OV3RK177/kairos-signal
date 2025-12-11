import ccxt
import clickhouse_connect
import time
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)

# USE KRAKEN (US-Friendly)
exchange = ccxt.kraken({'enableRateLimit': True})

def stream_market():
    print("🚀 KRAKEN FIREHOSE ONLINE (US-SAFE)...")
    while True:
        try:
            tickers = exchange.fetch_tickers()
            # Sort by volume to get the movers
            sorted_tickers = sorted(tickers.values(), key=lambda x: x.get('quoteVolume', 0) or 0, reverse=True)
            # Top 150 Liquid Assets on Kraken (Macro Signal)
            top_assets = sorted_tickers[:150]
            
            batch = []
            now = datetime.now(timezone.utc)
            
            for t in top_assets:
                symbol = t['symbol'].replace('/', '_')
                if t.get('last'):
                    batch.append([now, symbol, 'price_usd', float(t['last'])])
                if t.get('quoteVolume'):
                    batch.append([now, symbol, 'volume_24h', float(t['quoteVolume'])])

            if batch:
                client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                print(f"⚡ Flushed {len(batch)} High-Freq points (Kraken) at {now.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Stream Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    stream_market()
