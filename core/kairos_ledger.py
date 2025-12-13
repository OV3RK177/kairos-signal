import clickhouse_connect
import pandas as pd
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
print("// KAIROS LEDGER V2 // PAPER TIGER MODE", flush=True)

class KairosLedger:
    def __init__(self):
        self.host = 'clickhouse-server'
        self.password = 'kairos'
        self.client = None
        self.balance = 10000.00  # STARTING CAPITAL
        self.active_trades = []

    def connect(self):
        try:
            self.client = clickhouse_connect.get_client(host=self.host, port=8123, username='default', password=self.password)
            # Create Ledger Table if not exists
            q = """
            CREATE TABLE IF NOT EXISTS paper_ledger (
                trade_id UUID DEFAULT generateUUIDv4(),
                entry_time DateTime,
                asset String,
                side String,
                size Float64,
                entry_price Float64,
                exit_price Float64 DEFAULT 0,
                pnl Float64 DEFAULT 0,
                status String DEFAULT 'OPEN',
                balance_after Float64 DEFAULT 0
            ) ENGINE = MergeTree() ORDER BY entry_time
            """
            self.client.query(q)
            print(f"✅ Ledger Connected. Balance: ${self.balance:,.2f}", flush=True)
            return True
        except Exception as e:
            print(f"❌ Ledger DB Error: {e}", flush=True)
            return False

    def execute_trade(self, signal):
        # 1. Forex Filter
        if "USD" in signal['asset'] and len(signal['asset']) == 6: # Crude forex check
            return 
            
        # 2. Position Sizing (Example: 10% of portfolio)
        size = (self.balance * 0.10) / signal['price']
        
        # 3. Log Trade
        q = f"""
        INSERT INTO paper_ledger (entry_time, asset, side, size, entry_price, status)
        VALUES (now(), '{signal['asset']}', '{signal['action']}', {size}, {signal['price']}, 'OPEN')
        """
        self.client.query(q)
        print(f"💰 EXECUTED: {signal['action']} {signal['asset']} @ ${signal['price']}", flush=True)

    def run(self):
        while not self.connect(): time.sleep(5)
        # Main Loop would listen for Brain signals here
        while True:
            time.sleep(10) # Placeholder for heartbeat

if __name__ == "__main__":
    KairosLedger().run()
