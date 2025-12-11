import clickhouse_connect
from tabulate import tabulate

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("🏛️  KAIROS VAULT INVENTORY (FULL AUDIT)")
print("=========================================================================================")

# Get stats for EVERY metric in the system
query = """
SELECT 
    project_slug, 
    metric_name, 
    count() as total_rows, 
    min(timestamp) as first_seen, 
    max(timestamp) as last_seen
FROM metrics 
GROUP BY project_slug, metric_name 
ORDER BY total_rows DESC
"""

rows = client.query(query).result_rows

if not rows:
    print("❌ CRITICAL: Database is EMPTY.")
else:
    # Format nicely
    table_data = []
    for r in rows:
        # Calculate duration in hours
        duration = (r[4] - r[3]).total_seconds() / 3600
        table_data.append([
            r[0],           # Project
            r[1],           # Metric
            f"{r[2]:,}",    # Count
            f"{duration:.1f} hrs", # Duration
            str(r[3])[:16], # Start
            str(r[4])[:16]  # End
        ])
    
    print(tabulate(table_data, headers=["Project (Source)", "Metric", "Count", "History", "Start Time", "End Time"], tablefmt="simple"))

print("=========================================================================================")
