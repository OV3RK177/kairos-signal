import clickhouse_connect
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- CONFIG ---
INITIAL_CAPITAL = 10000.0
FEE_PCT = 0.001  # 0.1% per trade
STOP_LOSS = 0.02 # 2% Max Loss
TAKE_PROFIT = 0.05 # 5% Target

print("⏳ INITIALIZING QUANT BACKTEST ENGINE...")

try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')
    
    # 1. FIND BEST ASSET (Most Data)
    print("🔍 Scanning Vault for deepest asset...")
    target_q = """
    SELECT metric_name, count() as c 
    FROM metrics 
    WHERE project_slug IN ('stock_swarm', 'omni_sensor') AND metric_value > 0
    GROUP BY metric_name 
    ORDER BY c DESC 
    LIMIT 1
    """
    target_asset = client.query(target_q).result_rows[0][0]
    print(f"🎯 TARGET LOCKED: {target_asset}")

    # 2. FETCH HISTORY (Last 90 Days)
    print(f"📥 Downloading history for {target_asset}...")
    history_q = f"""
    SELECT timestamp, metric_value 
    FROM metrics 
    WHERE metric_name = '{target_asset}' 
    AND metric_value > 0
    ORDER BY timestamp ASC
    """
    data = client.query(history_q).result_rows
    
    # Convert to Pandas DataFrame for Vectorized Speed
    df = pd.DataFrame(data, columns=['timestamp', 'close'])
    df.set_index('timestamp', inplace=True)
    df['close'] = df['close'].astype(float)
    
    print(f"📊 DATA LOADED: {len(df)} candles.")

    # 3. CALCULATE INDICATORS (The Brain)
    print("🧠 Computing Strategy Logic (Trend + Momentum)...")
    
    # Trend: 200 SMA
    df['sma_200'] = ta.sma(df['close'], length=200)
    
    # Momentum: RSI 14
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    # 4. RUN SIMULATION
    print("⚔️  Simulating Trades...")
    
    position = None # None, 'long'
    entry_price = 0.0
    capital = INITIAL_CAPITAL
    trades = []
    
    # Iterate through the timeline
    for i in range(201, len(df)):
        price = df['close'].iloc[i]
        sma = df['sma_200'].iloc[i]
        rsi = df['rsi'].iloc[i]
        time = df.index[i]
        
        # LOGIC GATES
        
        # ENTRY: Price > SMA (Uptrend) AND RSI < 30 (Dip)
        if position is None:
            if price > sma and rsi < 30:
                position = 'long'
                entry_price = price
                capital -= capital * FEE_PCT # Entry Fee
                trades.append({'type': 'BUY', 'price': price, 'time': time, 'rsi': rsi, 'pnl': 0})
        
        # EXIT: RSI > 70 (Spike) OR Stop Loss OR Take Profit
        elif position == 'long':
            pct_change = (price - entry_price) / entry_price
            
            should_sell = False
            reason = ""
            
            if rsi > 70: 
                should_sell = True
                reason = "RSI_SPIKE"
            elif pct_change <= -STOP_LOSS:
                should_sell = True
                reason = "STOP_LOSS"
            elif pct_change >= TAKE_PROFIT:
                should_sell = True
                reason = "TAKE_PROFIT"
                
            if should_sell:
                position = None
                pnl = (capital * pct_change)
                capital += pnl
                capital -= capital * FEE_PCT # Exit Fee
                trades.append({'type': 'SELL', 'price': price, 'time': time, 'rsi': rsi, 'pnl': pnl, 'reason': reason})

    # 5. REPORT CARD
    print("\n" + "="*50)
    print(f"📜 BACKTEST REPORT: {target_asset}")
    print("="*50)
    
    wins = [t for t in trades if t.get('pnl', 0) > 0]
    losses = [t for t in trades if t.get('pnl', 0) < 0 and t['type'] == 'SELL']
    
    total_trades = len([t for t in trades if t['type'] == 'SELL'])
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
    total_return = ((capital - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100
    
    print(f"💰 INITIAL CAPITAL:   ${INITIAL_CAPITAL:,.2f}")
    print(f"🏁 FINAL CAPITAL:     ${capital:,.2f}")
    print(f"📈 TOTAL RETURN:      {total_return:+.2f}%")
    print("-" * 50)
    print(f"🤝 TOTAL TRADES:      {total_trades}")
    print(f"🏆 WIN RATE:          {win_rate:.1f}%")
    print(f"🟢 AVG WIN:           ${(sum(t['pnl'] for t in wins)/len(wins)) if wins else 0:.2f}")
    print(f"🔴 AVG LOSS:          ${(sum(t['pnl'] for t in losses)/len(losses)) if losses else 0:.2f}")
    print("="*50)

except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}")
