import clickhouse_connect
from datetime import datetime

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("\n--- 🔍 DATABASE FORENSICS ---")

# 1. TOTAL COUNT
try:
    count = client.query("SELECT count(*) FROM metrics").result_rows[0][0]
    print(f"📊 Total Rows in DB: {count}")
except:
    print("❌ Could not count rows (Table might be missing)")

# 2. CHECK RECENT DATA (Last 5 mins)
try:
    recent = client.query("SELECT count(*) FROM metrics WHERE timestamp > now() - INTERVAL 10 MINUTE").result_rows[0][0]
    print(f"⏱️  Rows last 10 mins: {recent}")
except:
    print("❌ Time query failed")

# 3. CHECK PROJECT SLUGS
try:
    slugs = client.query("SELECT DISTINCT project_slug FROM metrics").result_rows
    slugs_list = [s[0] for s in slugs]
    print(f"🏷️  Project Slugs Found: {slugs_list}")
except:
    print("❌ Could not fetch slugs")

# 4. SAMPLE DATA
if count > 0:
    print("\n📋 LATEST 3 ROWS:")
    res = client.query("SELECT timestamp, project_slug, metric_name, metric_value FROM metrics ORDER BY timestamp DESC LIMIT 3").result_rows
    for r in res:
        print(f"   {r}")
else:
    print("\n⚠️ TABLE IS EMPTY. SWARM IS NOT WRITING.")
print("-----------------------------\n")
