import clickhouse_connect
import numpy as np
import time
import re

# --- CONFIGURATION ---
CH_HOST = "localhost"
HISTORY_HOURS = 24  # Increased context for better sensor alignment
MIN_HISTORY = 30    
SENTIMENT_THRESHOLD = 0.05 # Neural Barrier (Median was 0.066)

print(f"--- KAIROS CORTEX v15.0: SENSOR FUSION ACTIVE ---", flush=True)
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

# BLACKLIST (Ignore noise, but allow specific sensors)
IGNORE_PATTERNS = [r"_price$", r"_vol$", r"_change$", r"^[a-z_]+$"]

def is_tradable(ticker):
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, ticker): return False
    if len(ticker) > 8 and not ticker.isupper(): return False
    return True

def get_market_context():
    """Fetches BOTH Asset Histories and Global Sensor States"""
    try:
        # 1. Fetch Asset Prices
        query_assets = f"""
        SELECT project_slug, groupArray(metric_value)
        FROM (
            SELECT project_slug, metric_value 
            FROM metrics 
            WHERE metric_name = 'price_usd' 
            AND timestamp >= now() - INTERVAL {HISTORY_HOURS} HOUR
            ORDER BY timestamp ASC
        ) 
        GROUP BY project_slug
        """
        asset_rows = client.query(query_assets).result_rows
        
        # 2. Fetch Global Sentiment (The "Vibe" Check)
        query_sensor = """
        SELECT argMax(metric_value, timestamp) 
        FROM metrics 
        WHERE metric_name = 'global_sentiment_score'
        """
        sensor_val = client.query(query_sensor).result_rows
        current_sentiment = sensor_val[0][0] if sensor_val else 0.0
        
        # Filter & Package
        assets = {}
        for r in asset_rows:
            if is_tradable(r[0]):
                assets[r[0]] = np.array(r[1], dtype=np.float64)
                
        return assets, current_sentiment
    except Exception as e:
        print(f"⚠️ MEMORY FAILURE: {e}", flush=True)
        return {}, 0.0

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50.0
    if np.std(prices) == 0: return 50.0
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    if down == 0: return 55.0
    rs = up/down
    return 100 - (100 / (1 + rs))

def analyze_ticker(ticker, prices, sentiment):
    if len(prices) < MIN_HISTORY: return None 

    current_price = prices[-1]
    lookback = min(len(prices), 200)
    trend_line = np.mean(prices[-lookback:]) 
    rsi = calculate_rsi(prices)
    
    # --- LOGIC GATES (FUSION) ---

    # SCENARIO A: UPTREND DIP (With Sentiment Confirmation)
    if current_price > trend_line and rsi < 30:
        # THE FUSION CHECK:
        if sentiment > SENTIMENT_THRESHOLD:
            return f"BUY {ticker} @ ${current_price:.2f} | 📈 TREND: UP | 🧠 SENTIMENT: {sentiment:.3f} (OK)"
        else:
            # We silently VETO the trade. 
            # (Optional: return a log if you want to see blocked trades)
            return None 

    # SCENARIO B: DOWNTREND RALLY (Sell)
    # We don't check sentiment for sells (Panic is panic)
    if current_price < trend_line and rsi > 75:
        return f"SELL {ticker} @ ${current_price:.2f} | 📉 TREND: DOWN | 📈 SPIKE: RSI {rsi:.1f}"

    return None

def scan_market():
    print("🦁 SYSTEM ONLINE. Waiting for cycle...", flush=True)
    while True:
        # 1. LOAD CONTEXT
        stock_swarm, global_sentiment = get_market_context()
        print(f"🧠 CONTEXT: Global Sentiment = {global_sentiment:.4f}", flush=True)
        
        if global_sentiment < SENTIMENT_THRESHOLD:
            print(f"🛡️  DEFENSE MODE: Sentiment low. Buying is restricted.", flush=True)
        
        signals = 0
        analyzed = 0
        
        print(f"🌊 ANALYZING: Scanning {len(stock_swarm)} assets...", flush=True)
        
        # 2. SCAN ASSETS
        for ticker, history in stock_swarm.items():
            analyzed += 1
            try:
                sig = analyze_ticker(ticker, history, global_sentiment)
                if sig:
                    print(f"🚨 SIGNAL: {sig}", flush=True)

                # --- AUTO EXECUTION (GLOBAL LEDGER) ---
                parts = sig.split('|')
                side_asset = parts[0].strip().split(' ') # ['BUY', 'BTC_USD']
                price_str = parts[0].split('@ $')[1] # '95000.00'
                
                side = side_asset[0]
                asset = side_asset[1]
                price = float(price_str)
                
                try:
                    client.command(f"INSERT INTO signal_ledger (timestamp, asset, signal_type, signal_price, entry_price, status) VALUES (now(), '{asset}', '{side}', {price}, {price}, 'OPEN')")
                    print(f"⚔️  ORDER SENT: {asset} to Ledger.", flush=True)
                except Exception as e:
                    print(f"❌ ORDER FAILED: {e}")
                # --------------------------------------
                    signals += 1
            except:
                continue
                
        print(f"✅ CYCLE COMPLETE. Scanned {analyzed} assets. Signals: {signals}")
        print("⏳ Waiting 30s...", flush=True)
        time.sleep(30)

if __name__ == "__main__":
    scan_market()
