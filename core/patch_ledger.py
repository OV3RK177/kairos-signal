import clickhouse_connect
import os
from dotenv import load_dotenv
load_dotenv()
try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')
    client.command("ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS current_price Float64")
    client.command("ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS pnl_percent Float64")
    client.command("ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS status String DEFAULT 'OPEN'")
    print("✅ Ledger Patched.")
except Exception as e: print(e)
