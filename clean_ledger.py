import clickhouse_connect

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🧹 CLEANING LEDGER...", flush=True)

# 1. Delete Weather/Sensor trades
client.command("ALTER TABLE signal_ledger DELETE WHERE asset LIKE '%temp%'")
client.command("ALTER TABLE signal_ledger DELETE WHERE asset LIKE '%sentiment%'")
client.command("ALTER TABLE signal_ledger DELETE WHERE asset LIKE '%weather%'")
client.command("ALTER TABLE signal_ledger DELETE WHERE asset LIKE '%risk%'")

print("✅ Weather derivatives liquidated (records deleted).")

# 2. Check remaining open positions
res = client.query("SELECT asset, signal_price FROM signal_ledger WHERE status='OPEN'").result_rows
print(f"💼 Remaining Open Positions: {len(res)}")
if len(res) < 10:
    print(res)
