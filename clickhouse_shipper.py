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
S3_BUCKET = "kairos-deep-archive-v0"  # CORRECTED
AWS_REGION = "us-east-1"

logging.basicConfig(filename='shipper.log', level=logging.INFO, format='%(asctime)s - %(message)s')
s3 = boto3.client('s3', region_name=AWS_REGION)

def ship_and_clean():
    query = "SELECT * FROM metrics WHERE timestamp > now() - INTERVAL 1 HOUR FORMAT Parquet"
    try:
        response = requests.post(CH_HOST, data=query, stream=True)
        if response.status_code == 200:
            if len(response.content) < 10: return

            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            s3_key = f"raw_data/{datetime.now().strftime('%Y/%m/%d')}/{filename}"
            
            s3.upload_fileobj(response.raw, S3_BUCKET, s3_key)
            logging.info(f"✅ Uploaded {filename} to {S3_BUCKET}")
            
            # NIGHT MODE: DELETE DATA OLDER THAN 2 HOURS
            requests.post(CH_HOST, data="ALTER TABLE metrics DELETE WHERE timestamp < now() - INTERVAL 2 HOUR")
            logging.info("🧹 Cleaned old DB data.")
            
        else:
            logging.error(f"DB Error: {response.text}")
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    logging.info(f"🚀 Night Mode Shipper Online -> {S3_BUCKET}")
    while True:
        ship_and_clean()
        time.sleep(60)
