import os, time, json, logging, requests, psycopg2, schedule
from datetime import datetime, timezone
from dotenv import load_dotenv
import colorlog
import urllib3

# SILENCE
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SETUP
load_dotenv()
handler = logging.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(asctime)s - %(message)s'))
logger = logging.getLogger("kairos-gpu")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

DB_URL = os.getenv("DATABASE_URL")

def save(project, metric, value, raw):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO live_metrics (time, project, metric, value, raw_data) VALUES (%s, %s, %s, %s, %s)",
            (datetime.now(timezone.utc), project, metric, float(value), json.dumps(raw)))
        conn.commit()
        conn.close()
        logger.info(f"🔥 {project.upper()}: {metric} = {value}")
    except: pass

# --- THE GPU SIGNALS ---

def task_akash_utilization():
    try:
        # Polkachu RPC for Akash
        r = requests.get("https://akash-api.polkachu.com/akash/market/v1beta4/leases/list", timeout=10)
        if r.status_code == 200:
            d = r.json()
            total_leases = int(d.get('pagination', {}).get('total', 0))
            # We can try to fetch active vs closed to get a utilization rate if available in pagination or summary
            # For now, total active leases is a strong demand signal
            save("akash", "active_leases", total_leases, {"source": "polkachu_rpc"})
            
            # Advanced: Check for specific high-value providers? (Future)
    except: logger.error("Akash GPU Fail")

def task_render_activity():
    try:
        # Render doesn't have a clean public API for frames, but we can proxy via token burn or escrow movement
        # Using Helius to check the Escrow/Burn address activity (Proxy for job volume)
        # RENDER Token Mint: rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof
        # We track transfer velocity as a proxy for job payments
        pass # We already have this in the main collector via 'tx_velocity'
    except: pass

def task_clore_ai():
    try:
        # Clore.ai Market Stats
        r = requests.get("https://api.clore.ai/v1/market_stats", timeout=10) 
        # Note: Endpoint inferred, usually requires auth or scraping. 
        # If public API is hidden, we fallback to price/vol which is already in CoinGecko
        pass 
    except: pass

def task_nosana_jobs():
    try:
        # Nosana Explorer API (Solana)
        # We can check the 'jobs' program account on Solana
        pass
    except: pass

def run_gpu_cycle():
    logger.info("--- START GPU SIGNAL CYCLE ---")
    task_akash_utilization()
    # Add more granular scrapers here as we reverse-engineer them
    logger.info("--- END GPU SIGNAL CYCLE ---")

if __name__ == "__main__":
    run_gpu_cycle() # One-off run for now to test
    # schedule.every(5).minutes.do(run_gpu_cycle)
    # while True: schedule.run_pending(); time.sleep(1)
