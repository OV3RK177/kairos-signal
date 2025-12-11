import time, requests, clickhouse_connect, os, threading
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
CH_HOST = "localhost"
BIRDEYE_KEY = os.getenv("BIRDEYE_API_KEY")
POLYGON_KEY = os.getenv("POLYGON_API_KEY")

print("--- KAIROS SWARM v5.0: REAL VOLUME & SAFE CRYPTO ---", flush=True)
client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password='kairos')

def inject(data):
    if not data: return
    try:
        client.insert('metrics', data, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value', 'source'])
        # print(f"   -> Synced {len(data)} metrics", flush=True) 
    except Exception as e:
        print(f"⚠️ DB Error: {e}", flush=True)

# --- WORKER 1: STOCK SWARM (Fast & Heavy) ---
def fetch_stocks_polygon():
    """Ingests Price AND Volume for True Institutional Analysis"""
    while True:
        try:
            # We fetch the entire market snapshot (~10,000 tickers) in one call
            url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?apiKey={POLYGON_KEY}"
            res = requests.get(url, timeout=15).json()
            
            if 'tickers' in res:
                batch = []
                timestamp = datetime.now()
                for t in res['tickers']:
                    ticker = t['ticker']
                    price = t['day']['c'] # Close price
                    vol = t['day']['v']   # Volume
                    
                    # 1. Store Price
                    batch.append([timestamp, 'stock_swarm', ticker, float(price), 'POLYGON'])
                    # 2. Store Volume (New Metric Name: TICKER_vol)
                    batch.append([timestamp, 'stock_swarm', f"{ticker}_vol", float(vol), 'POLYGON'])
                
                inject(batch)
                print(f"🏢 WALL ST: Ingested {len(res['tickers'])} Tickers (Price + Vol)", flush=True)
        
        except Exception as e:
            print(f"⚠️ Polygon Error: {e}", flush=True)
        
        time.sleep(60) # Standard 1-minute candles

# --- WORKER 2: CRYPTO (The "Safe" 11s Loop) ---
def fetch_crypto_safe():
    """Fetches Top 10 Crypto Assets one by one with 11s delay"""
    # Top assets to track (BirdEye addresses or IDs)
    # Using simple trending endpoint for discovery
    while True:
        try:
            url = "https://public-api.birdeye.so/defi/token_trending?sort_by=rank&sort_type=asc&offset=0&limit=5"
            headers = {"X-API-KEY": BIRDEYE_KEY, "accept": "application/json"}
            
            res = requests.get(url, headers=headers, timeout=10).json()
            
            if res.get('success'):
                batch = []
                timestamp = datetime.now()
                for token in res['data']['tokens']:
                    sym = token.get('symbol')
                    price = token.get('price')
                    if sym and price:
                        batch.append([timestamp, 'crypto_swarm', sym, float(price), 'BIRDEYE'])
                        print(f"   🪙 Crypto Found: {sym} @ ${price}", flush=True)
                
                inject(batch)
            
        except Exception as e:
            print(f"⚠️ Crypto Error: {e}", flush=True)
            
        print("⏳ Crypto Cooldown: Sleeping 12s...", flush=True)
        time.sleep(12) # 11s + 1s buffer = 100% Safe Rate

# --- WORKER 3: PHYSICAL WORLD ---
def fetch_physical_world():
    """Ingests Commodities & Yields via Yahoo"""
    while True:
        tickers = {
            '^TNX': 'us10y_yield', 'DX-Y.NYB': 'dxy_dollar', 'GC=F': 'gold_futures',
            'CL=F': 'oil_crude', '^VIX': 'volatility_index'
        }
        try:
            data = yf.download(list(tickers.keys()), period="1d", interval="1m", progress=False)
            batch = []
            for symbol, slug in tickers.items():
                try:
                    price = data['Close'][symbol].iloc[-1]
                    if price > 0: 
                        batch.append([datetime.now(), 'macro_world', slug, float(price), 'YFINANCE'])
                except: pass
            inject(batch)
            print(f"🌍 PHYSICAL: Updated Macro Assets", flush=True)
        except: pass
        time.sleep(60)

# --- LAUNCHER ---
if __name__ == "__main__":
    # Start threads
    t1 = threading.Thread(target=fetch_stocks_polygon)
    t2 = threading.Thread(target=fetch_crypto_safe)
    t3 = threading.Thread(target=fetch_physical_world)
    
    t1.start()
    t2.start()
    t3.start()
    
    t1.join()
    t2.join()
    t3.join()
