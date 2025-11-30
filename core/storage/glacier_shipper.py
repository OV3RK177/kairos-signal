import boto3
import os
import glob
import time
import sys
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError

load_dotenv()
LOCAL_VAULT_PATH = os.getenv("KAIROS_STORAGE_PATH", "/mnt/volume_nyc3_01/kairos_data")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
STORAGE_CLASS = "DEEP_ARCHIVE"

def upload_to_glacier():
    if not BUCKET_NAME:
        print("❌ ERROR: AWS_BUCKET_NAME not found in .env")
        sys.exit(1)

    print(f"❄️  GLACIER SHIPPER ONLINE.")
    print(f"📂 Scanning: {LOCAL_VAULT_PATH}")
    print(f"☁️  Target: s3://{BUCKET_NAME}")
    
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION")
        )
    except Exception as e:
        print(f"❌ AWS Init Failed: {e}")
        return

    while True:
        files = glob.glob(f"{LOCAL_VAULT_PATH}/*.parquet")
        if not files:
            time.sleep(60)
            continue
            
        print(f"📦 Found {len(files)} files to ship.")
        for local_file in files:
            filename = os.path.basename(local_file)
            s3_key = f"raw_ingest/{filename}"
            try:
                s3.upload_file(local_file, BUCKET_NAME, s3_key, ExtraArgs={'StorageClass': STORAGE_CLASS})
                print(f"✅ Archived: {filename}")
                os.remove(local_file)
            except Exception as e:
                print(f"⚠️ Upload Failed: {e}")
                time.sleep(5)
        time.sleep(10)

if __name__ == "__main__":
    upload_to_glacier()
