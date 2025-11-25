import os, psycopg2
from dotenv import load_dotenv
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()
    
    # Check Compression
    print("\n--- COMPRESSION STATUS ---")
    cur.execute("SELECT hypertable_name, compression_enabled FROM timescaledb_information.hypertables WHERE hypertable_name = 'live_metrics';")
    row = cur.fetchone()
    if row and row[1]: print("✅ Compression is ENABLED.")
    else: 
        print("⚠️ Compression OFF. Attempting to enable...")
        try:
            cur.execute("ALTER TABLE live_metrics SET (timescaledb.compress, timescaledb.compress_segmentby = 'project, metric', timescaledb.compress_orderby = 'time DESC');")
            cur.execute("SELECT add_compression_policy('live_metrics', INTERVAL '1 day');")
            conn.commit()
            print("✅ Compression ENABLED via Audit Script.")
        except Exception as e: print(f"❌ Could not enable compression: {e}")

    # Check Volume
    print("\n--- VOLUME AUDIT (Last 1 Hour) ---")
    cur.execute("SELECT count(*) FROM live_metrics WHERE time > NOW() - INTERVAL '1 hour';")
    count = cur.fetchone()[0]
    print(f"📊 Data Points (1h): {count:,}")
    print(f"📈 Projected Daily:  {count*24:,}")
    
    if count * 24 > 30000000: print("✅ TARGET REACHED (30M+ Daily)")
    else: print("⚠️ TARGET MISS (Check Collector Logs)")
    
    conn.close()
except Exception as e: print(f"Audit Fail: {e}")
