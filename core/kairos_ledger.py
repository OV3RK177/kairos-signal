import clickhouse_connect
import pandas as pd
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
CH_HOST = 'clickhouse-server' 
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')

print("// KAIROS LEDGER // REAL-TIME ACCOUNTANT")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

class KairosLedger:
    def __init__(self):
        self.host = 'clickhouse-server'
        self.password = CH_PASS
        self.client = None

    def connect(self):
        try:
            self.client = clickhouse_connect.get_client(host=self.host, port=8123, username='default', password=self.password)
            q = """
            CREATE TABLE IF NOT EXISTS signal_ledger (
                signal_time DateTime,
                asset String,
                action String,
                entry_price Float64,
                reason String,
                status String DEFAULT 'OPEN',
                exit_price Float64 DEFAULT 0,
                pnl_pct Float64 DEFAULT 0,
                closed_at DateTime DEFAULT toDateTime(0)
            ) ENGINE = MergeTree() ORDER BY signal_time
            """
            self.client.query(q)
            log("✅ Ledger Database Ready.")
            return True
        except Exception as e:
            log(f"❌ DB Error: {e}")
            return False

    def check_performance(self):
        # Find trades older than 4 hours that are still OPEN
        q_open = "SELECT asset, entry_price, action, signal_time FROM signal_ledger WHERE status = 'OPEN' AND signal_time < now() - INTERVAL 4 HOUR"
        try:
            open_trades = self.client.query_df(q_open)
        except: return

        if open_trades.empty: return

        log(f"🔍 Auditing {len(open_trades)} mature trades...")

        for index, trade in open_trades.iterrows():
            asset = trade['asset']
            entry = trade['entry_price']
            action = trade['action']
            
            # Get Current Price
            try:
                q_price = f"SELECT argMax(metric_value, timestamp) as price FROM metrics WHERE project_slug = '{asset}' AND metric_name = 'price_usd'"
                current_price = self.client.query(q_price).result_rows[0][0]
                
                if current_price == 0: continue # Data gap

                # Calc PnL
                if action == 'BUY':
                    pnl = ((current_price - entry) / entry) * 100
                else: # SELL
                    pnl = ((entry - current_price) / entry) * 100
                
                # Close Trade
                q_update = f"ALTER TABLE signal_ledger UPDATE status = 'CLOSED', exit_price = {current_price}, pnl_pct = {pnl}, closed_at = now() WHERE asset = '{asset}' AND status = 'OPEN'"
                self.client.query(q_update)
                
                icon = "🟢" if pnl > 0 else "🔴"
                log(f"{icon} CLOSED {asset}: {pnl:+.2f}%")
                
            except Exception as e:
                log(f"⚠️ Audit failed for {asset}: {e}")

    def run(self):
        while not self.connect(): time.sleep(5)
        
        while True:
            try:
                self.check_performance()
                
                # Stats
                try:
                    stats = self.client.query("SELECT count(), countIf(pnl_pct > 0) FROM signal_ledger WHERE status = 'CLOSED'").result_rows[0]
                    total, wins = stats
                    if total > 0:
                        log(f"🏆 WIN RATE: {(wins/total)*100:.1f}% ({wins}/{total})")
                except: pass
                
                time.sleep(60) 
            except Exception as e:
                log(f"❌ Ledger Loop Error: {e}"); self.connect(); time.sleep(10)

if __name__ == "__main__":
    KairosLedger().run()
