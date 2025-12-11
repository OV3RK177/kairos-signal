import clickhouse_connect
import requests
import time
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# --- LOGGING ---
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler("logs/system.log"), logging.StreamHandler()]
)
def log(msg): logging.info(msg)

# --- CONFIG ---
# HARDCODED FIX: Ignore environment variables. Force Docker networking.
CH_HOST = 'clickhouse-server' 
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')

client = None

def connect_db():
    global client
    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
        client.query("CREATE TABLE IF NOT EXISTS sentiment_stream (timestamp DateTime, source String, headline String, sentiment_score Float32, url String) ENGINE = MergeTree() ORDER BY timestamp")
        log(f"✅ Connected to DB at {CH_HOST}")
        return True
    except Exception as e:
        log(f"❌ DB Connect Fail: {e}")
        return False

def safe_insert(table, data, cols):
    global client
    try:
        if client is None: connect_db()
        client.insert(table, data, column_names=cols)
        log(f"✅ Inserted {len(data)} rows into {table}")
    except Exception as e:
        log(f"⚠️ Insert Error: {e}")
        connect_db()

def run_aggregator():
    log(f"🚀 AGGREGATOR ONLINE. Force Target: {CH_HOST}")
    
    # Initial Connect
    while not connect_db():
        time.sleep(5)

    # Main Loop (Heartbeat)
    while True:
        try:
            # Simple heartbeat to keep connection alive
            client.command('SELECT 1')
            time.sleep(10)
        except Exception as e:
            log(f"❌ Connection Lost: {e}")
            connect_db()
            time.sleep(5)

if __name__ == "__main__":
    run_aggregator()
