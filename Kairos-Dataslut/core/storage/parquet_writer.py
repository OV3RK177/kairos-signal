import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import os
import json
from kafka import KafkaConsumer

# Config
BATCH_SIZE = 10000
OUTPUT_DIR = "data/parquet_buffer"

def write_batch(data_list):
    if not data_list:
        return
    
    df = pd.DataFrame(data_list)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/kairos_batch_{timestamp}.parquet"
    
    # Write compressed parquet
    table = pa.Table.from_pandas(df)
    pq.write_table(table, filename, compression='snappy')
    print(f"💾 SAVED: {filename} | Rows: {len(df)}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    consumer = KafkaConsumer(
        'kairos_firehose',
        bootstrap_servers=['localhost:9092'],
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='latest'
    )
    
    buffer = []
    print("👁️  PARQUET WRITER ACTIVE. Waiting for data...")
    
    for message in consumer:
        buffer.append(message.value)
        
        if len(buffer) >= BATCH_SIZE:
            write_batch(buffer)
            buffer = []

if __name__ == "__main__":
    main()
