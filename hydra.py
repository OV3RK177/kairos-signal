import os
import time
import boto3
import requests
import logging
import json
import pandas as pd
import ollama
from io import BytesIO
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
WORKERS = 4
CHUNK_HOURS = 6
CH_HOST = "http://default:kairos@localhost:8123"
S3_BUCKET = "kairos-deep-archive-v0"
AWS_REGION = "us-east-1"
MODEL = "kimi-k2-thinking:cloud"
FORCE_START_DATE = datetime(2025, 10, 1)

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler("hydra_smart.log")]
)

s3 = boto3.client('s3', region_name=AWS_REGION)

def get_time_range():
    start = FORCE_START_DATE
    end = datetime.now() - timedelta(hours=2)
    return start, end

def analyze_chunk(df):
    if df.empty: return "No Data"
    stats = df.describe().to_dict()
    summary = { "rows": len(df), "metric_stats": str(stats.get('metric_value', 'N/A'))[:200] }
    prompt = f"Analyze summary: {json.dumps(summary)}. Rate anomaly 0-10."
    try:
        response = ollama.chat(model=MODEL, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
    except:
        return "Analysis Failed"

def process_chunk(time_tuple):
    start, end = time_tuple
    logging.info(f"🔥 PROCESSING SECTOR: {start} -> {end}")
    
    fmt = "%Y-%m-%d %H:%M:%S"
    query_time = f"timestamp >= '{start.strftime(fmt)}' AND timestamp < '{end.strftime(fmt)}'"
    
    try:
        # 1. FETCH
        query = f"SELECT * FROM metrics WHERE {query_time} FORMAT CSVWithNames"
        response = requests.post(CH_HOST, data=query)
        
        if response.status_code != 200 or len(response.content) < 100:
            logging.info(f"⚠️ Sector Empty: {start}. Deleting.")
            requests.post(CH_HOST, data=f"ALTER TABLE metrics DELETE WHERE {query_time}")
            return

        # 2. ANALYZE
        df = pd.read_csv(BytesIO(response.content))
        insight = analyze_chunk(df)
        logging.info(f"🧠 Insight for {start}: {insight[:50]}...")
        
        # 3. SHIP
        parquet_buffer = BytesIO()
        df.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0)
        
        filename = f"backlog_{start.strftime('%Y%m%d_%H%M')}.parquet"
        s3.put_object(Body=parquet_buffer, Bucket=S3_BUCKET, Key=f"raw_data/{filename}")
        s3.put_object(Body=json.dumps({"insight": insight}), Bucket=S3_BUCKET, Key=f"insights/{filename}_insight.json")

        # 4. DELETE
        requests.post(CH_HOST, data=f"ALTER TABLE metrics DELETE WHERE {query_time}")
        logging.info(f"🗑️  WIPED: {start}")
            
    except Exception as e:
        logging.error(f"Failed {start}: {e}")

def generate_tasks(start, end):
    tasks = []
    current = start
    while current < end:
        next_step = current + timedelta(hours=CHUNK_HOURS)
        tasks.append((current, next_step))
        current = next_step
    return tasks

if __name__ == "__main__":
    print("🐲 SMART HYDRA V2.2 (NANO EDITION) ONLINE.")
    start, end = get_time_range()
    tasks = generate_tasks(start, end)
    print(f"⚡ Processing {len(tasks)} sectors...")
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        executor.map(process_chunk, tasks)
