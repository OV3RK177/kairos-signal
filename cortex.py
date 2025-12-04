import time
import json
import os
import logging
import yfinance as yf
import ollama
import requests
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Kimi Model (Your Paid Asset)
MODEL = "kimi-k2-thinking:cloud"

# Data Sources
CH_HOST = "http://default:kairos@localhost:8123" # ClickHouse
TICKERS = ["NVDA", "COIN", "HNT-USD", "RNDR-USD", "HONEY-USD"]

# Logging
logging.basicConfig(
    filename='cortex.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_market_snapshot():
    """Get real-time volatility data."""
    data = {}
    try:
        for ticker in TICKERS:
            t = yf.Ticker(ticker)
            # Get intraday data (last 1 hour, 5m interval)
            hist = t.history(period="1d", interval="5m")
            if not hist.empty:
                latest = hist.iloc[-1]
                start = hist.iloc[0]
                pct_change = ((latest['Close'] - start['Open']) / start['Open']) * 100
                data[ticker] = {
                    "current": round(latest['Close'], 2),
                    "volatility_1h": round(pct_change, 2),
                    "volume": int(latest['Volume'])
                }
    except Exception as e:
        logging.error(f"Market Data Error: {e}")
    return data

def get_depin_health():
    """Query ClickHouse for infrastructure pulse."""
    # Simple query to get row count/activity velocity
    query = "SELECT count() FROM metrics WHERE timestamp > now() - INTERVAL 15 MINUTE"
    try:
        response = requests.post(CH_HOST, data=query)
        if response.status_code == 200:
            return {"ingestion_velocity_15m": response.text.strip()}
    except Exception as e:
        logging.error(f"ClickHouse Error: {e}")
    return {"ingestion_velocity_15m": "Unknown"}

def consult_kimi(context, agent_role):
    """Send deep-dive prompt to Kimi."""
    logging.info(f"🧠 Waking up {agent_role}...")
    
    prompt = f"""
    ROLE: You are {agent_role}. 
    CONTEXT: {json.dumps(context)}
    TASK: Analyze this 15-minute data snapshot.
    1. Detect any anomalous patterns.
    2. Predict the next 1-hour trend.
    3. Rate Risk Level (0-10).
    OUTPUT: Concise, bullet-point intelligence. No fluff.
    """
    
    try:
        response = ollama.chat(model=MODEL, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
    except Exception as e:
        logging.error(f"Kimi Error: {e}")
        return None

def save_intel(insight_type, content):
    """Save to disk (and later Postgres)."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"\n--- {timestamp} | {insight_type} ---\n{content}\n"
    
    # Append to Daily Briefing file
    with open("daily_intel_brief.md", "a") as f:
        f.write(entry)
    
    print(f"✅ {insight_type} Analysis Complete.")

def run_cortex_cycle():
    print(f"⚡ Cortex Cycle Started: {datetime.now().strftime('%H:%M')}")
    
    # 1. Gather Data
    market_data = get_market_snapshot()
    infra_data = get_depin_health()
    
    # 2. Agent A: Macro Analyst (Wall St vs Crypto)
    if market_data:
        macro_intel = consult_kimi(market_data, "The Macro-Volatility Analyst")
        save_intel("MACRO_RISK", macro_intel)
        
    # 3. Agent B: DePIN Specialist (Infrastructure)
    if infra_data:
        depin_intel = consult_kimi(infra_data, "The DePIN Network Engineer")
        save_intel("INFRA_HEALTH", depin_intel)

if __name__ == "__main__":
    print("🧠 CORTEX V1.0 ONLINE. Frequency: 15 Minutes.")
    while True:
        run_cortex_cycle()
        time.sleep(900) # 15 Minutes
