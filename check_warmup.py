import clickhouse_connect
import time

# Connect to DB
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🌡️  KAIROS WARMUP MONITOR")
print("---------------------------------------")

# Count how many VALID (>0) data points exist per asset in last 1 hour
query = """
SELECT count() as depth, any(metric_value) as sample_price 
FROM metrics 
WHERE project_slug='stock_swarm' AND metric_value > 0 AND timestamp > now() - INTERVAL 1 HOUR
GROUP BY metric_name 
ORDER BY depth DESC 
LIMIT 5
"""

res = client.query(query).result_rows

if not res:
    print("❄️  SYSTEM IS FROZEN: No valid data points found.")
else:
    depth = res[0][0]
    print(f"🔥 Max History Depth: {depth} data points")
    print(f"💲 Sample Price:      ${res[0][1]}")
    
    if depth < 5:
        print("\n⏳ STATUS: WARMING UP...")
        print("   The brain needs at least 5 data points to detect trends.")
        print(f"   Current Depth: {depth}/5")
        print("   Keep the sensor running. Signals will start in ~3-5 minutes.")
    else:
        print("\n✅ STATUS: ACTIVE")
        print("   Sufficient history exists. Signals should be generating.")

print("---------------------------------------")
