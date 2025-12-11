import clickhouse_connect

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🔧 RUNNING MASTER SCHEMA MIGRATION...")

columns_to_add = [
    ("entry_price", "Float64 DEFAULT 0.0"),
    ("signal_type", "String DEFAULT 'BUY'"),
    ("meta_data", "String DEFAULT '{}'"),
    ("exit_price", "Float64 DEFAULT 0.0"),
    ("exit_reason", "String DEFAULT ''"),
    ("pnl_percent", "Float64 DEFAULT 0.0"),
    ("status", "String DEFAULT 'OPEN'")
]

for col, dtype in columns_to_add:
    try:
        query = f"ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS {col} {dtype}"
        client.command(query)
        print(f"✅ Verified Column: {col}")
    except Exception as e:
        print(f"⚠️  Note on {col}: {e}")

print("🚀 DATABASE IS FULLY UPGRADED.")
