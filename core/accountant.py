import time
import clickhouse_connect
import os
from dotenv import load_dotenv

load_dotenv()
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("💰 KAIROS ACCOUNTANT: Starting Audit Loop...", flush=True)
while True:
    try:
        # Get OPEN trades
        trades = client.query("SELECT asset, signal_price, timestamp FROM signal_ledger WHERE action = 'BUY' ORDER BY timestamp DESC").result_rows
        
        for trade in trades:
            asset, entry, ts = trade
            # Get Latest Price
            res = client.query(f"SELECT metric_value FROM metrics WHERE project_slug = '{asset}' AND metric_name = 'price' ORDER BY timestamp DESC LIMIT 1").result_rows
            if res:
                curr = res[0][0]
                pnl = ((curr - entry) / entry) * 100
                # Update Ledger
                client.command(f"ALTER TABLE signal_ledger UPDATE current_price = {curr}, pnl_percent = {pnl} WHERE asset = '{asset}' AND timestamp = '{ts}'")
                print(f"📊 {asset}: Entry ${entry:.4f} -> Now ${curr:.4f} | {pnl:+.2f}%", flush=True)
        
        time.sleep(60)
    except Exception as e:
        print(f"⚠️ Accountant Error: {e}")
        time.sleep(60)
