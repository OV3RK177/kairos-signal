#!/bin/bash
set -e

echo "🚀 KAIROS: FINAL DEPLOYMENT SEQUENCE..."

# KILL OLD PROCESSES
echo "💀 Killing zombies..."
sudo systemctl stop kairos-macro 2>/dev/null || true
pkill -f macro_engine.py 2>/dev/null || true
pkill -f neural_link.py 2>/dev/null || true
pkill -f python3 2>/dev/null || true

# VERIFY ENV
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file missing in /root/kairos-signal"
    exit 1
fi
source .env

# SETUP VENV
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q clickhouse-connect psycopg2-binary requests ccxt python-dotenv tabulate

# CREATE MACRO ENGINE (Ingestion)
echo "🏛️ Creating Macro Engine..."
cat << 'PY' > core/macro_engine.py
import ccxt, clickhouse_connect, psycopg2, requests, json, time, threading, os
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'kairos') 

def run_kraken():
    print("🚀 [FAST] KRAKEN ONLINE")
    client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
    ex = ccxt.kraken({'enableRateLimit': True})
    while True:
        try:
            tickers = ex.fetch_tickers()
            sorted_t = sorted(tickers.values(), key=lambda x: x.get('quoteVolume', 0) or 0, reverse=True)[:100]
            batch = []
            now = datetime.now(timezone.utc)
            for t in sorted_t:
                sym = t['symbol'].replace('/', '_')
                if t.get('last'): batch.append([now, sym, 'price_usd', float(t['last'])])
            if batch:
                client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                print(f"⚡ [FAST] Flushed {len(batch)} ticks.")
            time.sleep(10)
        except: time.sleep(5)

def run_gecko():
    print("🌍 [SLOW] COINGECKO ONLINE")
    urls = ["https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&category=depin&order=market_cap_desc&per_page=100&page=1&sparkline=false"]
    while True:
        try:
            conn = psycopg2.connect(host=PG_HOST, database="kairos_meta", user="doadmin", password=PG_PASS)
            cur = conn.cursor()
            now = datetime.now(timezone.utc)
            for url in urls:
                data = requests.get(url, timeout=30).json()
                if isinstance(data, list):
                    for i in data:
                        cur.execute("INSERT INTO live_metrics (time, project, metric, value, raw_data) VALUES (%s, %s, %s, %s, %s)", (now, i['id'], 'price_usd', i['current_price'], json.dumps(i)))
                time.sleep(2)
            conn.commit(); conn.close()
            print("✅ [SLOW] Saved DePIN prices.")
            time.sleep(120)
        except: time.sleep(60)

if __name__ == "__main__":
    t1 = threading.Thread(target=run_kraken); t2 = threading.Thread(target=run_gecko)
    t1.start(); t2.start(); t1.join(); t2.join()
PY

# CREATE NEURAL LINK (Brain)
echo "🧠 Creating Neural Link..."
cat << 'PY' > core/neural_link.py
import clickhouse_connect, psycopg2, pandas as pd, requests, json, os
from dotenv import load_dotenv
load_dotenv()

CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'kairos') 
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')

def engage():
    print("... Compiling Data ...")
    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
        phy = client.query_df("SELECT project_slug, metric_name, argMax(metric_value, timestamp) as val FROM metrics WHERE timestamp > now() - INTERVAL 7 DAY AND metric_name LIKE '%node%' GROUP BY project_slug, metric_name")
        
        conn = psycopg2.connect(host=PG_HOST, database="kairos_meta", user="doadmin", password=PG_PASS)
        fin = pd.read_sql("SELECT project, AVG(value) as price FROM live_metrics WHERE time > NOW() - INTERVAL '24 hours' AND metric = 'price_usd' GROUP BY project", conn)
        conn.close()
        
        prompt = f"SYSTEM: KAIROS INTELLIGENCE\nDATA:\n{phy.to_string()}\n\n{fin.to_string()}\nTASK: Identify undervalued DePIN networks."
        
        print(f"... Sending to Gemini 3 ...")
        res = requests.post(OLLAMA_URL, json={"model": "gemini-3-pro-preview", "prompt": prompt, "stream": False}, timeout=300)
        if res.status_code == 200: print(f"\n>>> INTELLIGENCE REPORT <<<\n{res.json().get('response')}")
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__": engage()
PY

# START SERVICE
echo "⚙️ Starting Service..."
nohup python3 -u core/macro_engine.py > macro.log 2>&1 &

echo "✅ DEPLOYMENT COMPLETE."
echo "   Run 'tail -f macro.log' to watch data flow."
echo "   Run 'python3 core/neural_link.py' to ask the AI."
