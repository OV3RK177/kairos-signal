import clickhouse_connect
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')
    print("🔌 CONNECTED TO DB. FORCE FEEDING DATA...", flush=True)

    # 1. INSERT TIER 3 ASSETS (To fill the "Dark List")
    # We insert timestamps for "now"
    print("💉 Injecting Deep Tier Prices...", flush=True)
    assets = [
        ('SYNESIS', 0.045),
        ('UPROCK', 0.012),
        ('WICRYPT', 0.150),
        ('NOSANA', 4.20),
        ('SHADOW', 0.85)
    ]
    data = []
    for asset, price in assets:
        data.append([datetime.now(), asset, 'price', price, 'FORCE_FEED'])
    
    client.insert('metrics', data, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value', 'source'])

    # 2. INSERT A WINNING TRADE (To fill the "P&L Tracker")
    print("💉 Injecting Fake Winning Trade...", flush=True)
    # We bought NOSANA at $2.00, it is now $4.20 (inserted above)
    entry_price = 2.00
    curr_price = 4.20
    pnl = ((curr_price - entry_price) / entry_price) * 100
    
    # Insert the trade record
    client.insert('signal_ledger', 
                  [[datetime.now(), 'NOSANA', 'BUY', entry_price, 'FORCE_TEST', curr_price, pnl, 'OPEN']], 
                  column_names=['timestamp', 'asset', 'action', 'signal_price', 'reason', 'current_price', 'pnl_percent', 'status'])

    print("✅ FORCE FEED COMPLETE.")
    print(f"📊 Added 5 Assets and 1 Trade (+{pnl}% profit)")

except Exception as e:
    print(f"❌ FORCE FEED FAILED: {e}")
