import clickhouse_connect
import time

def init_ledger():
    print("⏳ Connecting to ClickHouse...")
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')
    
    # 1. Create Trades Table (The Ledger)
    sql = """
    CREATE TABLE IF NOT EXISTS kairos.trades (
        timestamp DateTime,
        symbol String,
        side String,        -- 'BUY' or 'SELL'
        price Float64,
        size Float64,
        pnl Float64,        -- Realized PnL (0 if open)
        status String       -- 'OPEN' or 'CLOSED'
    ) ENGINE = MergeTree()
    ORDER BY (symbol, timestamp)
    """
    client.command(sql)
    print("✅ Ledger Initialized: [kairos.trades]")

if __name__ == "__main__":
    init_ledger()
