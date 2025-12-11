import yfinance as yf
import clickhouse_connect
import time
import pandas as pd
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)

# TARGETS: The benchmarks that move the world
TICKERS = ["SPY", "QQQ", "NVDA", "TSLA", "COIN", "MSTR", "AMD", "GOOGL"]

def stream_wall_street():
    print(f"🏛️  WALL STREET FEED ONLINE: Tracking {len(TICKERS)} assets...")
    while True:
        try:
            # Download live data
            data = yf.download(TICKERS, period="1d", interval="1m", progress=False)
            
            # Extract latest close prices safely
            if not data.empty:
                # yfinance returns a MultiIndex DataFrame, we need to handle it carefully
                latest = data['Close'].iloc[-1]
                now = datetime.now(timezone.utc)
                batch = []
                
                for symbol in TICKERS:
                    try:
                        price = latest[symbol]
                        # Check if price is a valid number (not NaN)
                        if pd.notna(price): 
                            # METRIC: TRADFI_{SYMBOL}
                            batch.append([now, f"TRADFI_{symbol}", 'price_usd', float(price)])
                    except:
                        pass # Symbol might not be trading right now
                
                if batch:
                    client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                    print(f"💸 Captured {len(batch)} Wall Street ticks.")
                
            # Markets move slower than crypto. 60s is fine.
            time.sleep(60) 
            
        except Exception as e:
            print(f"Wall Street Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    stream_wall_street()
