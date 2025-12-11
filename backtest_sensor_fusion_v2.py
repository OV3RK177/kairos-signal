import clickhouse_connect
import pandas as pd
import pandas_ta as ta
import numpy as np
from tabulate import tabulate

# --- CONFIG ---
ASSET_TICKER = 'BTC_USD'     
SENSOR_METRIC = 'global_sentiment_score'
INITIAL_CAP = 1000.0
FEE = 0.001

print(f"🦁 INITIALIZING SENSOR FUSION BACKTEST V2 (ADAPTIVE)...")
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

# 1. FETCH ASSET HISTORY
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

# 2. FETCH SENSOR HISTORY
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
print("🔗 Fusing datasets...", end=" ", flush=True)
merged = df.join(sensor_df, how='inner').dropna()
print(f"DONE. {len(merged)} synchronized hours found.")

if len(merged) < 20:
    print("\n⚠️  CRITICAL WARNING: INSUFFICIENT DATA OVERLAP")
    print(f"   We cannot run a reliable simulation on only {len(merged)} hours of fused data.")
    print("   The AI needs at least ~100 hours of overlapping history to learn correlations.")
    print("   Skipping simulation to prevent hallucination.")
    exit()

# 4. COMPUTE TECHNICALS (Adaptive)
# Use a shorter window if history is short
sma_window = min(200, int(len(merged) / 2))
print(f"🧠 Calibrating Math: Using {sma_window}-Hour Moving Average (based on available depth)")

merged['sma'] = ta.sma(merged['close'], length=sma_window)
merged['rsi'] = ta.rsi(merged['close'], length=14)

# DROP NANS (This fixes the crash)
merged.dropna(inplace=True)

# 5. DEFINE LOGIC
# Strategy A: Blind Math
merged['sig_blind'] = np.where((merged['rsi'] < 30) & (merged['close'] > merged['sma']), 1, 0)

# Strategy B: Sensor Fusion
# We use the median of the *available* window as the baseline
sensor_median = merged['sensor'].median()

merged['sig_fusion'] = np.where(
    (merged['rsi'] < 30) & 
    (merged['close'] > merged['sma']) & 
    (merged['sensor'] > sensor_median), # SENSOR FILTER
    1, 0
)

# 6. RUN SIMULATION
def simulate(signals):
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
        
        # SELL
        elif pos and rsis[i] > 70:
            pos = False
            pnl = (closes[i] - entry) / entry
            cap += cap * pnl
            cap -= cap * FEE
            if pnl > 0: wins += 1
            
    return cap, trades, wins

cap_blind, t_blind, w_blind = simulate(merged['sig_blind'])
cap_fusion, t_fusion, w_fusion = simulate(merged['sig_fusion'])

# 7. RESULTS
print("\n" + "="*60)
print(f"🦁 SENSOR FUSION REPORT: {ASSET_TICKER} + {SENSOR_METRIC}")
print("="*60)

res_data = [
    ["Blind Math", t_blind, f"{w_blind/t_blind*100:.1f}%" if t_blind else "0%", f"${cap_blind - INITIAL_CAP:.2f}"],
    ["Sensor Fusion", t_fusion, f"{w_fusion/t_fusion*100:.1f}%" if t_fusion else "0%", f"${cap_fusion - INITIAL_CAP:.2f}"]
]

print(tabulate(res_data, headers=["Strategy", "Trades", "Win Rate", "PnL ($)"], tablefmt="fancy_grid"))

if cap_fusion > cap_blind:
    print(f"✅ VERDICT: Sensor Improved Performance. KEEP IT.")
elif cap_fusion == cap_blind:
    print(f"⚠️ VERDICT: Sensor had NO EFFECT (Neutral).")
else:
    print(f"❌ VERDICT: Sensor HURT Performance. REMOVE IT.")
