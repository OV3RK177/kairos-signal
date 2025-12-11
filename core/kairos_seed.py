import clickhouse_connect
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random

# --- CONFIG ---
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')
DAYS_TO_GENERATE = 7
INTERVAL_MINUTES = 10

print(f"🌱 KAIROS SEEDER: Generating {DAYS_TO_GENERATE} days of synthetic market data...")

try:
    client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
except Exception as e:
    print(f"❌ DB FAIL: {e}"); exit(1)

# 1. GENERATE TIME SERIES
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=DAYS_TO_GENERATE)
timestamps = pd.date_range(start=start_time, end=end_time, freq=f'{INTERVAL_MINUTES}min')

steps = len(timestamps)
print(f"📊 Steps to generate: {steps}")

# 2. GENERATE RANDOM WALK PRICE
# Start at 96k, random walk with volatility
price = 96000.0
prices = []
volumes = []

for _ in range(steps):
    change = np.random.normal(0, 50) # Random $ swing
    price += change
    prices.append(price)
    # Random volume between 10M and 100M
    volumes.append(random.uniform(10000000, 100000000))

# 3. PREPARE DATA FOR INSERT
data = []
for i in range(steps):
    # Insert Price
    data.append([timestamps[i].to_pydatetime(), 'BTC_USD', 'price_usd', float(prices[i])])
    # Insert Volume
    data.append([timestamps[i].to_pydatetime(), 'BTC_USD', 'volume_24h', float(volumes[i])])

# 4. INSERT BATCH
print("💾 Injecting data into ClickHouse...")
try:
    client.insert('metrics', data, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
    print("✅ SEED COMPLETE. The Brain now has memory.")
except Exception as e:
    print(f"❌ INSERT FAILED: {e}")
