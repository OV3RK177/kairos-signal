import os
import time
import boto3
import requests
import logging
from datetime import datetime, timedelta

# --- CONFIG ---
CH_USER = "default"
CH_PASS = "kairos"
CH_HOST = f"http://{CH_USER}:{CH_PASS}@localhost:8123"
S3_BUCKET = "kairos-deep-archive-v0"
AWS_REGION = "us-east-1"

# --- TUNING ---
CHUNK_MINUTES = 10      # Ship 10 mins at a time (manageable size)
RETENTION_MINUTES = 30  # Keep only 30 mins of data on disk (Aggressive)

logging.basicConfig(filename='shipper.log', level=logging.INFO, format='%(asctime)s - %(message)s')
s3 = boto3.client('s3', region_name=AWS_REGION)

def execute_sql(query):
    r = requests.post(CH_HOST, data=query)
    if r.status_code != 200:
        logging.error(f"SQL Error: {r.text}")
    return r

def ship_and_purge():
    # 1. Target the "Safe Zone" (Data older than 15 mins, younger than 25 mins)
    # We walk backward in time essentially
    target_time = datetime.now() - timedelta(minutes=15)
    start_time = target_time - timedelta(minutes=CHUNK_MINUTES)
    
    fmt = "%Y-%m-%d %H:%M:%S"
    time_filter = f"timestamp >= '{start_time.strftime(fmt)}' AND timestamp < '{target_time.strftime(fmt)}'"
    
    logging.info(f"🔄 Processing window: {start_time.strftime('%H:%M')} -> {target_time.strftime('%H:%M')}")

    # 2. EXPORT & SHIP
    query = f"SELECT * FROM metrics WHERE {time_filter} FORMAT Parquet"
    try:
        response = requests.post(CH_HOST, data=query, stream=True)
        
        if response.status_code == 200 and len(response.content) > 1000:
            filename = f"metrics_{start_time.strftime('%Y%m%d_%H%M')}.parquet"
            s3_key = f"raw_data/{start_time.strftime('%Y/%m/%d')}/{filename}"
            
            s3.upload_fileobj(response.raw, S3_BUCKET, s3_key)
            logging.info(f"✅ Shipped: {filename}")
        else:
            logging.info("⚠️ Window empty or error.")

        # 3. DELETE OLD DATA (Everything older than retention)
        # We delete aggressively to keep disk light
        delete_filter = f"timestamp < now() - INTERVAL {RETENTION_MINUTES} MINUTE"
        execute_sql(f"ALTER TABLE metrics DELETE WHERE {delete_filter}")
        
        # 4. FORCE CLEANUP (The secret sauce)
        # This makes the disk space actually come back
        execute_sql("OPTIMIZE TABLE metrics FINAL")
        logging.info("🧹 Disk Optimized (Space Reclaimed).")

    except Exception as e:
        logging.error(f"Critial Error: {e}")

if __name__ == "__main__":
    logging.info("🚀 RAPID FIREHOSE V15.2 ONLINE")
    while True:
        ship_and_purge()
        # No sleep. Continuous cycle.
