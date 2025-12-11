import clickhouse_connect
import ollama
import pandas as pd
import numpy as np
import os
import json
import re
import sys

# --- CONFIG ---
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')
MODEL = "kimi-k2-thinking:cloud"
TARGET_ASSET = "BTC_USD" 

print(f"// KAIROS NEURAL BRAIN // CONNECTING TO MEMORY...")

try:
    client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
except Exception as e:
    print(f"❌ DB FAIL: {e}"); exit(1)

# 1. FETCH DATA (Full History)
print(f"📥 Fetching history for {TARGET_ASSET}...")
q = f"""
SELECT timestamp, price_close 
FROM candles_10m 
WHERE project_slug = '{TARGET_ASSET}'
ORDER BY timestamp ASC
"""
df = client.query_df(q)

if df.empty:
    print(f"❌ NO DATA FOR {TARGET_ASSET}. Did the backfill work?")
    exit(1)

# 2. CALCULATE INDICATORS
df = df.set_index('timestamp')
# Simple Moving Average
df['SMA_20'] = df['price_close'].rolling(window=20).mean()
# RSI
delta = df['price_close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# Drop NaN
df = df.dropna()
last_price = df.iloc[-1]['price_close']
last_rsi = df.iloc[-1]['RSI']
last_time = df.index[-1]

print(f"✅ DATA LOADED: {len(df)} candles found.")
print(f"📅 RANGE: {df.index.min()} -> {last_time}")
print(f"📊 LATEST: ${last_price:,.2f} | RSI: {last_rsi:.1f}")

# 3. CONSTRUCT PROMPT
# We give Kimi the last 10 candles of context
context = df.tail(10)[['price_close', 'RSI', 'SMA_20']].to_string()

prompt = f"""
Analyze this REAL market data for {TARGET_ASSET}.
Candle Interval: 10 Minutes.

{context}

Current Price: {last_price}
Current RSI: {last_rsi:.2f}

INSTRUCTIONS:
1. Analyze the trend (Price vs SMA).
2. Analyze Momentum (RSI).
3. Decide: BUY, SELL, or HOLD.

OUTPUT FORMAT:
Return ONLY a valid JSON object. Do not write markdown.
Example: {{"action": "BUY", "confidence": "high", "reason": "RSI crossing 30 upwards"}}
"""

print("\n🧠 KAIROS IS THINKING...")

try:
    response = ollama.generate(model=MODEL, prompt=prompt, stream=False)
    raw_output = response['response']
    
    # robust json extraction
    match = re.search(r'\{.*\}', raw_output, re.DOTALL)
    if match:
        json_str = match.group(0)
        decision = json.loads(json_str)
        
        action = decision.get('action', 'UNKNOWN').upper()
        reason = decision.get('reason', 'No reason provided')
        confidence = decision.get('confidence', 'low')
        
        color = "\033[92m" if action == "BUY" else "\033[91m" if action == "SELL" else "\033[93m"
        reset = "\033[0m"
        
        print(f"\n{color}=== DECISION: {action} ==={reset}")
        print(f"Confidence: {confidence}")
        print(f"Rationale:  {reason}")
    else:
        print(f"⚠️ PARSE ERROR. Raw Output:\n{raw_output}")

except Exception as e:
    print(f"❌ AI ERROR: {e}")
