import clickhouse_connect
from tabulate import tabulate

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🏛️  KAIROS VAULT SUMMARY (Grouped by Source)")
print("==================================================================================")

# Group by project_slug (Source) to see high-level volumes
query = """
SELECT 
    project_slug, 
    count(DISTINCT metric_name) as unique_metrics, 
    count() as total_rows, 
    min(timestamp) as start_time, 
    max(timestamp) as end_time
FROM metrics 
GROUP BY project_slug 
ORDER BY total_rows DESC 
LIMIT 25
"""

rows = client.query(query).result_rows

table = []
for r in rows:
    # Calculate Data Duration
    hours = (r[4] - r[3]).total_seconds() / 3600
    
    table.append([
        r[0],              # Source Name (e.g., BTC_USD, FRED, NEWS)
        r[1],              # Unique Metrics
        f"{r[2]:,}",       # Total Data Points
        f"{hours:.1f} hr", # Duration
        str(r[4])[:16]     # Last Update
    ])

print(tabulate(table, headers=["Source", "Metrics", "Total Points", "History", "Last Update"], tablefmt="simple"))
print("==================================================================================")
