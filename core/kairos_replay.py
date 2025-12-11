import clickhouse_connect
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# --- CONFIG ---
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')
HISTORY_DAYS = 365  # THE FULL ARCHIVE

print("⏳ KAIROS TIME MACHINE: DEEP DIVE INITIALIZING...")

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

# 1. LOAD RAW DATA
print(f"📥 Fetching ALL price/volume data (Limit: {HISTORY_DAYS} days)...")
q = f"""
SELECT 
    toStartOfTenMinutes(timestamp) as step_time,
    project_slug,
    metric_name,
    argMax(metric_value, timestamp) as val
FROM metrics 
WHERE timestamp > now() - INTERVAL {HISTORY_DAYS} DAY
  AND metric_name IN ('price_usd', 'volume_24h')
GROUP BY step_time, project_slug, metric_name
ORDER BY step_time ASC
"""
df = client.query_df(q)

if df.empty:
    print("⚠️ No data found. Is the Aggregator running?"); exit()

# 2. PIVOT & FILL
print("⚙️ Structuring Matrix...")
df_pivot = df.pivot_table(index='step_time', columns=['project_slug', 'metric_name'], values='val')
df_pivot = df_pivot.fillna(method='ffill')

# 3. SIMULATION
active_positions = [] 
balance = 10000
starting_balance = balance
min_vol_threshold = 10000000 # $10M Volume
trade_log = []

print(f"\n🚀 STARTING REPLAY (Start: {df_pivot.index[0]} | End: {df_pivot.index[-1]})")
print("-" * 80)

for step_time, row in df_pivot.iterrows():
    
    # A. SELL LOGIC (24h Hold)
    for pos in active_positions[:]:
        if step_time >= pos['exit_time']:
            current_price = row.get((pos['asset'], 'price_usd'))
            if pd.notna(current_price) and current_price > 0:
                pnl_pct = (current_price - pos['entry_price']) / pos['entry_price']
                pnl_usd = pos['size'] * pnl_pct
                balance += pos['size'] + pnl_usd
                active_positions.remove(pos)
                trade_log.append(pnl_pct)
                
                # Log only significant moves to reduce noise
                if abs(pnl_pct) > 0.01: 
                    color = "\033[92m" if pnl_usd > 0 else "\033[91m"
                    print(f"{color}{str(step_time)[5:-3]:<15} | SELL | {pos['asset']:<12} | {pnl_pct:+.2%} (${pnl_usd:+.2f})\033[0m")

    # B. BUY LOGIC
    # Heuristic: Only buy if we aren't already exposed to this asset
    assets = row.index.get_level_values(0).unique()
    for asset in assets:
        try:
            vol = row.get((asset, 'volume_24h'))
            price = row.get((asset, 'price_usd'))
            
            if pd.isna(vol) or pd.isna(price) or price == 0: continue

            if vol > min_vol_threshold:
                if not any(p['asset'] == asset for p in active_positions):
                    pos_size = 1000
                    if balance > pos_size:
                        balance -= pos_size
                        exit_t = step_time + timedelta(hours=24)
                        active_positions.append({
                            'asset': asset, 'entry_price': price, 'size': pos_size, 'exit_time': exit_t
                        })
                        # Only log buys if we haven't spammed logs
                        if len(trade_log) < 5 or abs(vol) > 50000000:
                            print(f"{str(step_time)[5:-3]:<15} | BUY  | {asset:<12} | Vol: ${vol/1000000:.0f}M")
        except: pass

# 4. LIQUIDATION
print("-" * 80)
print("🏁 LIQUIDATING OPEN POSITIONS...")
last_row = df_pivot.iloc[-1]
for pos in active_positions:
    exit_price = last_row.get((pos['asset'], 'price_usd'), pos['entry_price'])
    pnl_pct = (exit_price - pos['entry_price']) / pos['entry_price']
    balance += pos['size'] * (1 + pnl_pct)
    trade_log.append(pnl_pct)

# 5. KIMI'S REPORT CARD
trades = np.array(trade_log)
total_return = (balance - starting_balance) / starting_balance
win_rate = (len(trades[trades > 0]) / len(trades) * 100) if len(trades) > 0 else 0
avg_win = trades[trades > 0].mean() if len(trades[trades > 0]) > 0 else 0
avg_loss = trades[trades < 0].mean() if len(trades[trades < 0]) > 0 else 0

print("\n=== 🧠 KIMI ANALYSIS REPORT ===")
print(f"📊 Dataset:      {len(df_pivot)} Candles (10m)")
print(f"💰 Final Equity: ${balance:,.2f}")
print(f"📈 Total Return: {total_return:+.2%}")
print(f"🎲 Trades Taken: {len(trades)}")
print(f"✅ Win Rate:     {win_rate:.1f}%")
print(f"🟢 Avg Win:      {avg_win:+.2%}")
print(f"🔴 Avg Loss:     {avg_loss:+.2%}")

if len(trades) > 0:
    if total_return > 0:
        print("💡 CONCLUSION: ALPHA DETECTED. Volume leads price.")
    else:
        print("💡 CONCLUSION: STRATEGY FAILED. Volume spikes are selling events.")
else:
    print("💡 CONCLUSION: NO TRADES. Threshold too high or data gap.")
