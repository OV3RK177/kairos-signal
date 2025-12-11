import clickhouse_connect
import os
from dotenv import load_dotenv

load_dotenv()
try:
    # Force localhost here to bypass any lingering env issues
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')
    
    print("🔧 PATCHING SCHEMA...", flush=True)
    
    # 1. Add 'source' to metrics if missing
    try:
        client.command("ALTER TABLE metrics ADD COLUMN IF NOT EXISTS source String DEFAULT 'UNKNOWN'")
        print("✅ Added 'source' column to metrics.")
    except Exception as e:
        print(f"ℹ️ Metrics patch note: {e}")

    # 2. Add 'status' to ledger if missing
    try:
        client.command("ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS status String DEFAULT 'OPEN'")
        print("✅ Added 'status' column to ledger.")
    except Exception as e:
        print(f"ℹ️ Ledger patch note: {e}")
        
    print("✅ SCHEMA PATCH COMPLETE.")

except Exception as e:
    print(f"❌ PATCH FAILED: {e}")
