import os, psycopg2, secrets, time
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def run():
    for i in range(5):
        try:
            print(f"Attempt {i+1} connecting to DB...")
            conn = psycopg2.connect(DB_URL, sslmode='require')
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    tier TEXT DEFAULT 'free'
                );
            """)
            
            # Ensure Admin
            cur.execute("SELECT * FROM users WHERE email='mav@kairossignal.com'")
            if not cur.fetchone():
                pw = pwd_context.hash("admin")
                cur.execute("INSERT INTO users (email, password_hash, tier) VALUES (%s, %s, 'admin')", ("mav@kairossignal.com", pw))
                print("✅ Admin Created")
            
            conn.commit()
            conn.close()
            print("✅ DB Init Success")
            return
        except Exception as e:
            print(f"❌ Fail: {e}")
            time.sleep(2)

run()
