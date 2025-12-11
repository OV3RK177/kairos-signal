import clickhouse_connect
import pandas as pd
import pandas_ta as ta
import numpy as np
from tabulate import tabulate

# --- CONFIG ---
ASSET_TICKER = 'BTC_USD'     # The Asset to trade
SENSOR_METRIC = 'global_sentiment_score' # The "Sense" to test against (Try: cushing_temp_f, fed_interest_rate)
INITIAL_CAP = 1000.0
FEE = 0.001

print(f"🦁 INITIALIZING SENSOR FUSION BACKTEST...")
print(f"   Target: {ASSET_TICKER}")
print(f"   Context: {SENSOR_METRIC}")
print("--------------------------------------------------")

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

# 1. FETCH ASSET HISTORY (The Market)
print("📥 Loading Market Data...", end=" ", flush=True)
q_price = f"""
SELECT toStartOfHour(timestamp) as t, argMax(metric_value, timestamp) as close
FROM metrics 
WHERE project_slug = '{ASSET_TICKER}' AND metric_name = 'price_usd'
GROUP BY t ORDER BY t ASC
"""
price_data = client.query(q_price).result_rows
df = pd.DataFrame(price_data, columns=['time', 'close'])
df.set_index('time', inplace=True)
print(f"DONE ({len(df)} hours)")

# 2. FETCH SENSOR HISTORY (The Physical World)
print(f"📥 Loading Sensor Data ({SENSOR_METRIC})...", end=" ", flush=True)
q_sensor = f"""
SELECT toStartOfHour(timestamp) as t, avg(metric_value) as val
FROM metrics 
WHERE metric_name = '{SENSOR_METRIC}'
GROUP BY t ORDER BY t ASC
"""
sensor_data = client.query(q_sensor).result_rows
sensor_df = pd.DataFrame(sensor_data, columns=['time', 'sensor'])
sensor_df.set_index('time', inplace=True)
print(f"DONE ({len(sensor_df)} hours)")

# 3. FUSE REALITIES
# We merge the datasets so we know EXACTLY what the sensor said at that specific price candle
print("🔗 Fusing datasets...", end=" ", flush=True)
merged = df.join(sensor_df, how='inner').dropna()
print(f"DONE. {len(merged)} synchronized simulation points.")

# 4. COMPUTE TECHNICALS (The Math)
merged['sma'] = ta.sma(merged['close'], length=200)
merged['rsi'] = ta.rsi(merged['close'], length=14)

# 5. DEFINE THE "AI" LOGIC (Math + Context)
# Strategy A: Pure Math (Blind)
merged['sig_blind'] = np.where((merged['rsi'] < 30) & (merged['close'] > merged['sma']), 1, 0)

# Strategy B: Sensor Fusion (Aware)
# We calculate the median sensor value to define "Positive Context"
sensor_median = merged['sensor'].median()
print(f"   (Sensor Baseline: {sensor_median:.4f})")

# LOGIC: Only Buy Dip if the Context is Higher than average (Positive Sentiment / High Energy / Etc)
# NOTE: If testing 'cushing_temp', you might want 'sensor < median' (Low temp = High Energy Demand)
merged['sig_fusion'] = np.where(
    (merged['rsi'] < 30) & 
    (merged['close'] > merged['sma']) & 
    (merged['sensor'] > sensor_median), # <--- THE SENSOR FILTER
    1, 0
)

# 6. RUN SIMULATIONS
def simulate(signals, name):
    cap = INITIAL_CAP
    pos = False
    entry = 0.0
    trades = 0
    wins = 0
    
    closes = merged['close'].values
    sigs = signals.values
    rsis = merged['rsi'].values
    
    for i in range(len(merged)):
        # BUY
        if not pos and sigs[i] == 1:
            pos = True
            entry = closes[i]
            cap -= cap * FEE
            trades += 1
        
        # SELL (Standard RSI Exit)
        elif pos and rsis[i] > 70:
            pos = False
            pnl = (closes[i] - entry) / entry
            cap += cap * pnl
            cap -= cap * FEE
            if pnl > 0: wins += 1
            
    return cap, trades, wins

cap_blind, t_blind, w_blind = simulate(merged['sig_blind'], "Blind Math")
cap_fusion, t_fusion, w_fusion = simulate(merged['sig_fusion'], "Sensor AI")

# 7. RESULTS
print("\n" + "="*60)
print(f"🦁 SENSOR FUSION RESULTS: {ASSET_TICKER} + {SENSOR_METRIC}")
print("="*60)

res_data = [
    ["Blind Math (RSI Only)", t_blind, f"{w_blind/t_blind*100:.1f}%" if t_blind else "0%", f"${cap_blind - INITIAL_CAP:.2f}"],
    ["Sensor Fusion (AI)", t_fusion, f"{w_fusion/t_fusion*100:.1f}%" if t_fusion else "0%", f"${cap_fusion - INITIAL_CAP:.2f}"]
]

print(tabulate(res_data, headers=["Strategy", "Trades", "Win Rate", "PnL ($)"], tablefmt="fancy_grid"))
print("="*60)

if cap_fusion > cap_blind:
    print(f"✅ CONFIRMED: Using '{SENSOR_METRIC}' improved performance.")
    print("   The AI should LISTEN to this sensor.")
else:
    print(f"❌ REJECTED: '{SENSOR_METRIC}' was noise.")
    print("   The AI should IGNORE this sensor.")
