import clickhouse_connect

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🧹 RESETTING SCOREBOARD STATISTICS...")

# Nuke the entire table (Open AND Closed trades) to reset IDs and Stats
client.command("TRUNCATE TABLE signal_ledger")

print("✅ SUCCESS: Trade history wiped.")
print("   - Total Trades: 0")
print("   - Win Rate: 0%")
print("   - PnL: 0%")
print("🚀 SYSTEM IS CLEAN.")
