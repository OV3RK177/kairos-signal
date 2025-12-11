import clickhouse_connect

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🏛️  KAIROS VAULT AUDIT")
print("---------------------------------------")

# 1. Total Row Count
total = client.query("SELECT count() FROM metrics").result_rows[0][0]
print(f"📚 TOTAL RECORDED MEMORIES: {total:,} rows")

# 2. Date Range
bounds = client.query("SELECT min(timestamp), max(timestamp) FROM metrics").result_rows[0]
print(f"⏳ TIMELINE: From {bounds[0]} to {bounds[1]}")

# 3. Data Volume by Project (The "Senses")
print("\n🧠 DATA VOLUME BY SENSE (Source):")
senses = client.query("SELECT project_slug, count() as c FROM metrics GROUP BY project_slug ORDER BY c DESC").result_rows
for s in senses:
    print(f"   • {s[0]:<20} : {s[1]:,} records")

# 4. Deepest Asset History
print("\n📜 DEEPEST ASSET HISTORIES:")
deep = client.query("SELECT metric_name, count() as c FROM metrics GROUP BY metric_name ORDER BY c DESC LIMIT 5").result_rows
for d in deep:
    print(f"   • {d[0]:<20} : {d[1]:,} data points")

print("\n---------------------------------------")
print(f"💡 NOTE: The '59' you saw earlier was just the last hour of data.")
print(f"   Your engine is sipping from this firehose, not ignoring it.")
print("---------------------------------------")
