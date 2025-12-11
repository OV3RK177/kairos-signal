import clickhouse_connect
import pandas as pd
import requests
import json
import os
from datetime import timedelta

# --- CONFIG ---
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')
# This connects to the host machine's Ollama
OLLAMA_URL = "http://host.docker.internal:11434/api/generate" 
MODEL_NAME = "kimi-k2" 
HISTORY_DAYS = 365 # FULL ARCHIVE

print(f"🧠 KAIROS NEURAL ENGINE: CONNECTING TO {MODEL_NAME}...")

# CONNECT (High Mem)
try:
    client = clickhouse_connect.get_client(
        host=CH_HOST, 
        port=8123, 
        username='default', 
        password=CH_PASS,
        settings={'max_memory_usage': 10000000000}
    )
except:
    print("❌ DB Connect Fail"); exit(1)

# 1. LOAD THE CONTEXT STREAM
print(f"📥 Loading {HISTORY_DAYS} days of raw data...")
q = f"""
SELECT 
    toStartOfTenMinutes(timestamp) as step_time,
    project_slug,
    metric_name,
    argMax(metric_value, timestamp) as val
FROM metrics 
WHERE timestamp > now() - INTERVAL {HISTORY_DAYS} DAY
GROUP BY step_time, project_slug, metric_name
ORDER BY step_time ASC
"""
try:
    df = client.query_df(q)
except Exception as e:
    print(f"❌ Query Failed: {e}"); exit()

if df.empty: print("⚠️ No data found."); exit()

# Pivot to create "Frames"
print("⚙️ Structuring Memory Matrix...")
df_pivot = df.pivot_table(index='step_time', columns=['project_slug', 'metric_name'], values='val')
df_pivot = df_pivot.fillna(method='ffill').fillna(0)

# 2. THE THINKING LOOP
balance = 10000
positions = []

print(f"\n🚀 STARTING NEURAL REPLAY (Model: {MODEL_NAME})")
print("-" * 80)

# We define a system prompt that forces Kimi to act as a quant
SYSTEM_PROMPT = """You are KAIROS, an autonomous algorithmic trader. 
Analyze the provided market snapshot. 
Look for divergences between Volume and Price. 
Look for Sentiment shifts.
Output ONLY JSON."""

# Iterate through history
for step_time, row in df_pivot.iterrows():
    
    # A. CONSTRUCT THE SITREP
    btc_price = row.get(('BTC_USD', 'price_usd'), 0)
    btc_vol = row.get(('BTC_USD', 'volume_24h'), 0)
    eth_price = row.get(('ETH_USD', 'price_usd'), 0)
    sentiment = row.get(('news_api', 'sentiment_score'), 0)
    
    if btc_price == 0: continue

    # The Prompt for Kimi
    prompt = f"""
    [MARKET SNAPSHOT @ {step_time}]
    BTC Price: ${btc_price:,.2f}
    BTC Volume: ${btc_vol:,.0f}
    ETH Price: ${eth_price:,.2f}
    News Sentiment: {sentiment}
    
    [DECISION]
    Should we enter a NEW position?
    Format: JSON {{ "action": "BUY" | "SELL" | "HOLD", "asset": "BTC_USD", "reason": "brief reason" }}
    """

    # B. INVOKE THE AI
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "format": "json"
        }
        
        # Hit Ollama
        response = requests.post(OLLAMA_URL, json=payload, timeout=20)
        
        if response.status_code == 200:
            res_json = response.json()
            decision = json.loads(res_json['response'])
            action = decision.get('action', 'HOLD')
            reason = decision.get('reason', '...')
            
            # C. EXECUTE
            if action == "BUY" and balance > 1000:
                balance -= 1000
                positions.append({'asset': 'BTC_USD', 'entry': btc_price, 'size': 1000, 'time': step_time})
                print(f"🟢 {str(step_time)[5:-3]} | AI BUY  | ${btc_price:,.0f} | 🧠 {reason}")
                
            elif action == "SELL":
                # Sell all open positions for simplicity in this test
                for pos in positions[:]:
                    pnl = (btc_price - pos['entry']) / pos['entry']
                    pnl_usd = pos['size'] * pnl
                    balance += pos['size'] + pnl_usd
                    color = "\033[92m" if pnl > 0 else "\033[91m"
                    print(f"{color}🔴 {str(step_time)[5:-3]} | AI SELL | ${btc_price:,.0f} | PnL: {pnl:+.2%} (${pnl_usd:.2f}) | 🧠 {reason}\033[0m")
                    positions.remove(pos)
                    
    except Exception as e:
        # If Ollama is slow/offline, skip to next candle
        pass

print("-" * 80)
# Final Liquidation
for p in positions:
    balance += p['size'] # Return capital
print(f"💰 FINAL EQUITY: ${balance:,.2f}")
