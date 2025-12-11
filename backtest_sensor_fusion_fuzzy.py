import clickhouse_connect
import pandas as pd
import pandas_ta as ta
import numpy as np
from tabulate import tabulate

# --- CONFIG ---
# We use TAO_USD because your audit confirmed it has 42.8 hours of dense data
ASSET_TICKER = 'TAO_USD'     
SENSOR_METRIC = 'global_sentiment_score' 
INITIAL_CAP = 1000.0
FEE = 0.001

print(f"🦁 INITIALIZING SENSOR FUSION BACKTEST (FUZZY LOGIC)...")
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

# 1. FETCH ASSET HISTORY (The Market)
print(f"📥 Loading Market Data for {ASSET_TICKER}...", end=" ", flush=True)
q_price = f"""
SELECT timestamp, metric_value as close
FROM metrics 
WHERE project_slug = '{ASSET_TICKER}' AND metric_name = 'price_usd'
ORDER BY timestamp ASC
"""
price_data = client.query(q_price).result_rows
df = pd.DataFrame(price_data, columns=['time', 'close'])
df['time'] = pd.to_datetime(df['time'])
df.sort_values('time', inplace=True)
print(f"DONE ({len(df)} rows)")

# 2. FETCH SENSOR HISTORY (The Physical World)
print(f"📥 Loading Sensor Data ({SENSOR_METRIC})...", end=" ", flush=True)
# We look for the sensor anywhere in the DB
q_sensor = f"""
SELECT timestamp, metric_value as val
FROM metrics 
WHERE metric_name = '{SENSOR_METRIC}'
ORDER BY timestamp ASC
"""
sensor_data = client.query(q_sensor).result_rows

if not sensor_data:
    print("\n❌ ERROR: Sensor data not found!")
    print("   Checking for ANY sensor data...")
    check = client.query("SELECT DISTINCT metric_name FROM metrics WHERE metric_name LIKE '%score%' OR metric_name LIKE '%rate%' LIMIT 5").result_rows
    print(f"   Available sensors: {[r[0] for r in check]}")
    exit()

sensor_df = pd.DataFrame(sensor_data, columns=['time', 'sensor'])
sensor_df['time'] = pd.to_datetime(sensor_df['time'])
sensor_df.sort_values('time', inplace=True)
print(f"DONE ({len(sensor_df)} rows)")

# 3. FUZZY MERGE (The Fix)
print("🔗 Fusing realities (As-Of Merge)...", end=" ", flush=True)
# This aligns the price candle with the LAST KNOWN sensor reading
merged = pd.merge_asof(
    df, 
    sensor_df, 
    on='time', 
    direction='backward',
    tolerance=pd.Timedelta('24 hours') # Allow sensor data to be up to 24h old
)
# Forward fill to ensure continuity
merged['sensor'] = merged['sensor'].ffill()
merged.dropna(inplace=True)
print(f"DONE. {len(merged)} synchronized points.")

# 4. COMPUTE TECHNICALS
merged['sma'] = ta.sma(merged['close'], length=200)
merged['rsi'] = ta.rsi(merged['close'], length=14)
merged.dropna(inplace=True)

# 5. DEFINE LOGIC
# Strategy A: Blind Math (Standard RSI)
# Buy Dip (RSI < 30) in Uptrend (Price > SMA)
merged['sig_blind'] = np.where((merged['rsi'] < 30) & (merged['close'] > merged['sma']), 1, 0)

# Strategy B: Sensor Fusion (Math + Context)
# "Smart" Context: We calculate a dynamic threshold for sentiment
# If Sentiment is rising or high, we are aggressive. If low, we stay out.
sensor_median = merged['sensor'].median()
merged['sig_fusion'] = np.where(
    (merged['rsi'] < 30) & 
    (merged['close'] > merged['sma']) & 
    (merged['sensor'] > sensor_median), # SENSOR FILTER: Only trade if sentiment is above median
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
        
        # SELL (RSI Spike)
        elif pos and rsis[i] > 70:
            pos = False
            pnl = (closes[i] - entry) / entry
            cap += cap * pnl
            cap -= cap * FEE
            if pnl > 0: wins += 1
            
    return cap, trades, wins, cap - INITIAL_CAP

cap_blind, t_blind, w_blind, pnl_blind = simulate(merged['sig_blind'])
cap_fusion, t_fusion, w_fusion, pnl_fusion = simulate(merged['sig_fusion'])

# 7. RESULTS
print("\n" + "="*60)
print(f"🦁 SENSOR FUSION REPORT: {ASSET_TICKER} + {SENSOR_METRIC}")
print("="*60)

res_data = [
    ["Blind Math", t_blind, f"{w_blind/t_blind*100:.1f}%" if t_blind else "0%", f"${pnl_blind:.2f}"],
    ["Sensor Fusion", t_fusion, f"{w_fusion/t_fusion*100:.1f}%" if t_fusion else "0%", f"${pnl_fusion:.2f}"]
]

print(tabulate(res_data, headers=["Strategy", "Trades", "Win Rate", "PnL ($)"], tablefmt="fancy_grid"))

print(f"\n📊 DATA CONTEXT:")
print(f"   Asset History: {df['time'].min()} to {df['time'].max()}")
print(f"   Sensor Median: {sensor_median:.4f}")
print(f"   Blind Trades:  {t_blind}")
print(f"   Fused Trades:  {t_fusion} (Filtered {t_blind - t_fusion} risky setups)")

if pnl_fusion > pnl_blind:
    print(f"\n✅ VERDICT: Sensor Fusion works. It improved profit/reduced loss.")
    print(f"   DIFFERENCE: ${pnl_fusion - pnl_blind:.2f}")
elif pnl_fusion == pnl_blind:
    print(f"\n⚠️ VERDICT: Neutral. The Sensor didn't change the outcome.")
else:
    print(f"\n❌ VERDICT: Sensor Fusion failed. It filtered out winning trades.")
