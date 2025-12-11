import clickhouse_connect
import pandas as pd
import pandas_ta as ta
import numpy as np
from tabulate import tabulate

# --- CONFIG ---
FEE = 0.001
INITIAL_CAP = 1000.0

print(f"🏟️  INITIATING STRATEGY TOURNAMENT...")
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

def get_volatile_assets():
    # Filter out stablecoins (USDT, USDC) to stop wasting compute
    query = """
    SELECT project_slug, count() as c 
    FROM metrics 
    WHERE metric_name = 'price_usd' 
      AND project_slug NOT LIKE '%USDT%' 
      AND project_slug NOT LIKE '%USDC%'
      AND project_slug NOT LIKE '%EUR%'
    GROUP BY project_slug 
    ORDER BY c DESC 
    LIMIT 5
    """
    return client.query(query).result_rows

# --- STRATEGIES ---

def strat_scalp(df):
    # Buy RSI < 30, Sell RSI > 70 (Your current loser)
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['signal'] = np.where(df['rsi'] < 30, 1, 0)
    df['exit'] = np.where(df['rsi'] > 70, 1, 0)
    return run_sim(df, "Scalp")

def strat_trend(df):
    # Buy when Price > EMA 50, Sell when Price < EMA 50
    df['ema50'] = ta.ema(df['close'], length=50)
    df['signal'] = np.where(df['close'] > df['ema50'], 1, 0)
    df['exit'] = np.where(df['close'] < df['ema50'], 1, 0)
    return run_sim(df, "Trend")

def strat_breakout(df):
    # Buy when Price breaks Upper Bollinger Band
    bb = ta.bbands(df['close'], length=20, std=2)
    # Pandas TA returns columns like BBL_20_2.0, BBU_20_2.0
    upper = bb[f"BBU_20_2.0"]
    lower = bb[f"BBL_20_2.0"]
    
    df['signal'] = np.where(df['close'] > upper, 1, 0)
    df['exit'] = np.where(df['close'] < lower, 1, 0) # Stop loss at lower band
    return run_sim(df, "Breakout")

def run_sim(df, name):
    capital = INITIAL_CAP
    position = False
    entry = 0.0
    wins = 0
    trades = 0
    
    closes = df['close'].values
    entries = df['signal'].values
    exits = df['exit'].values
    
    for i in range(50, len(df)):
        # BUY
        if not position and entries[i] == 1:
            position = True
            entry = closes[i]
            capital -= capital * FEE
            trades += 1
        
        # SELL
        elif position and exits[i] == 1:
            position = False
            pnl = (closes[i] - entry) / entry
            capital += capital * pnl
            capital -= capital * FEE
            if pnl > 0: wins += 1
            
    return capital, trades, wins

# --- MAIN ---
assets = get_volatile_assets()
scoreboard = []

print(f"⚔️  FIGHTING ON {len(assets)} ASSETS (TAO, SOL, KAS, etc)...")

for asset, _ in assets:
    print(f"   Analyzing {asset}...", end=" ", flush=True)
    
    # Fetch Data
    q = f"SELECT timestamp, metric_value FROM metrics WHERE project_slug='{asset}' AND metric_name='price_usd' ORDER BY timestamp ASC"
    data = client.query(q).result_rows
    if len(data) < 200: continue
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['close'] = df['close'].astype(float)
    
    # Run All 3
    cap_a, t_a, w_a = strat_scalp(df.copy())
    cap_b, t_b, w_b = strat_trend(df.copy())
    cap_c, t_c, w_c = strat_breakout(df.copy())
    
    # Record Best PnL
    res = {
        "Asset": asset,
        "Scalp ($)": f"${cap_a - INITIAL_CAP:.0f}",
        "Trend ($)": f"${cap_b - INITIAL_CAP:.0f}",
        "Breakout ($)": f"${cap_c - INITIAL_CAP:.0f}",
        "Winner": "Scalp" if cap_a > cap_b and cap_a > cap_c else "Trend" if cap_b > cap_c else "Breakout"
    }
    scoreboard.append(res)
    print("DONE.")

print("\n" + "="*60)
print("🏆 TOURNAMENT RESULTS")
print("="*60)
print(tabulate(scoreboard, headers="keys", tablefmt="fancy_grid"))

# Verdict
wins = [x['Winner'] for x in scoreboard]
print(f"\n🥇 BEST OVERALL: {max(set(wins), key=wins.count)}")
