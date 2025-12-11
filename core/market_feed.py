import time, requests, psycopg2, os, json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'kairos') 

def get_db(): return psycopg2.connect(host=PG_HOST, database="kairos_meta", user="doadmin", password=PG_PASS)

def main():
    print("🌍 COINGECKO WIDE-NET ONLINE (Background)...")
    while True:
        try:
            # Fetch Top 250 + DePIN Category
            urls = [
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false",
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&category=depin&order=market_cap_desc&per_page=100&page=1&sparkline=false"
            ]
            
            conn = get_db()
            cur = conn.cursor()
            count = 0
            now = datetime.now(timezone.utc)

            for url in urls:
                data = requests.get(url, timeout=30).json()
                if isinstance(data, list):
                    for item in data:
                        cur.execute(
                            "INSERT INTO live_metrics (time, project, metric, value, raw_data) VALUES (%s, %s, %s, %s, %s)",
                            (now, item['id'], 'price_usd', item['current_price'], json.dumps(item))
                        )
                        count += 1
                time.sleep(2)

            conn.commit()
            conn.close()
            print(f"✅ Injected {count} Wide-Net data points.")
        except Exception as e:
            print(f"Feed Error: {e}")
        
        time.sleep(120)

if __name__ == "__main__":
    main()
