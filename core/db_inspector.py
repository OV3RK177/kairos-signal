import psycopg2
import os
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

# CONFIRM CONNECTION
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'kairos') 

def inspect():
    try:
        conn = psycopg2.connect(host=PG_HOST, database="kairos_meta", user="doadmin", password=PG_PASS)
        cur = conn.cursor()
        
        # 1. SEARCH FOR OUR TARGETS
        targets = ['dimo', 'flux', 'myst', 'helium', 'render', 'grass']
        print(f"\n🔍 SCANNING POSTGRES FOR: {', '.join(targets)}...")
        
        found = []
        for t in targets:
            # Case-insensitive search (%like%)
            cur.execute(f"SELECT DISTINCT project FROM live_metrics WHERE project ILIKE '%{t}%'")
            rows = cur.fetchall()
            for r in rows:
                found.append([t.upper(), r[0]])

        if found:
            print(tabulate(found, headers=["Looking For", "Found In DB"], tablefmt="github"))
        else:
            print("❌ CRITICAL: No price data found for ANY target assets.")
            
        # 2. CHECK MOST RECENT ENTRIES (To see if data is stale)
        print("\n⏱️ CHECKING FRESHNESS (Latest 5 Entries):")
        cur.execute("SELECT time, project, value FROM live_metrics ORDER BY time DESC LIMIT 5")
        recent = cur.fetchall()
        print(tabulate(recent, headers=["Timestamp", "Project", "Price"], tablefmt="github"))

        conn.close()

    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")

if __name__ == "__main__":
    inspect()
