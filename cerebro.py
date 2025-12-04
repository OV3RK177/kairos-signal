import os
import time
import json
import logging
import boto3
import pandas as pd
from boto3.s3.transfer import TransferConfig
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# --- CONFIGURATION ---
# UPDATE THIS if your volume is mounted elsewhere. 
# Using local dir as fallback if /data/buffer doesn't exist.
BUFFER_DIR = "/mnt/volume_nyc3_01/buffer" if os.path.exists("/mnt/volume_nyc3_01/buffer") else "./buffer"
BUCKET_NAME = "kairos-archive-v1" 
AWS_REGION = "us-east-1"
THREADS = 10

# --- LOGGING ---
logging.basicConfig(
    filename='cerebro.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(message)s'
)

# --- S3 SETUP ---
s3 = boto3.client('s3', region_name=AWS_REGION)
config = TransferConfig(max_concurrency=THREADS, use_threads=True)

def ship_data():
    """Checks buffer, uploads to S3, and DELETES local files."""
    if not os.path.exists(BUFFER_DIR):
        os.makedirs(BUFFER_DIR)
        
    # List parquet files
    files = [f for f in os.listdir(BUFFER_DIR) if f.endswith('.parquet')]
    
    if not files:
        return

    logging.info(f"🔥 Shipping {len(files)} files from {BUFFER_DIR}...")
    
    def upload_worker(file):
        local_path = os.path.join(BUFFER_DIR, file)
        s3_key = f"raw_data/{datetime.now().strftime('%Y/%m/%d')}/{file}"
        try:
            # Upload
            s3.upload_file(local_path, BUCKET_NAME, s3_key, Config=config)
            # DELETE
            os.remove(local_path)
            logging.info(f"✅ Shipped & Deleted: {file}")
        except Exception as e:
            logging.error(f"❌ Ship Failed: {file} - {e}")

    # Parallel Uploads
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        executor.map(upload_worker, files)

def main():
    print(f"🚀 CEREBRO V15.0 ONLINE. Monitoring {BUFFER_DIR}")
    logging.info("Cerebro Started.")
    
    while True:
        try:
            # 1. Ship Data (Priority: Save Disk)
            ship_data()
            
            # 2. Wait (Heartbeat)
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("🛑 Stopping.")
            break
        except Exception as e:
            logging.error(f"CRITICAL ERROR: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
