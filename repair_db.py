import os, psycopg2
from dotenv import load_dotenv
load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    # 1. Connect
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    print("✅ Connected to Local DB.")

    # 2. Ensure Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_metrics (
            time TIMESTAMPTZ NOT NULL, 
            project TEXT NOT NULL, 
            metric TEXT NOT NULL, 
            value DOUBLE PRECISION, 
            raw_data JSONB
        );
    """)

    # 3. Rebuild View (For Dashboard Speed)
    print("⚡ Rebuilding Dashboard View...")
    cur.execute("DROP VIEW IF EXISTS market_snapshot CASCADE;")
    cur.execute("""
        CREATE OR REPLACE VIEW market_snapshot AS
        SELECT DISTINCT ON (project) 
            project, 
            value as price,
            raw_data,
            time as last_updated
        FROM live_metrics 
        WHERE metric = 'price_usd'
        ORDER BY project, time DESC;
    """)
    
    print("✅ Repair Complete.")
    conn.close()
except Exception as e:
    print(f"❌ Repair Failed: {e}")
