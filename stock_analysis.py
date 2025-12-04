import yfinance as yf
import ollama
import json
import os
from datetime import datetime

# --- CONFIG ---
TICKERS = ["SPY", "QQQ", "NVDA", "AAPL", "MSFT", "COIN", "TSLA"]
MODEL = "kimi-k2-thinking:cloud"

def get_market_data():
    print(f"📉 Fetching Wall Street data for {len(TICKERS)} tickers...")
    market_summary = {}
    for ticker in TICKERS:
        try:
            stock = yf.Ticker(ticker)
            # Get yesterday's close since market is closed
            hist = stock.history(period="5d") 
            if not hist.empty:
                last_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = ((last_close - prev_close) / prev_close) * 100
                market_summary[ticker] = {
                    "price": round(last_close, 2),
                    "change_pct": round(change, 2)
                }
        except Exception as e:
            print(f"⚠️ Error fetching {ticker}: {e}")
    return market_summary

def analyze_with_kimi(data):
    print(f"🧠 Sending data to {MODEL}...")
    prompt = f"""
    Analyze this market snapshot from yesterday's close: {json.dumps(data)}.
    Identify any anomalies or trends relevant to DePIN crypto infrastructure and AI compute.
    Provide a risk score (0-10) and a short strategic summary.
    """
    try:
        response = ollama.chat(model=MODEL, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return None

if __name__ == "__main__":
    print("--- STARTING STOCK ANALYSIS ---")
    data = get_market_data()
    if data:
        print("✅ Data Fetched. Analyzing...")
        insight = analyze_with_kimi(data)
        print("\n--- KIMI INSIGHT ---")
        print(insight)
        print("--------------------")
        
        # Save to a log file for Cerebro to pick up if needed
        with open("latest_market_insight.txt", "w") as f:
            f.write(str(insight))
    else:
        print("❌ No data fetched.")
