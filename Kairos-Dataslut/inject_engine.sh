#!/bin/bash

echo "🔧 INJECTING KAIROS V4 ENGINE (DATASLUT PROTOCOL)..."

# 1. Create Architecture Folders
mkdir -p collectors/batch_01
mkdir -p core/storage
mkdir -p core/infra
mkdir -p data/parquet_buffer

# 2. Write Docker Compose (The Iron)
echo "🏗️  Writing Docker Compose..."
cat <<DOCKER > docker-compose.yml
version: '3.8'
services:
  redpanda:
    image: docker.redpanda.com/redpandadata/redpanda:latest
    container_name: kairos_redpanda
    command:
      - redpanda start
      - --smp 1
      - --memory 1G
      - --reserve-memory 0M
      - --overprovisioned
      - --node-id 0
      - --check=false
    ports:
      - "9092:9092"
      - "9644:9644"
    volumes:
      - redpanda_data:/var/lib/redpanda/data

  postgres:
    image: postgres:15
    container_name: kairos_db
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASS:-kairos}
      POSTGRES_DB: kairos_meta
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:alpine
    container_name: kairos_redis
    ports:
      - "6379:6379"

volumes:
  redpanda_data:
  postgres_data:
DOCKER

# 3. Inject Parquet Writer
echo "💾 Injecting Parquet Storage Engine..."
cat <<PARQUET > core/storage/parquet_writer.py
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
PARQUET

# 4. Inject Base Collector Contract
echo "📜 Injecting Base Collector Contract..."
cat <<COLLECTOR > collectors/base.py
from abc import ABC, abstractmethod
from datetime import datetime
import json
from kafka import KafkaProducer

class KairosCollector(ABC):
    def __init__(self, name):
        self.name = name
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
        except:
            print("⚠️ Warning: Redpanda not found. Running in local mode.")
            self.producer = None

    def send_data(self, metric_name, value, meta=None):
        payload = {
            "ts": datetime.utcnow().isoformat(),
            "source": self.name,
            "metric": metric_name,
            "value": value,
            "meta": meta or {}
        }
        if self.producer:
            self.producer.send('kairos_firehose', value=payload)
        else:
            print(f"[LOCAL] {metric_name}: {value}")
        
    @abstractmethod
    def collect(self):
        pass
COLLECTOR

# 5. Update .gitignore
echo "🛡️  Securing Git..."
if ! grep -q "data/" .gitignore; then echo "data/" >> .gitignore; fi
if ! grep -q "*.parquet" .gitignore; then echo "*.parquet" >> .gitignore; fi
if ! grep -q ".env" .gitignore; then echo ".env" >> .gitignore; fi

echo "✅ KAIROS DATASLUT ENGINE INSTALLED."
