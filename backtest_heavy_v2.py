import clickhouse_connect
import pandas as pd
import pandas_ta as ta
import numpy as np
from tabulate import tabulate

# --- CONFIG ---
INITIAL_CAPITAL_PER_ASSET = 1000.0
FEE_PCT = 0.001
DAYS_BACK = 365 
SMA_PERIOD = 200
RSI_BUY_THRESHOLD = 30

print(f"🔥 INITIALIZING HEAVY BACKTEST V2 (TARGETING 'price' & 'price_usd')...")
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

def get_top_assets(limit=10):
    print("🔍 Finding the deep history...")
    # FIXED QUERY: Target the specific metric names we know exist
    query = """
    SELECT metric_name, count() as c 
    FROM metrics 
    WHERE metric_name IN ('price', 'price_usd', 'close') 
       OR (project_slug='stock_swarm' AND count() > 1000)
    GROUP BY metric_name 
    ORDER BY c DESC 
    LIMIT 10
    """
    return client.query(query).result_rows

def run_simulation(asset_name, df):
    # INDICATORS
    df['sma'] = ta.sma(df['close'], length=SMA_PERIOD)
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    # LOGIC: Trend (Price > SMA) + Dip (RSI < 30)
    df['signal'] = np.where((df['close'] > df['sma']) & (df['rsi'] < RSI_BUY_THRESHOLD), 1, 0)
    
    # FAST EXECUTION
    capital = INITIAL_CAPITAL_PER_ASSET
    position = False
    entry_price = 0.0
    trades = 0
    wins = 0
    
    prices = df['close'].values
    signals = df['signal'].values
    rsis = df['rsi'].values
    
    for i in range(SMA_PERIOD, len(df)):
        price = prices[i]
        
        # BUY
        if not position and signals[i] == 1:
            position = True
            entry_price = price
            capital -= capital * FEE_PCT
            trades += 1
            
        # SELL (RSI Spike > 70)
        elif position and rsis[i] > 70:
            position = False
            pnl = (price - entry_price) / entry_price
            capital += (capital * pnl)
            capital -= capital * FEE_PCT
            if pnl > 0: wins += 1

    return capital, trades, wins

# --- MAIN ---
top_assets = get_top_assets()
results = []

print(f"🌊 FOUND {len(top_assets)} HEAVY DATA STREAMS. COOKING...\n")

for metric, count in top_assets:
    print(f"   Cooking {metric} ({count:,} rows)...", end=" ", flush=True)
    
    # Fetch Data
    query = f"""
    SELECT timestamp, metric_value 
    FROM metrics 
    WHERE metric_name = '{metric}' 
    ORDER BY timestamp ASC
    """
    data = client.query(query).result_rows
    
    if len(data) < SMA_PERIOD:
        print("Skipping (Too short)")
        continue
        
    df = pd.DataFrame(data, columns=['date', 'close'])
    df.set_index('date', inplace=True)
    df['close'] = df['close'].astype(float)
    
    final_cap, t_count, w_count = run_simulation(metric, df)
    
    pnl_val = final_cap - INITIAL_CAPITAL_PER_ASSET
    pnl_pct = (pnl_val / INITIAL_CAPITAL_PER_ASSET) * 100
    win_rate = (w_count / t_count * 100) if t_count > 0 else 0
    
    results.append([metric, t_count, f"{win_rate:.1f}%", f"${pnl_val:.2f}", f"{pnl_pct:.2f}%"])
    print(f"DONE. PnL: {pnl_pct:.2f}%")

print("\n" + "="*60)
print(f"🦁 KAIROS BACKTEST REPORT")
print("="*60)
print(tabulate(results, headers=["Metric", "Trades", "Win Rate", "PnL ($)", "PnL (%)"], tablefmt="fancy_grid"))
