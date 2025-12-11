import clickhouse_connect
import psycopg2
import pandas as pd
import requests
import json
import os
import re
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'kairos')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')
MODEL = "gemini-3-pro-preview"

# DB Clients
ch_client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)

def get_physical_reality():
    q = """
    SELECT project_slug, metric_name, 
           argMax(metric_value, timestamp) as current,
           (argMax(metric_value, timestamp) - avg(metric_value)) / avg(metric_value) * 100 as growth_pct
    FROM metrics 
    WHERE timestamp > now() - INTERVAL 7 DAY 
    AND (metric_name LIKE '%node%' OR metric_name LIKE '%vehicle%' OR metric_name LIKE '%active%')
    GROUP BY project_slug, metric_name
    """
    return ch_client.query_df(q)

def get_financial_reality():
    conn = psycopg2.connect(host=PG_HOST, database="kairos_meta", user="doadmin", password=PG_PASS)
    q = """
    SELECT project, AVG(value) as price, STDDEV(value) as volatility 
    FROM live_metrics 
    WHERE time > NOW() - INTERVAL '24 hours' AND metric = 'price_usd'
    GROUP BY project ORDER BY volatility DESC LIMIT 100
    """
    df = pd.read_sql(q, conn)
    conn.close()
    return df

def log_trade_to_ledger(asset, action, reason, price):
    try:
        # Create Ledger Table if not exists
        ch_client.command("""
            CREATE TABLE IF NOT EXISTS signal_ledger (
                signal_time DateTime,
                asset String,
                action String,
                entry_price Float64,
                reason String,
                status String DEFAULT 'OPEN',
                exit_price Float64 DEFAULT 0,
                pnl_pct Float64 DEFAULT 0,
                closed_at DateTime DEFAULT toDateTime(0)
            ) ENGINE = MergeTree() ORDER BY signal_time
        """)
        
        # Insert Signal
        data = [[datetime.now(), asset, action, float(price), reason]]
        ch_client.insert('signal_ledger', data, column_names=['signal_time', 'asset', 'action', 'entry_price', 'reason'])
        print(f"✅ LEDGER UPDATED: {action} {asset} @ ${price}")
    except Exception as e:
        print(f"❌ Ledger Write Failed: {e}")

def engage():
    print("... Compiling Digital Twin State ...")
    phy = get_physical_reality()
    fin = get_financial_reality()
    
    # We force Gemini to output specific JSON for the database
    prompt = f"""
    SYSTEM: KAIROS INTELLIGENCE
    DATA: PHYSICAL vs VIRTUAL MARKETS (7-DAY WINDOW)
    
    PHYSICAL INFRASTRUCTURE GROWTH:
    {phy.to_string(index=False)}
    
    MARKET CAPITAL FLOWS (HIGH VOLATILITY):
    {fin.to_string(index=False)}
    
    TASK:
    Identify ONE high-conviction trade based on divergence.
    
    OUTPUT FORMAT (STRICT JSON ONLY, NO TEXT):
    {{
        "asset": "DIMO",
        "action": "BUY", 
        "price": 0.018,
        "reason": "Nodes up 3% but price flat"
    }}
    If no trade is clear, return empty JSON {{}}.
    """
    
    print(f"... Transmitting to {MODEL} ...")
    
    try:
        res = requests.post(OLLAMA_URL, json={
            "model": MODEL, 
            "prompt": prompt, 
            "stream": False,
            "format": "json", # This forces the model to be a computer, not a poet
            "options": {"num_ctx": 32000}
        }, timeout=300)
        
        if res.status_code == 200:
            resp_str = res.json().get('response', '{}')
            print(f">>> AI DECISION: {resp_str}")
            
            # Parse and Log
            try:
                decision = json.loads(resp_str)
                if decision.get('asset') and decision.get('action'):
                    log_trade_to_ledger(
                        decision['asset'], 
                        decision['action'], 
                        decision['reason'], 
                        decision.get('price', 0)
                    )
            except json.JSONDecodeError:
                print("❌ AI returned invalid JSON. Skipping ledger update.")
        else:
            print(f"AI Error: {res.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    engage()
