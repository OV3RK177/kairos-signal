import os, socket, psycopg2, secrets
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load Env
load_dotenv("/root/kairos-sprint/.env")
raw_url = os.getenv("DATABASE_URL")

# Extract Hostname
try:
    # Format: postgres://user:pass@HOSTNAME:port/db
    current_host = raw_url.split('@')[1].split(':')[0]
    print(f"🎯 Targeting Host: {current_host}")
    
    # Force Resolution (System Level)
    try:
        # Try native first
        target_ip = socket.gethostbyname(current_host)
    except:
        # If native fails, just print error and hope the previous IP injection worked
        print("⚠️ Native DNS failed. Checking if we already have an IP...")
        import re
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", current_host):
            target_ip = current_host
            print("✅ Host is already an IP.")
        else:
            raise Exception("DNS Dead.")

    print(f"📍 Target IP: {target_ip}")
    
    # Construct Working URL
    final_url = raw_url.replace(current_host, target_ip)
    
    # Save to Disk (Persistence)
    with open("/root/kairos-sprint/.env", "r") as f: lines = f.readlines()
    with open("/root/kairos-sprint/.env", "w") as f:
        for line in lines:
            if "DATABASE_URL=" in line:
                f.write(f'DATABASE_URL="{final_url}"\n')
            else:
                f.write(line)
    print("💾 Coordinates Saved.")

    # BREACH DATABASE
    print("💥 Breaching...")
    conn = psycopg2.connect(final_url, sslmode='require')
    cur = conn.cursor()

    # Nuke Users Table
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT,
            api_key TEXT,
            tier TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # Create Admin
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_ctx.hash("admin")
    key = secrets.token_urlsafe(32)
    
    cur.execute(
        "INSERT INTO users (email, password_hash, api_key, tier) VALUES (%s, %s, %s, 'admin')", 
        ("mav@kairossignal.com", hashed, key)
    )
    
    conn.commit()
    conn.close()
    print("🏆 MISSION SUCCESS: Admin Created.")
    print("   User: mav@kairossignal.com")
    print("   Pass: admin")

except Exception as e:
    print(f"💀 FATAL ERROR: {e}")
    exit(1)
