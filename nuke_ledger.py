import clickhouse_connect

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("☢️  INITIATING TOTAL LEDGER WIPE...")

# 1. Count before
count = client.query("SELECT count() FROM signal_ledger WHERE status='OPEN'").result_rows[0][0]
print(f"📉 Found {count} corrupted positions.")

# 2. The Nuke Command (Deletes ALL rows with status='OPEN')
client.command("ALTER TABLE signal_ledger DELETE WHERE status='OPEN'")

# 3. Verification
# We loop briefly because ClickHouse mutations are asynchronous
import time
for i in range(5):
    remaining = client.query("SELECT count() FROM signal_ledger WHERE status='OPEN'").result_rows[0][0]
    if remaining == 0:
        print("✅ SUCCESS: Ledger is completely empty (0 positions).")
        break
    print(f"⏳ Deleting... ({remaining} remaining)")
    time.sleep(1)

if remaining > 0:
    print("⚠️  NOTE: Deletion is queued in background. It will finish shortly.")

print("🚀 SYSTEM READY FOR FRESH START.")
