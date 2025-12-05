import os
import sys
from dotenv import load_dotenv

print("🔍 STARTING PRE-FLIGHT CHECK...")

# 1. CHECK IMPORTS
print("[1/3] Checking Dependencies...")
try:
    import websocket
    print("   ✅ websocket-client: FOUND")
except ImportError:
    print("   ❌ websocket-client: MISSING")

try:
    import pandas
    print("   ✅ pandas: FOUND")
except ImportError:
    print("   ❌ pandas: MISSING")

# 2. CHECK KEYS
print("[2/3] Checking API Keys...")
load_dotenv()
keys = ["POLYGON_API_KEY", "HELIUS_API_KEY", "BIRDEYE_API_KEY"]
missing = []
for k in keys:
    val = os.getenv(k)
    if val and val != "your_key_here":
        print(f"   ✅ {k}: LOADED ({val[:4]}...)")
    else:
        print(f"   ⚠️ {k}: MISSING or PLACEHOLDER")
        missing.append(k)

# 3. CHECK DATABASE
print("[3/3] Checking Database Connection...")
try:
    import requests
    # Use the exact logic from base.py
    CH_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
    CH_PORT = os.getenv("CLICKHOUSE_PORT", "8123")
    CH_USER = os.getenv("CLICKHOUSE_USER", "default")
    CH_PASS = os.getenv("CLICKHOUSE_PASSWORD", "kairos")
    URL = f"http://{CH_USER}:{CH_PASS}@{CH_HOST}:{CH_PORT}"
    
    r = requests.get(f"{URL}/?query=SELECT%201")
    if r.status_code == 200:
        print("   ✅ Database: CONNECTED")
    else:
        print(f"   ❌ Database: ERROR ({r.status_code})")
except Exception as e:
    print(f"   ❌ Database: FAILED ({e})")

print("\n🏁 DIAGNOSTIC COMPLETE.")
