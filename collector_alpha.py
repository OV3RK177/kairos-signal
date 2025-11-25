#!/usr/bin/env python3
import time, logging, sys, os, json
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Import Collectors
sys.path.append('/root/kairos-sprint/collectors')
import deep_helius, social_dark, mev_detector

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alpha")

def save_batch(rows):
    if not rows: return
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        cur = conn.cursor()
        vals = [(datetime.now(timezone.utc), r[0], r[1], float(r[2]), json.dumps(r[3])) for r in rows]
        execute_values(cur, "INSERT INTO live_metrics (time, project, metric, value, raw_data) VALUES %s", vals)
        conn.commit()
        conn.close()
        logger.info(f"🔥 ALPHA SAVED: {len(rows)} points")
    except Exception as e: logger.error(f"Save Fail: {e}")

def run_alpha_cycle():
    logger.info("🚀 ALPHA v2 CYCLE START")
    data = []
    
    # 1. Deep Scan (Helius)
    try: data.extend(deep_helius.deep_scan())
    except Exception as e: logger.error(f"Helius Fail: {e}")

    # 2. Social Sentiment
    try: data.extend(social_dark.scrape_social())
    except Exception as e: logger.error(f"Social Fail: {e}")

    # 3. DEX Scanner
    try: data.extend(mev_detector.scan_dex())
    except Exception as e: logger.error(f"DEX Fail: {e}")
    
    save_batch(data)
    logger.info("✅ ALPHA CYCLE END")

if __name__ == "__main__":
    while True:
        run_alpha_cycle()
        time.sleep(60)
