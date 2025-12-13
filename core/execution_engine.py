import clickhouse_connect
import time
import os

# --- CONFIGURATION ---
LEVERAGE = 2.0  # 200% Leverage
print(f"--- KAIROS EXECUTION: GLOBAL MACRO MODE (Lev: {LEVERAGE}x) ---", flush=True)

def get_client():
    return clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

def execute_trade(signal):
    """
    Takes a signal dict and logs it to the ledger.
    """
    client = get_client()
    ticker = signal['asset']
    price = float(signal['signal_price'])
    side = signal['action']
    
    print(f"⚔️  EXECUTING: {side} {ticker} @ ${price}")
    
    try:
        # Check if already in ledger to prevent duplicates
        exists = client.query(f"SELECT count() FROM signal_ledger WHERE asset = '{ticker}' AND timestamp = '{signal['timestamp']}'").result_rows[0][0]
        
        if exists == 0:
            query = f"""
            INSERT INTO signal_ledger (
                timestamp, asset, signal_type, signal_price, entry_price, status, meta_data
            ) VALUES (
                '{signal['timestamp']}', '{ticker}', '{side}', {price}, {price}, 'OPEN', '{{"leverage": {LEVERAGE}}}'
            )
            """
            client.command(query)
            print(f"✅ FILLED: {ticker} (Ledger Updated)")
        else:
            print(f"⚠️ SKIPPING: {ticker} (Already Executed)")
            
    except Exception as e:
        print(f"❌ EXECUTION FAILURE: {e}")

def monitor_signals():
    print("⚔️  Execution Engine Active. Polling for signals...", flush=True)
    client = get_client()
    
    while True:
        try:
            # Poll 'signals' table for entries in the last 10 seconds
            query = """
                SELECT timestamp, asset, action, signal_price 
                FROM signals 
                WHERE timestamp > now() - INTERVAL 10 SECOND
                ORDER BY timestamp DESC
            """
            recent_signals = client.query(query).result_rows
            
            for sig in recent_signals:
                signal_data = {
                    'timestamp': sig[0],
                    'asset': sig[1],
                    'action': sig[2],
                    'signal_price': sig[3]
                }
                execute_trade(signal_data)
            
            time.sleep(1) # POLLING RATE
            
        except Exception as e:
            print(f"⚠️ Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_signals()
