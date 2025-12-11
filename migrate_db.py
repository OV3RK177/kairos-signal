import clickhouse_connect

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🔧 MIGRATING DATABASE SCHEMA...")

try:
    # 1. Add Signal Type (BUY/SELL)
    client.command("ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS signal_type String DEFAULT 'BUY'")
    print("✅ Added column: signal_type")
    
    # 2. Add Meta Data (For Leverage/Lot Size info)
    client.command("ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS meta_data String DEFAULT '{}'")
    print("✅ Added column: meta_data")
    
    print("🚀 SUCCESS: Database is now compatible with Cortex v15.")
    
except Exception as e:
    print(f"⚠️ MIGRATION NOTE: {e}")
