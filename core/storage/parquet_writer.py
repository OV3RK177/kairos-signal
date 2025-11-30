import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import os
import json
import sys
from kafka import KafkaConsumer
from dotenv import load_dotenv

load_dotenv()

# CONFIG: HFT TUNING
# 50,000 rows = ~2-5MB parquet file.
# At peak Polygon volume, this writes every ~5-10 seconds. Perfect balance.
BATCH_SIZE = 100 
OUTPUT_DIR = os.getenv("KAIROS_STORAGE_PATH", "/mnt/volume_nyc3_01/kairos_data")

def write_batch(data_list):
    if not data_list:
        return
    
    try:
        df = pd.DataFrame(data_list)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f") # Added microsecond precision
        filename = f"{OUTPUT_DIR}/kairos_hft_{timestamp}.parquet"
        
        # PyArrow is faster than Pandas for high volume
        table = pa.Table.from_pandas(df)
        pq.write_table(table, filename, compression='snappy')
        
        print(f"💾 SAVED: {filename} | Rows: {len(df)} | HFT Mode")
    except Exception as e:
        print(f"❌ WRITE ERROR: {e}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"👁️  PARQUET WRITER (HFT EDITION) ACTIVE. Buffer: {BATCH_SIZE}")
    
    try:
        consumer = KafkaConsumer(
            'kairos_firehose',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='kairos_archiver_v2', # New group ID to force fresh start
            fetch_min_bytes=1048576, # 1MB minimum fetch for efficiency
            fetch_max_wait_ms=500    # Max wait 500ms
        )
    except Exception as e:
        print(f"❌ KAFKA CONNECTION FAILED: {e}")
        return

    buffer = []
    print("👂 Listening on channel 'kairos_firehose'...")
    
    for message in consumer:
        buffer.append(message.value)
        
        if len(buffer) >= BATCH_SIZE:
            write_batch(buffer)
            buffer = []

if __name__ == "__main__":
    main()
