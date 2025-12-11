import clickhouse_connect
import datetime

# Connect to DB
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🕵️ KAIROS DATA INSPECTOR")
print("---------------------------------")

# 1. Check the very latest timestamp in the entire system
latest = client.query("SELECT max(timestamp) FROM metrics WHERE project_slug='stock_swarm'").result_rows
if latest and latest[0][0]:
    print(f"🕒 LATEST SYSTEM HEARTBEAT: {latest[0][0]}")
    
    # Calculate lag
    now = datetime.datetime.now()
    lag = (now - latest[0][0]).total_seconds()
    if lag > 300: # 5 minutes
        print(f"⚠️  WARNING: Data is STALE. Lag: {lag/60:.1f} minutes.")
    else:
        print(f"✅  Data is LIVE. Lag: {lag:.1f} seconds.")
else:
    print("❌  CRITICAL: No data found in 'stock_swarm'.")

print("\n🔎 RECENT AAPL PRICES:")
# 2. Check a specific ticker (AAPL) to see if it looks like a flatline or real trading
query = "SELECT timestamp, metric_value FROM metrics WHERE project_slug='stock_swarm' AND metric_name='AAPL' ORDER BY timestamp DESC LIMIT 3"
res = client.query(query).result_rows

if res:
    for row in res:
        print(f"   {row[0]} | ")
else:
    print("   (No AAPL data found)")

print("---------------------------------")
