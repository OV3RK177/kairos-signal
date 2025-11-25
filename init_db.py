import os
import psycopg2
import secrets
import time
import logging
import socket
from passlib.context import CryptContext
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv("/root/kairos-sprint/.env")
DB_URL = os.getenv("DATABASE_URL")
DB_URL_IP = os.getenv("DATABASE_URL_IP")  # Optional IP fallback

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_connection(url, max_attempts=5):
    """Test database connection with retry and backoff"""
    for attempt in range(max_attempts):
        try:
            logger.info(f"🔌 Testing DB connection (attempt {attempt + 1}/{max_attempts})...")
            conn = psycopg2.connect(url, sslmode='require', connect_timeout=10)
            conn.close()
            logger.info("✅ DB Connection Successful")
            return True
        except psycopg2.OperationalError as e:
            logger.error(f"❌ Connection attempt {attempt + 1} failed: {e}")
            if "could not translate host name" in str(e):
                logger.error("💡 DNS Resolution Failed. Check your DATABASE_URL.")
                # If we have an IP fallback, try it
                if DB_URL_IP and attempt == max_attempts - 1:
                    logger.info("🔄 Trying IP fallback...")
                    return test_connection(DB_URL_IP, max_attempts=3)
            if attempt < max_attempts - 1:
                wait_time = 3 * (attempt + 1)
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            if attempt < max_attempts - 1:
                time.sleep(3)
    
    return False

def create_users_table():
    """Create users table and admin user"""
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        cur = conn.cursor()
        
        # Create users table
        logger.info("📊 Creating users table...")
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
        
        # Create index for performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        
        conn.commit()
        logger.info("✅ Users table created/verified")
        
        # Check if admin exists
        logger.info("🔍 Checking for admin user...")
        cur.execute("SELECT id, email, tier FROM users WHERE email = 'mav@kairossignal.com'")
        user = cur.fetchone()
        
        if not user:
            logger.info("👤 Creating admin user...")
            hashed_pw = pwd_context.hash("admin")
            api_key = secrets.token_urlsafe(32)
            
            cur.execute(
                "INSERT INTO users (email, password_hash, api_key, tier) VALUES (%s, %s, %s, 'admin')",
                ("mav@kairossignal.com", hashed_pw, api_key)
            )
            conn.commit()
            logger.info("✅ Admin user created: mav@kairossignal.com / admin")
            logger.info(f"🔑 API Key: {api_key}")
        else:
            logger.info(f"ℹ️ Admin user already exists (ID: {user[0]}, Tier: {user[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

def verify_dns():
    """Verify DNS resolution for the database host"""
    try:
        host = DB_URL.split('@')[1].split(':')[0]
        logger.info(f"🌐 Testing DNS resolution for: {host}")
        socket.gethostbyname(host)
        logger.info("✅ DNS Resolution OK")
        return True
    except Exception as e:
        logger.error(f"❌ DNS Resolution Failed: {e}")
        return False

def main():
    logger.info("=== KAIROS DB INITIALIZATION STARTED ===")
    
    # Test DNS first
    verify_dns()
    
    # Test connection
    if not test_connection(DB_URL):
        logger.error("❌ Could not connect to database after all attempts")
        logger.error("💡 Check your DATABASE_URL in .env")
        logger.error("💡 Ensure your DigitalOcean database is 'Trusted' from this IP")
        return False
    
    # Create tables
    if not create_users_table():
        logger.error("❌ Failed to create users table")
        return False
    
    logger.info("=== ✅ DB INITIALIZATION COMPLETE ===")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
