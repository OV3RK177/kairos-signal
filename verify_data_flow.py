import clickhouse_connect
import time

print("🔍 VERIFYING SENSOR DATA FLOW...", flush=True)
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

# Query for ANY valid price data in the last 2 minutes
query = """
SELECT timestamp, metric_name, metric_value 
FROM metrics 
WHERE project_slug='stock_swarm' 
  AND metric_value > 0.01 
  AND timestamp >= now() - INTERVAL 2 MINUTE
ORDER BY timestamp DESC 
LIMIT 5
"""

results = client.query(query).result_rows

if results:
    print(f"✅ SUCCESS: Found {len(results)} valid data points in the last 2 minutes.")
    for row in results:
        print(f"   {row[0]} | {row[1]} : ")
    print("\n🚀 ACTION: Data is flowing. You can now restart 'kairos-cortex'.")
else:
    print("❌ FAILURE: Sensor is still writing ZEROS or NO DATA.")
    print("   Please check '/var/log/syslog' or 'journalctl -u kairos-sensor' for API errors.")
