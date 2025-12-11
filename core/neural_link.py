import os
import time
import clickhouse_connect
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIG ---
load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')
MODEL = "deepseekv3.1:671b:cloud" 

# --- DB CONNECTION ---
def get_db():
    try:
        return clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
    except Exception as e:
        print(f"⚠️ DB CONNECTION FAILED: {e}", flush=True)
        return None

# --- ANALYTICS ROUTINE ---
def run_pulse_check(client):
    if not client: return

    swarm_count = 0
    sol_count = 0

    try:
        # 1. Check Swarm Ingestion (Target: 'metrics' table)
        try:
            swarm_count = client.command("SELECT count() FROM metrics WHERE timestamp > now() - INTERVAL 1 MINUTE")
        except:
            pass
        
        # 2. Check Solana Firehose (Target: 'solana_firehose' table)
        try:
            sol_count = client.command("SELECT count() FROM solana_firehose WHERE timestamp > now() - INTERVAL 1 MINUTE")
        except:
            pass

        # 3. Log Heartbeat
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🧠 [{timestamp}] PULSE | Swarm (metrics): +{swarm_count} | Solana: +{sol_count} | {MODEL}", flush=True)

    except Exception as e:
        print(f"❌ PULSE ERROR: {e}", flush=True)

# --- DIAGNOSTIC STARTUP ---
def perform_diagnostics(client):
    print("🏥 RUNNING DIAGNOSTICS...", flush=True)
    try:
        tables = client.command("SHOW TABLES")
        print(f"📂 EXISTING TABLES: {tables.replace(chr(10), ', ')}", flush=True)
    except Exception as e:
        print(f"⚠️ COULD NOT LIST TABLES: {e}", flush=True)

# --- MAIN LOOP ---
def activate_cortex():
    print(f"🧠 KAIROS NEURAL LINK: ONLINE [{MODEL}]", flush=True)
    
    # Initial DB Check
    client = get_db()
    if client:
        perform_diagnostics(client)
        client.close()
    
    print("   Listening to ClickHouse streams...", flush=True)
    
    while True:
        client = get_db()
        run_pulse_check(client)
        if client: client.close() 
        
        # Heartbeat every 30s
        time.sleep(30)

if __name__ == "__main__":
    activate_cortex()
