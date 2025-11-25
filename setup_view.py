import os, psycopg2
from dotenv import load_dotenv
load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DB_URL, sslmode='require')
    conn.autocommit = True
    cur = conn.cursor()
    print("⚡ Rebuilding Golden View...")
    cur.execute("DROP VIEW IF EXISTS market_snapshot CASCADE;")
    cur.execute("""
        CREATE OR REPLACE VIEW market_snapshot AS
        SELECT 
            p.project,
            p.value as price,
            COALESCE(v.value, 0) as volume,
            COALESCE(c.value, 0) as change_24h,
            p.time as last_updated
        FROM 
            (SELECT DISTINCT ON (project) project, value, time FROM live_metrics WHERE metric = 'price_usd' ORDER BY project, time DESC) p
        LEFT JOIN 
            (SELECT DISTINCT ON (project) project, value FROM live_metrics WHERE metric = 'volume_24h' ORDER BY project, time DESC) v 
            ON p.project = v.project
        LEFT JOIN 
            (SELECT DISTINCT ON (project) project, value FROM live_metrics WHERE metric = 'change_24h' ORDER BY project, time DESC) c 
            ON p.project = c.project;
    """)
    print("✅ View Active.")
    conn.close()
except Exception as e: print(f"❌ DB Error: {e}")
