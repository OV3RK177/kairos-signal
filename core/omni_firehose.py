import ccxt
import clickhouse_connect
import time
from datetime import datetime, timezone
import os
import logging
from dotenv import load_dotenv

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 

# SETUP CLICKHOUSE
client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)

# SETUP EXCHANGE (Binance has the most volume/pairs)
# We use public API (no keys needed for market data)
exchange = ccxt.binance({'enableRateLimit': True})

def stream_market():
    print("🚀 OMNI-FIREHOSE ACTIVE. TARGETING TOP 500 ASSETS...")
    
    while True:
        try:
            # 1. FETCH EVERYTHING (Snapshot of the whole market)
            # This returns ~2000+ pairs instantly
            tickers = exchange.fetch_tickers()
            
            # 2. SORT & FILTER (Top 500 by Volume)
            # We convert dictionary to list, sort by quote volume (USDT volume)
            sorted_tickers = sorted(tickers.values(), key=lambda x: x.get('quoteVolume', 0) or 0, reverse=True)
            top_500 = sorted_tickers[:500]
            
            # 3. PREPARE BATCH
            batch = []
            now = datetime.now(timezone.utc)
            
            for t in top_500:
                symbol = t['symbol'].replace('/', '_') # Clean symbol: BTC/USDT -> BTC_USDT
                price = t.get('last')
                vol = t.get('quoteVolume')
                bid = t.get('bid')
                ask = t.get('ask')
                
                if price:
                    # Log Price
                    batch.append([now, symbol, 'price_usd', float(price)])
                
                if vol:
                    # Log Volume (Critical for "Spurious Correlation" detection)
                    batch.append([now, symbol, 'volume_24h', float(vol)])
                    
                if bid and ask:
                    # Log Spread (Volatility proxy)
                    spread = (ask - bid) / ask * 100
                    batch.append([now, symbol, 'spread_pct', float(spread)])

            # 4. INJECT INTO WAREHOUSE
            if batch:
                client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                print(f"⚡ Flushed {len(batch)} data points (Top 500 Assets) at {now.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Stream Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    stream_market()
