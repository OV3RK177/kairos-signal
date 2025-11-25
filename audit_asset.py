import os, psycopg2
from dotenv import load_dotenv

load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    print("🔌 Connecting to the Vault...")
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()

    # 1. EXACT ROW COUNT (Approximate for speed on big DBs)
    cur.execute("SELECT reltuples::bigint AS estimate FROM pg_class WHERE relname = 'live_metrics';")
    rows = cur.fetchone()[0]
    
    # 2. ACTUAL DISK SIZE
    cur.execute("SELECT pg_size_pretty(pg_total_relation_size('live_metrics'));")
    size = cur.fetchone()[0]

    # 3. LATEST HEARTBEAT
    cur.execute("SELECT time, project, value FROM live_metrics ORDER BY time DESC LIMIT 1;")
    last = cur.fetchone()

    # 4. BREAKDOWN
    cur.execute("SELECT project, COUNT(*) as c FROM live_metrics WHERE time > NOW() - INTERVAL '1 hour' GROUP BY project ORDER BY c DESC LIMIT 5;")
    top = cur.fetchall()

    print("\n--- 🏛️ KAIROS ASSET AUDIT ---")
    print(f"💰 TOTAL DATA POINTS:  {rows:,} (Approx)")
    print(f"💾 TOTAL DISK USAGE:   {size}")
    print(f"💓 LATEST INGESTION:   {last[0]} | {last[1]} | {last[2]}")
    print("\n--- TOP SOURCES (LAST 1HR) ---")
    for t in top:
        print(f"📊 {t[0]}: {t[1]} records")

    conn.close()

except Exception as e:
    print(f"❌ Audit Failed: {e}")
