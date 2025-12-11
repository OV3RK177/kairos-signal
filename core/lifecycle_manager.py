import clickhouse_connect
import psycopg2
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# CONFIG
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'kairos') 

ARCHIVE_DIR = "archive"
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)

RETENTION_DAYS = 2  # Keep 2 days hot for AI, freeze the rest

def archive_physical_data():
    print("❄️  Freezing Physical Data (ClickHouse)...")
    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
        
        # 1. Select Old Data
        query = f"SELECT * FROM metrics WHERE timestamp < now() - INTERVAL {RETENTION_DAYS} DAY"
        df = client.query_df(query)
        
        if not df.empty:
            # 2. Compress to Parquet
            filename = f"{ARCHIVE_DIR}/physical_{datetime.now().strftime('%Y%m%d_%H%M')}.parquet"
            df.to_parquet(filename, engine='pyarrow', compression='snappy')
            print(f"📦 Archived {len(df)} rows to {filename}")
            
            # 3. Delete from DB (Free up disk)
            # ClickHouse deletion is heavy, we do it carefully
            client.command(f"ALTER TABLE metrics DELETE WHERE timestamp < now() - INTERVAL {RETENTION_DAYS} DAY")
            print("🗑️  Purged old data from Hot Storage.")
        else:
            print("✅ No stale physical data found.")
            
    except Exception as e:
        print(f"Physical Archive Error: {e}")

def archive_financial_data():
    print("❄️  Freezing Financial Data (Postgres)...")
    try:
        conn = psycopg2.connect(host=PG_HOST, database="kairos_meta", user="doadmin", password=PG_PASS)
        
        # 1. Select Old Data
        query = f"SELECT * FROM live_metrics WHERE time < NOW() - INTERVAL '{RETENTION_DAYS} days'"
        df = pd.read_sql(query, conn)
        
        if not df.empty:
            # 2. Compress
            filename = f"{ARCHIVE_DIR}/financial_{datetime.now().strftime('%Y%m%d_%H%M')}.parquet"
            df.to_parquet(filename, engine='pyarrow', compression='snappy')
            print(f"📦 Archived {len(df)} rows to {filename}")
            
            # 3. Delete
            cur = conn.cursor()
            cur.execute(f"DELETE FROM live_metrics WHERE time < NOW() - INTERVAL '{RETENTION_DAYS} days'")
            conn.commit()
            print("🗑️  Purged old data from Hot Storage.")
        else:
            print("✅ No stale financial data found.")
            
        conn.close()
    except Exception as e:
        print(f"Financial Archive Error: {e}")

if __name__ == "__main__":
    print(f"--- LIFECYCLE MANAGER STARTING ({datetime.now()}) ---")
    archive_physical_data()
    archive_financial_data()
    print("--- LIFECYCLE COMPLETE ---")
