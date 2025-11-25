import os, json, psycopg2, time
from datetime import datetime, timezone, timedelta
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from polygon import RESTClient

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
POLYGON_KEY = os.getenv("POLYGON_API_KEY")

TARGETS = [
    "NVDA", "SPY", "QQQ", "COIN", "GOOG", "AMD", "MSFT", "AAPL", "TSLA", "META",
    "IBM", "INTC", "MSTR", "MARA", "RIOT"
]

def get_db():
    # Retry loop for DNS/Connection stability
    for i in range(5):
        try:
            return psycopg2.connect(DB_URL, sslmode='require')
        except Exception as e:
            print(f"⚠️ Connection failed (Attempt {i+1}/5): {e}")
            time.sleep(5)
    raise Exception("❌ Could not connect to DB after 5 attempts")

def backfill_ticker(client, ticker):
    print(f">> Fetching 1 Year of data for {ticker}...")
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        aggs = client.list_aggs(ticker=ticker, multiplier=1, timespan="hour", from_=start_date, to=end_date, limit=50000)
        
        rows = []
        for agg in aggs:
            ts = datetime.fromtimestamp(agg.timestamp / 1000, tz=timezone.utc)
            project = f"tradfi_{ticker.lower()}"
            rows.append((ts, project, "price_usd", agg.close, json.dumps({"source": "polygon_history"})))

        if not rows:
            print(f"⚠️ No data found for {ticker}")
            return

        conn = get_db()
        cur = conn.cursor()
        execute_values(cur, "INSERT INTO live_metrics (time, project, metric, value, raw_data) VALUES %s ON CONFLICT DO NOTHING", rows)
        conn.commit()
        conn.close()
        print(f"✅ {ticker}: Inserted {len(rows)} historical points.")
        
    except Exception as e:
        print(f"❌ Failed {ticker}: {e}")

if __name__ == "__main__":
    if not POLYGON_KEY:
        print("No Polygon Key found!")
        exit(1)
        
    client = RESTClient(api_key=POLYGON_KEY)
    for t in TARGETS: backfill_ticker(client, t)
    print("--- BACKFILL COMPLETE ---")
