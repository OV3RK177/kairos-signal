import os, psycopg2
from dotenv import load_dotenv
load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DB_URL, sslmode='require')
    conn.autocommit = True
    cur = conn.cursor()
    
    print("⚡ Creating Speed Indexes...")
    # 1. For "Select * where metric='price_usd'"
    cur.execute("CREATE INDEX IF NOT EXISTS idx_metric_time ON live_metrics (metric, time DESC);")
    
    # 2. For "Select * where project='x' and metric='y'" (Charts)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_proj_metric_time ON live_metrics (project, metric, time DESC);")
    
    print("✅ Indexes Applied. Query speed boosted.")
    conn.close()
except Exception as e: print(f"❌ DB Error: {e}")
