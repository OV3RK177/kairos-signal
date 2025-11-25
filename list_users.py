import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

try:
    print("Connecting to database...")
    conn = psycopg2.connect(DB_URL, sslmode='require', connect_timeout=5)
    cur = conn.cursor()
    
    # List all users
    cur.execute("SELECT email, tier FROM users ORDER BY id")
    users = cur.fetchall()
    
    if users:
        print("✅ Found users:")
        for email, tier in users:
            print(f"  Email: {email}, Tier: {tier}")
            if email == 'mav@kairossignal.com':
                print(f"  🔑 Default password for {email}: admin")
    else:
        print("❌ No users found in database")
        
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("This means the API can't authenticate users")
