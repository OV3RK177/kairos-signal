import clickhouse_connect
import time

def init_db():
    print("⏳ Connecting to ClickHouse...")
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')
    
    # 1. Create Database
    client.command('CREATE DATABASE IF NOT EXISTS kairos')
    
    # 2. Create Signals Table (The output of Cortex)
    # Stores the raw price/vol plus the 6-Dim Physics Score
    sql = """
    CREATE TABLE IF NOT EXISTS kairos.signals (
        timestamp DateTime,
        symbol String,
        price Float64,
        volume Float64,
        score Float64,
        gravity Float64,
        velocity Float64,
        entropy Float64
    ) ENGINE = MergeTree()
    ORDER BY (symbol, timestamp)
    TTL timestamp + INTERVAL 7 DAY
    """
    client.command(sql)
    print("✅ Database & Schema Initialized: [kairos.signals]")

if __name__ == "__main__":
    time.sleep(5) # Let DB warm up
    init_db()
