import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    print("Testing database connection for Terminal v2.0...")
    conn = psycopg2.connect(DB_URL, sslmode='require', connect_timeout=10)
    print("✅ Database connection successful")
    
    cur = conn.cursor()
    # Test a simple query to make sure we can access live_metrics
    cur.execute("SELECT COUNT(*) FROM live_metrics")
    count = cur.fetchone()[0]
    print(f"✅ Found {count} records in live_metrics table")
    
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
