import os, psycopg2, secrets
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = psycopg2.connect(DB_URL, sslmode='require')
cur = conn.cursor()

# Create Users Table
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        api_key TEXT UNIQUE,
        tier TEXT DEFAULT 'free',
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
""")

# Create Admin User (Mav)
email = "mav@kairossignal.com"
password = "admin" # CHANGE THIS LATER
hashed = pwd_context.hash(password)
key = secrets.token_urlsafe(32)

try:
    cur.execute("INSERT INTO users (email, password_hash, api_key, tier) VALUES (%s, %s, %s, 'admin') RETURNING id", (email, hashed, key))
    print(f"✅ Admin Created: {email} / {password}")
    print(f"🔑 API Key: {key}")
except:
    print("⚠️ Admin already exists")

conn.commit()
conn.close()
