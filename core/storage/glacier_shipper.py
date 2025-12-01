import boto3
import os
import glob
import time
import sys
from dotenv import load_dotenv

load_dotenv()

# CONFIG: Scan the ENTIRE volume root
ROOT_VAULT = "/mnt/volume_nyc3_01"
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
# Deep Archive = -bash.99/TB/Month (Cheapest)
STORAGE_CLASS = "DEEP_ARCHIVE"

def upload_to_glacier():
    if not BUCKET_NAME:
        print("❌ ERROR: AWS_BUCKET_NAME missing.")
        sys.exit(1)

    print(f"❄️  GLACIER SHIPPER ONLINE.")
    print(f"📂 Target Root: {ROOT_VAULT}")
    
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION")
        )
    except Exception as e:
        print(f"❌ AWS Connect Error: {e}")
        return

    while True:
        # RECURSIVE SCAN: Finds .parquet in ALL subfolders (Legacy + Live)
        files = glob.glob(f"{ROOT_VAULT}/**/*.parquet", recursive=True)
        
        if not files:
            print("zzz... Vault clean. Sleeping 60s.")
            time.sleep(60)
            continue
            
        print(f"📦 Found {len(files)} files to ship.")
        
        for local_file in files:
            try:
                # Create a clean S3 key (folder structure)
                # e.g. kairos_legacy_processed/table_part_0.parquet
                relative_path = os.path.relpath(local_file, ROOT_VAULT)
                s3_key = f"raw_ingest/{relative_path}"
                
                print(f"🚀 Uploading: {relative_path}...")
                
                s3.upload_file(
                    local_file, 
                    BUCKET_NAME, 
                    s3_key, 
                    ExtraArgs={'StorageClass': STORAGE_CLASS}
                )
                
                print(f"✅ Archived: {s3_key}")
                
                # DELETE LOCAL (The Purge)
                os.remove(local_file)
                
            except Exception as e:
                print(f"⚠️ Upload Failed: {e}")
                time.sleep(5)

        # Breathe between batches
        time.sleep(5)

if __name__ == "__main__":
    upload_to_glacier()
