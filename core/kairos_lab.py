import clickhouse_connect
import pandas as pd
import numpy as np
import os

CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')

print("🧪 KAIROS LAB: INITIALIZING...")

# CONNECT WITH HIGH MEMORY SETTINGS
try:
    client = clickhouse_connect.get_client(
        host=CH_HOST, 
        port=8123, 
        username='default', 
        password=CH_PASS,
        settings={'max_memory_usage': 10000000000} # 10GB Limit
    )
except:
    print("❌ DB Connect Fail"); exit(1)

# 1. INTEGRITY CHECK (High Mem)
print("\n🔍 STEP 1: DATA INTEGRITY AUDIT (Last 24 Hours)")
try:
    q = """
    SELECT 
        metric_name, 
        count() as ticks
    FROM metrics 
    WHERE timestamp > now() - INTERVAL 24 HOUR
    GROUP BY metric_name 
    ORDER BY ticks DESC 
    LIMIT 10
    """
    print(client.query_df(q))
except Exception as e:
    print(f"⚠️ Audit Failed: {e}")

# 2. CORRELATION (High Mem)
print("\n🔗 STEP 2: SIGNAL CORRELATION")
try:
    q = """
    SELECT 
        toStartOfHour(timestamp) as hour,
        metric_name,
        avg(metric_value) as value
    FROM metrics 
    WHERE timestamp > now() - INTERVAL 24 HOUR
      AND metric_name IN ('price_usd', 'volume_24h', 'sentiment_score')
    GROUP BY hour, metric_name
    ORDER BY hour ASC
    """
    df = client.query_df(q)
    if not df.empty:
        p = df.pivot_table(index='hour', columns='metric_name', values='value').fillna(0)
        print(p.corr())
    else:
        print("No Data for Correlation.")
except Exception as e:
    print(f"⚠️ Correlation Failed: {e}")

print("\n🧪 LAB RUN COMPLETE.")
