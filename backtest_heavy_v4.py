import clickhouse_connect
import pandas as pd
import pandas_ta as ta
import numpy as np
from tabulate import tabulate

# --- CONFIG ---
INITIAL_CAPITAL_PER_ASSET = 1000.0
FEE_PCT = 0.001
SMA_PERIOD = 200
RSI_BUY_THRESHOLD = 30 
RSI_SELL_THRESHOLD = 70

print(f"🔥 INITIALIZING BACKTEST V4 (TARGETING 'price_usd' BY TICKER)...")
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

def get_top_assets(limit=10):
    print("🔍 Separating the soup into assets...")
    # FIXED QUERY: We filter for 'price_usd' but GROUP BY project_slug (The Ticker)
    query = """
    SELECT project_slug, count() as c 
    FROM metrics 
    WHERE metric_name = 'price_usd' AND metric_value > 0
    GROUP BY project_slug 
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
            
        # SELL
        elif position and rsis[i] > RSI_SELL_THRESHOLD:
            position = False
            pnl = (price - entry_price) / entry_price
            capital += (capital * pnl)
            capital -= capital * FEE_PCT
            if pnl > 0: wins += 1

    return capital, trades, wins

# --- MAIN ---
try:
    top_assets = get_top_assets()
except Exception as e:
    print(f"❌ DATABASE ERROR: {e}")
    exit()

results = []
print(f"🌊 FOUND {len(top_assets)} CRYPTO ASSETS. COOKING...\n")

for ticker, count in top_assets:
    print(f"   Cooking {ticker:<15} ({count:,} rows)...", end=" ", flush=True)
    
    # Fetch Data using project_slug as the identifier
    query = f"""
    SELECT timestamp, metric_value 
    FROM metrics 
    WHERE project_slug = '{ticker}' AND metric_name = 'price_usd'
    ORDER BY timestamp ASC
    """
    data = client.query(query).result_rows
    
    if len(data) < SMA_PERIOD:
        print("Skipping (Too short)")
        continue
        
    df = pd.DataFrame(data, columns=['date', 'close'])
    df.set_index('date', inplace=True)
    df['close'] = df['close'].astype(float)
    
    final_cap, t_count, w_count = run_simulation(ticker, df)
    
    pnl_val = final_cap - INITIAL_CAPITAL_PER_ASSET
    pnl_pct = (pnl_val / INITIAL_CAPITAL_PER_ASSET) * 100
    win_rate = (w_count / t_count * 100) if t_count > 0 else 0
    
    results.append([ticker, t_count, f"{win_rate:.1f}%", f"${pnl_val:.2f}", f"{pnl_pct:.2f}%"])
    print(f"DONE. PnL: {pnl_pct:.2f}%")

print("\n" + "="*65)
print(f"🦁 KAIROS BACKTEST REPORT (UNFILTERED)")
print("="*65)
if not results:
    print("⚠️  NO ASSETS FOUND. CHECK DATABASE.")
else:
    print(tabulate(results, headers=["Asset", "Trades", "Win Rate", "PnL ($)", "PnL (%)"], tablefmt="fancy_grid"))

    # Summary
    total_pnl = sum([float(r[3].replace('$','')) for r in results])
    avg_return = sum([float(r[4].replace('%','')) for r in results]) / len(results)
    
    print(f"\n💰 TOTAL PnL:         ${total_pnl:,.2f}")
    print(f"📈 AVG ASSET RETURN:  {avg_return:.2f}%")
