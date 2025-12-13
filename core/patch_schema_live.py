import clickhouse_connect
import os

# Connect to Localhost
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password=os.getenv('CLICKHOUSE_PASSWORD', 'kairos'))

print("// APPLYING BATTLEFIELD SURGERY TO DB //")

# 1. FIX LEDGER (The Accountant)
try:
    print("🔧 Patching 'signal_ledger'...")
    client.command("ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS pnl_pct Float64 DEFAULT 0")
    client.command("ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS exit_price Float64 DEFAULT 0")
    client.command("ALTER TABLE signal_ledger ADD COLUMN IF NOT EXISTS closed_at DateTime DEFAULT toDateTime(0)")
    print("✅ Ledger Patched.")
except Exception as e:
    print(f"⚠️ Ledger Patch Note: {e}")

# 2. FIX BRAIN (The Signals)
try:
    print("🔧 Patching 'signals'...")
    client.command("ALTER TABLE signals ADD COLUMN IF NOT EXISTS reason String")
    client.command("ALTER TABLE signals ADD COLUMN IF NOT EXISTS confidence Float64 DEFAULT 0.5")
    print("✅ Brain Patched.")
except Exception as e:
    print(f"⚠️ Brain Patch Note: {e}")

print("\n🚀 SCHEMA SYNC COMPLETE. RESTART SERVICES.")
