import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    print("Testing database connection...")
    conn = psycopg2.connect(DB_URL, sslmode='require', connect_timeout=10)
    print("✅ Database connection successful!")
    
    cur = conn.cursor()
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"Database version: {version}")
    
    # Test a simple query
    cur.execute("SELECT COUNT(*) FROM live_metrics LIMIT 1")
    count = cur.fetchone()[0]
    print("✅ Database queries working")
    
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
