#!/usr/bin/env python3
import time, logging, sys, os, json
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values

# --- HARDCODED CONNECTION STRING (The Fix) ---
# We force TCP (127.0.0.1) to stop the socket error.
DB_URL = "postgresql://doadmin:kairos@127.0.0.1:5432/kairos_meta"

# Import Collectors
sys.path.append('/root/kairos-signal/collectors')
try:
    import deep_helius, social_dark, mev_detector
except ImportError:
    # If imports fail, we still want the script to run its heartbeat
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alpha")

def save_batch(rows):
    if not rows: return
    try:
        # Explicitly connect using the hardcoded URL
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        vals = [(datetime.now(timezone.utc), r[0], r[1], float(r[2]), json.dumps(r[3])) for r in rows]
        execute_values(cur, "INSERT INTO live_metrics (time, project, metric, value, raw_data) VALUES %s", vals)
        conn.commit()
        conn.close()
        logger.info(f"🔥 ALPHA SAVED: {len(rows)} points")
    except Exception as e: 
        logger.error(f"Save Fail: {e}")

def run_alpha_cycle():
    logger.info("🚀 ALPHA v2 CYCLE START")
    data = []
    
    # 1. Heartbeat (Proof of Life)
    data.append(("system", "alpha_heartbeat", 1.0, {"status": "alive"}))

    # 2. Run Collectors (If available)
    try: 
        if 'deep_helius' in sys.modules: data.extend(deep_helius.deep_scan())
    except: pass

    try: 
        if 'social_dark' in sys.modules: data.extend(social_dark.scrape_social())
    except: pass

    try: 
        if 'mev_detector' in sys.modules: data.extend(mev_detector.scan_dex())
    except: pass
    
    save_batch(data)
    logger.info("✅ ALPHA CYCLE END")

if __name__ == "__main__":
    print(f"🔌 Connecting to: {DB_URL}")
    while True:
        run_alpha_cycle()
        time.sleep(60)
