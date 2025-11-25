import os, psycopg2, sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load Config
load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

def audit():
    try:
        print(f"🔌 Connecting to Database...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("\n--- 1. FRESHNESS CHECK (Are we live?) ---")
        cur.execute("SELECT MAX(time) FROM live_metrics")
        last_time = cur.fetchone()[0]
        now = datetime.now(last_time.tzinfo)
        diff = now - last_time
        
        print(f"⏰ Latest Data Point: {last_time}")
        print(f"⏱️ Time Since Update: {diff}")
        
        if diff.total_seconds() > 300:
            print("❌ CRITICAL: Data is stale (> 5 mins old). Collector is DOWN.")
        else:
            print("✅ PASS: Data is flowing live.")

        print("\n--- 2. VOLUME CHECK (Do we have the Titan payload?) ---")
        cur.execute("SELECT count(*) FROM live_metrics")
        total_rows = cur.fetchone()[0]
        print(f"💾 Total Rows Stored: {total_rows:,}")
        
        cur.execute("SELECT count(DISTINCT project) FROM live_metrics WHERE time > NOW() - INTERVAL '24 hours'")
        active_assets = cur.fetchone()[0]
        print(f"📊 Unique Active Assets (24h): {active_assets:,}")
        
        if active_assets < 1000:
            print("❌ CRITICAL: Asset count too low. Titan is failing.")
        else:
            print("✅ PASS: Titan is ingesting massive volume.")

        print("\n--- 3. SECTOR CHECK (Are all engines firing?) ---")
        sectors = {
            "Wall Street": "project LIKE 'tradfi_%'",
            "DePIN Crypto": "project NOT LIKE 'tradfi_%' AND project NOT LIKE '%_node' AND project NOT LIKE '%_lease'",
            "Infrastructure": "project LIKE '%_node' OR project LIKE '%_lease'"
        }
        
        for name, query in sectors.items():
            cur.execute(f"SELECT count(*) FROM live_metrics WHERE {query} AND time > NOW() - INTERVAL '1 hour'")
            count = cur.fetchone()[0]
            status = "✅" if count > 0 else "❌"
            print(f"{status} {name}: {count:,} records (Last Hour)")

        print("\n--- 4. CANARY CHECK (Specific High-Value Targets) ---")
        canaries = ['tradfi_nvda', 'render-token', 'flux_node', 'dimo']
        for c in canaries:
            cur.execute("SELECT value FROM live_metrics WHERE project = %s ORDER BY time DESC LIMIT 1", (c,))
            res = cur.fetchone()
            val = res[0] if res else "MISSING"
            print(f"🐦 {c.upper()}: {val}")

        conn.close()

    except Exception as e:
        print(f"💀 FATAL AUDIT ERROR: {e}")

if __name__ == "__main__":
    audit()
