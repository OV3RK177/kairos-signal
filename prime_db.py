import os, psycopg2, random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv("/root/kairos-sprint/.env")
conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')
cur = conn.cursor()

print("💉 Injecting Primer Data...")
projects = {
    'bitcoin': 98000,
    'render-token': 7.50,
    'tradfi_nvda': 145.00
}

now = datetime.now(timezone.utc)
for proj, base_price in projects.items():
    # Generate 48 points (1 per hour for last 2 days)
    for i in range(48):
        t = now - timedelta(hours=i)
        # Random walk price
        price = base_price * (1 + (random.random() - 0.5) * 0.05) 
        cur.execute(
            "INSERT INTO live_metrics (time, project, metric, value, raw_data) VALUES (%s, %s, 'price_usd', %s, '{}')",
            (t, proj, price)
        )
conn.commit()
print("✅ Charts Primed.")
