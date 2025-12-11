import clickhouse_connect
import os
from dotenv import load_dotenv

load_dotenv()
try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')
    
    print("🔧 REBUILDING LEDGER...", flush=True)
    
    # 1. Drop existing table
    client.command("DROP TABLE IF EXISTS signal_ledger")
    
    # 2. Create fresh with correct columns
    create_cmd = """
    CREATE TABLE signal_ledger (
        timestamp DateTime,
        asset String,
        action String,
        signal_price Float64,
        reason String,
        current_price Float64 DEFAULT 0.0,
        pnl_percent Float64 DEFAULT 0.0,
        status String DEFAULT 'OPEN'
    ) ENGINE = MergeTree()
    ORDER BY timestamp
    """
    client.command(create_cmd)
    
    print("✅ SIGNAL LEDGER REBUILT.")

except Exception as e:
    print(f"❌ REBUILD FAILED: {e}")
