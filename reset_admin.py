import os, psycopg2, secrets
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    print("🔌 Connecting to Database...")
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()

    # Nuke and Rebuild
    print("💥 Resetting Users Table...")
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            api_key TEXT UNIQUE,
            tier TEXT DEFAULT 'free',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # Create Admin
    print("👤 Creating Admin User...")
    hashed = pwd_context.hash("admin")
    key = secrets.token_urlsafe(32)
    
    cur.execute(
        "INSERT INTO users (email, password_hash, api_key, tier) VALUES (%s, %s, %s, 'admin')", 
        ("mav@kairossignal.com", hashed, key)
    )
    
    conn.commit()
    conn.close()
    print("✅ SUCCESS: Admin Reset.")
    print("👉 Login: mav@kairossignal.com")
    print("👉 Pass:  admin")

except Exception as e:
    print(f"❌ FAILURE: {e}")
