#!/usr/bin/env python3
import os, time, json, logging, requests, psycopg2, schedule, sys
from datetime import datetime, timezone
from psycopg2 import pool
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import colorlog
import urllib3

urllib3.disable_warnings()
load_dotenv("/root/kairos-signal/.env")

# LOGGING
handler = logging.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(asctime)s - %(message)s', log_colors={'INFO':'green','ERROR':'red','WARNING':'yellow'}))
logger = logging.getLogger("kairos")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# --- HARDCODED CONFIG ---
DB_URL = "postgresql://doadmin:kairos@127.0.0.1:5432/kairos_meta"
# Hardcoded Key from your previous inputs
POLYGON_KEY = "tMpcS7ihrpro3APH9_S3GP0LBpxN7Z6j" 
GRASS_TOKEN = os.getenv("GRASS_AUTH_TOKEN")

# DB POOL
try:
    DB_POOL = pool.ThreadedConnectionPool(2, 10, dsn=DB_URL)
    logger.info("✅ DB Pool Online (TCP Forced)")
except Exception as e:
    logger.critical(f"❌ DB Init Fail: {e}")
    sys.exit(1)

def save_batch(rows):
    if not rows or not DB_POOL: return
    conn = None
    try:
        conn = DB_POOL.getconn()
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS live_metrics (time TIMESTAMPTZ NOT NULL, project TEXT NOT NULL, metric TEXT NOT NULL, value DOUBLE PRECISION, raw_data JSONB);")
            
            vals = []
            for r in rows:
                try: vals.append((datetime.now(timezone.utc), r[0], r[1], float(r[2]), json.dumps(r[3])))
                except: pass
            
            if vals:
                execute_values(cur, "INSERT INTO live_metrics (time, project, metric, value, raw_data) VALUES %s", vals)
                conn.commit()
                logger.info(f"🔥 BATCH: {len(vals)} saved")
    except Exception as e:
        logger.error(f"Save Error: {e}")
        if conn: conn.rollback()
    finally:
        if conn: DB_POOL.putconn(conn)

# --- TASKS ---

def task_wallstreet():
    if not POLYGON_KEY: return
    try:
        r = requests.get(f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?apiKey={POLYGON_KEY}", timeout=60)
        if r.status_code == 200:
            batch = []
            for t in r.json().get('tickers', []):
                vol = t.get('day', {}).get('v', 0) or t.get('prevDay', {}).get('v', 0)
                price = t.get('day', {}).get('c') or t.get('prevDay', {}).get('c')
                if vol > 10000 and price:
                    batch.append((f"tradfi_{t['ticker'].lower()}", "price_usd", price, {"vol": vol, "chg": t.get('todaysChangePerc', 0)}))
                if len(batch) >= 2000: 
                    save_batch(batch)
                    batch = []
            save_batch(batch)
            logger.info("✅ Wall St Ingested")
        else:
            logger.error(f"Polygon Fail: {r.status_code}")
    except Exception as e: 
        logger.error(f"Wall St Error: {e}")

def task_crypto():
    try:
        for p in [1, 2]:
            r = requests.get("https://api.coingecko.com/api/v3/coins/markets", params={"vs_currency":"usd","per_page":250,"page":p}, timeout=15)
            if r.status_code == 200:
                batch = []
                for c in r.json():
                    batch.append((c['id'], "price_usd", c['current_price'], {"vol": c['total_volume'], "chg": c.get('price_change_percentage_24h', 0)}))
                save_batch(batch)
        logger.info(f"✅ Crypto Ingested") 
    except: pass

def task_census():
    batch = []
    try:
        r = requests.get("https://api.runonflux.io/daemon/viewdeterministiczelnodelist", timeout=15)
        nodes = r.json().get('data', [])
        batch.append(("flux", "total_nodes", len(nodes), {}))
    except: pass
    
    try:
        r = requests.get("https://discovery.mysterium.network/api/v3/proposals", timeout=15)
        nodes = r.json()
        batch.append(("mysterium", "total_nodes", len(nodes), {}))
    except: pass

    try:
        r = requests.post("https://identity-api.dimo.zone/query", json={'query': "query { vehicles (first: 1) { totalCount } }"}, timeout=10)
        batch.append(("dimo", "vehicles", r.json()['data']['vehicles']['totalCount'], {}))
    except: pass

    save_batch(batch)
    logger.info("🚜 Census Updated")

def run_cycle():
    logger.info("🚀 START v25.0")
    task_wallstreet()
    task_crypto()
    task_census()
    logger.info("✅ END v25.0")

if __name__ == "__main__":
    schedule.every(1).minutes.do(run_cycle)
    run_cycle()
    while True: schedule.run_pending(); time.sleep(1)
