import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    print("Testing local PostgreSQL connection...")
    conn = psycopg2.connect(DB_URL, sslmode='prefer', connect_timeout=10)
    print("✅ Local database connection successful!")
    
    cur = conn.cursor()
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"Database version: {version}")
    
    # Test if live_metrics table exists
    cur.execute("SELECT COUNT(*) FROM live_metrics LIMIT 1")
    count = cur.fetchone()[0]
    print(f"✅ Found {count} records in live_metrics table")
    
    conn.close()
    print("✅ Database test completed successfully")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("Make sure PostgreSQL is running and the database exists")
