import clickhouse_connect
import ollama
import pandas as pd
import numpy as np
import os
import json
import re
import time
import csv
from tqdm import tqdm

# --- CONFIG ---
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')
MODEL = "kimi-k2-thinking:cloud"
TARGET_ASSET = "BTC_USD"
RESULTS_FILE = "deep_backtest_results.csv"
INITIAL_CAPITAL = 10000.00

print(f"// KAIROS DEEP BACKTEST // TARGET: {TARGET_ASSET}")

# 1. CONNECT & FETCH DATA
try:
    client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
    q = f"SELECT timestamp, price_close FROM candles_10m WHERE project_slug = '{TARGET_ASSET}' ORDER BY timestamp ASC"
    df = client.query_df(q)
except Exception as e:
    print(f"❌ DB ERROR: {e}"); exit(1)

if df.empty: print("❌ NO DATA FOUND."); exit(1)

# 2. PRE-CALCULATE INDICATORS (Vectorized Speed)
df = df.set_index('timestamp')
df['SMA_20'] = df['price_close'].rolling(window=20).mean()
delta = df['price_close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))
df = df.dropna() # Remove warmup period

# 3. LOAD STATE (Resiliency)
start_index = 0
balance = INITIAL_CAPITAL
btc_holdings = 0.0
history = []

if os.path.exists(RESULTS_FILE):
    print(f"🔄 Resuming from {RESULTS_FILE}...")
    saved_df = pd.read_csv(RESULTS_FILE)
    if not saved_df.empty:
        start_index = len(saved_df)
        last_row = saved_df.iloc[-1]
        balance = last_row['balance']
        btc_holdings = last_row['btc_holdings']
        print(f"   Resuming at Step {start_index} | Equity: ${last_row['equity']:,.2f}")
else:
    # Initialize CSV with headers
    with open(RESULTS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'price', 'rsi', 'action', 'reason', 'balance', 'btc_holdings', 'equity'])

# 4. THE GRIND LOOP
timestamps = df.index.tolist()
total_steps = len(df)

# Use TQDM for a progress bar
pbar = tqdm(total=total_steps, initial=start_index, unit="candle")

for i in range(start_index, total_steps):
    current_time = timestamps[i]
    current_price = df.iloc[i]['price_close']
    current_rsi = df.iloc[i]['RSI']
    
    # Context Window (Last 10 candles)
    # We need to look back from the current index 'i' in the dataframe
    if i < 10: 
        pbar.update(1); continue
        
    context = df.iloc[i-10:i][['price_close', 'RSI', 'SMA_20']].to_string()

    prompt = f"""
    MARKET DATA ({TARGET_ASSET}):
    {context}
    
    NOW: Price ${current_price} | RSI {current_rsi:.1f}
    
    DECISION:
    Based strictly on the data, decide to BUY (enter/add), SELL (exit/reduce), or HOLD.
    Return JSON: {{"action": "BUY/SELL/HOLD", "reason": "rationale"}}
    """

    action = "HOLD"
    reason = "Error"
    
    try:
        # Retry loop for AI glitches
        for attempt in range(3):
            try:
                response = ollama.generate(model=MODEL, prompt=prompt, stream=False, options={'temperature': 0.1})
                raw = response['response']
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    action = data.get('action', 'HOLD').upper()
                    reason = data.get('reason', '...')
                    break
            except:
                time.sleep(1) # Backoff
                continue

    except Exception as e:
        reason = f"AI Failure: {e}"

    # EXECUTE TRADE
    if action == "BUY" and balance > 10: # Min trade $10
        buy_amt = balance * 0.99 # All in minus fee buffer
        btc_holdings += buy_amt / current_price
        balance -= buy_amt
    elif action == "SELL" and btc_holdings > 0.0001:
        balance += btc_holdings * current_price
        btc_holdings = 0

    current_equity = balance + (btc_holdings * current_price)

    # SAVE RESULT
    with open(RESULTS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([current_time, current_price, current_rsi, action, reason, balance, btc_holdings, current_equity])

    # Update Progress Bar
    pbar.set_description(f"Eq: ${current_equity:,.0f} | Act: {action}")
    pbar.update(1)

pbar.close()
print(f"\n🏁 BACKTEST COMPLETE. Results saved to {RESULTS_FILE}")
print(f"💰 FINAL EQUITY: ${current_equity:,.2f}")
