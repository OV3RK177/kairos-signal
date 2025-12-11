import clickhouse_connect
import pandas as pd
import pandas_ta as ta
import numpy as np
from tabulate import tabulate

# --- CONFIG ---
INITIAL_CAPITAL_PER_ASSET = 1000.0
FEE_PCT = 0.001  # 0.1% fee
LEVERAGE = 1     # Spot trading
DAYS_BACK = 365  # Full Year

# STRATEGY PARAMS
SMA_PERIOD = 200
RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 30  # Standard (We will test this)
RSI_SELL_THRESHOLD = 70

print(f"🔥 INITIALIZING HEAVY BACKTEST ENGINE (365 DAYS)...")
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

def get_top_assets(limit=10):
    print("🔍 Scanning for heaviest data streams...")
    query = """
    SELECT metric_name, count() as c 
    FROM metrics 
    WHERE project_slug IN ('stock_swarm') 
    AND metric_value > 0 
    AND metric_name NOT LIKE '%_price' -- Exclude macro indicators
    GROUP BY metric_name 
    ORDER BY c DESC 
    LIMIT 10
    """
    return client.query(query).result_rows

def run_simulation(ticker, df):
    # PREPARE INDICATORS
    df['sma'] = ta.sma(df['close'], length=SMA_PERIOD)
    df['rsi'] = ta.rsi(df['close'], length=RSI_PERIOD)
    
    # VECTORIZED SIGNALS (Much faster than loops)
    # 1. Trend Filter: Close > SMA
    # 2. Dip Trigger: RSI < 30
    df['signal'] = np.where((df['close'] > df['sma']) & (df['rsi'] < RSI_BUY_THRESHOLD), 1, 0)
    
    # EXECUTION LOGIC (Iterative for PnL accuracy)
    position = False
    entry_price = 0.0
    capital = INITIAL_CAPITAL_PER_ASSET
    trades = 0
    wins = 0
    
    prices = df['close'].values
    signals = df['signal'].values
    rsis = df['rsi'].values
    dates = df.index
    
    for i in range(SMA_PERIOD, len(df)):
        price = prices[i]
        
        # BUY LOGIC
        if not position and signals[i] == 1:
            position = True
            entry_price = price
            capital -= capital * FEE_PCT
            trades += 1
            
        # SELL LOGIC (RSI Spike or Stop Loss)
        elif position:
            rsi = rsis[i]
            # Simple Sell: RSI > 70
            if rsi > RSI_SELL_THRESHOLD:
                position = False
                pnl_pct = (price - entry_price) / entry_price
                capital += (capital * pnl_pct)
                capital -= capital * FEE_PCT
                if pnl_pct > 0: wins += 1

    return capital, trades, wins

# --- MAIN LOOP ---
top_assets = get_top_assets()
results = []

print(f"🌊 FOUND {len(top_assets)} ASSETS. STARTING SIMULATION...\n")

for asset, count in top_assets:
    print(f"   Cooking {asset} ({count:,} rows)...", end=" ", flush=True)
    
    # FETCH DATA
    query = f"""
    SELECT timestamp, metric_value 
    FROM metrics 
    WHERE metric_name = '{asset}' 
    AND timestamp > now() - INTERVAL {DAYS_BACK} DAY
    ORDER BY timestamp ASC
    """
    data = client.query(query).result_rows
    
    if len(data) < SMA_PERIOD:
        print("Skipping (Not enough data)")
        continue
        
    df = pd.DataFrame(data, columns=['date', 'close'])
    df.set_index('date', inplace=True)
    df['close'] = df['close'].astype(float)
    
    # RUN SIM
    final_cap, trade_count, win_count = run_simulation(asset, df)
    
    # METRICS
    pnl_abs = final_cap - INITIAL_CAPITAL_PER_ASSET
    pnl_pct = (pnl_abs / INITIAL_CAPITAL_PER_ASSET) * 100
    win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
    
    results.append([asset, trade_count, f"{win_rate:.1f}%", f"${pnl_abs:.2f}", f"{pnl_pct:.2f}%"])
    print(f"DONE. PnL: {pnl_pct:.2f}%")

# --- FINAL REPORT ---
print("\n" + "="*60)
print(f"🦁 KAIROS BACKTEST REPORT ({DAYS_BACK} DAYS)")
print("="*60)
headers = ["Asset", "Trades", "Win Rate", "PnL ($)", "PnL (%)"]
print(tabulate(results, headers=headers, tablefmt="fancy_grid"))

# Total Stats
total_pnl = sum([float(r[3].replace('$','')) for r in results])
avg_return = sum([float(r[4].replace('%','')) for r in results]) / len(results) if results else 0

print(f"\n💰 TOTAL PORTFOLIO PnL: ${total_pnl:,.2f}")
print(f"📈 AVERAGE ASSET RETURN: {avg_return:.2f}%")
print("="*60)

if avg_return > 10:
    print("✅ VERDICT: Strategy is PROFITABLE. Keep 'v14.3' running.")
elif avg_return > 0:
    print("⚠️ VERDICT: Strategy is BREAK-EVEN. Consider loosening RSI.")
else:
    print("❌ VERDICT: Strategy is LOSING. We must change the logic.")
