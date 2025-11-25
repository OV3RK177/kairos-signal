import os, psycopg2
from dotenv import load_dotenv

load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    print("⚡ Creating Snapshot Infrastructure...")
    
    # 1. The Fast Table (Only latest state)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS asset_snapshot (
            project TEXT PRIMARY KEY,
            metric TEXT,
            value DOUBLE PRECISION,
            last_updated TIMESTAMPTZ,
            raw_data JSONB
        );
    """)
    
    # 2. Clean it (in case of old bad data)
    cur.execute("TRUNCATE TABLE asset_snapshot;")
    
    # 3. Prime it (Populate from history so it's not empty)
    print("⚡ Priming Snapshot from History (This takes ~10s)...")
    cur.execute("""
        INSERT INTO asset_snapshot (project, metric, value, last_updated, raw_data)
        SELECT DISTINCT ON (project) project, metric, value, time, raw_data
        FROM live_metrics
        ORDER BY project, time DESC;
    """)
    
    print("✅ Dual-Core DB Ready.")
    conn.close()
except Exception as e: print(f"❌ DB Setup Fail: {e}")
