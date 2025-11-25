import os, psycopg2
from dotenv import load_dotenv
load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DB_URL, sslmode='require')
    conn.autocommit = True
    cur = conn.cursor()
    
    print("⚡ Building Golden Index (This might take 30s)...")
    # This specific order matches "DISTINCT ON (project) ... ORDER BY project, time DESC"
    cur.execute("CREATE INDEX IF NOT EXISTS idx_project_time_desc ON live_metrics (project, time DESC);")
    
    print("⚡ Analyzing Table Statistics...")
    cur.execute("ANALYZE live_metrics;")
    
    print("✅ Optimization Complete.")
    conn.close()
except Exception as e: print(f"❌ DB Error: {e}")
