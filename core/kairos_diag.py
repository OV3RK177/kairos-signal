import clickhouse_connect
import pandas as pd
import subprocess
import os
import time
from datetime import datetime, timedelta
from termcolor import colored

# CONFIG
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')

def get_client():
    try:
        return clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
    except Exception as e:
        return None

def check_services():
    print(colored("\n--- 1. SERVICE STATUS (SYSTEMD/DOCKER) ---", "cyan"))
    services = ["kairos-cortex", "kairos-trader", "docker"]
    for svc in services:
        try:
            res = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True)
            status = res.stdout.strip()
            color = "green" if status == "active" else "red"
            print(f"Service: {svc.ljust(20)} | Status: {colored(status.upper(), color)}")
        except:
            print(f"Service: {svc.ljust(20)} | Status: {colored('UNKNOWN', 'yellow')}")

    # Check Screen Sessions
    try:
        screens = subprocess.check_output("screen -ls", shell=True).decode()
        if "kairos" in screens or "ledger" in screens or "omni" in screens:
            print(f"Screens: {colored('ACTIVE', 'green')} (Found ledger/omni sessions)")
        else:
            print(f"Screens: {colored('MISSING', 'red')} (No ledger/omni screens found)")
    except: pass

def check_ingestion_health(client):
    print(colored("\n--- 2. INGESTION HEALTH (CLICKHOUSE) ---", "cyan"))
    
    # 1. CANDLES (Market Data)
    try:
        q = """
        SELECT count(DISTINCT project_slug), max(timestamp) 
        FROM candles_10m 
        """
        res = client.query(q).result_rows[0]
        count, last_ts = res
        lag = (datetime.now() - last_ts).total_seconds() / 60
        
        status = "green" if lag < 15 else "red"
        print(f"Market Assets Tracked: {count}")
        print(f"Latest Candle:         {last_ts} ({colored(f'{lag:.1f} mins ago', status)})")
        
        # 2. DEAD ASSETS REPORT
        print("\n[Audit: Active vs Dead Sources]")
        q_dead = """
        SELECT project_slug, max(timestamp) as last_seen 
        FROM candles_10m 
        GROUP BY project_slug 
        HAVING last_seen < now() - INTERVAL 1 HOUR
        ORDER BY last_seen ASC
        LIMIT 10
        """
        dead_df = client.query_df(q_dead)
        
        if not dead_df.empty:
            print(colored(f"⚠️ FOUND {len(dead_df)} DEAD/STALE SOURCES (Sample):", "yellow"))
            print(dead_df.to_string(index=False))
        else:
            print(colored("✅ All tracked assets are reporting live data.", "green"))

    except Exception as e:
        print(colored(f"❌ Ingestion Check Failed: {e}", "red"))

def check_brain_health(client):
    print(colored("\n--- 3. BRAIN & OMNI STATUS ---", "cyan"))
    try:
        # Check Signals Table
        q = "SELECT count(), max(timestamp) FROM signals"
        count, last_ts = client.query(q).result_rows[0]
        
        if last_ts.year == 1970: # Default if empty
             print(colored("❌ NO SIGNALS GENERATED YET.", "red"))
        else:
            lag = (datetime.now() - last_ts).total_seconds() / 60
            color = "green" if lag < 30 else "yellow"
            print(f"Total Signals:       {count}")
            print(f"Last Signal:         {last_ts} ({colored(f'{lag:.1f} mins ago', color)})")
            
            # Show last signal
            last = client.query_df("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 1")
            print("\nLast Brain Output:")
            print(last[['timestamp', 'asset', 'action', 'confidence', 'reason']].to_string(index=False))

    except Exception as e:
        print(colored(f"❌ Brain Check Failed: {e}", "red"))

def check_ledger_health(client):
    print(colored("\n--- 4. EXECUTION LEDGER ---", "cyan"))
    try:
        q = "SELECT status, count() FROM signal_ledger GROUP BY status"
        res = client.query_df(q)
        if res.empty:
             print(colored("⚪ Ledger is Empty (No Paper Trades)", "white"))
        else:
            print(res.to_string(index=False))
            
            # Win Rate
            q_stats = "SELECT countIf(pnl_pct > 0), count() FROM signal_ledger WHERE status='CLOSED'"
            wins, total = client.query(q_stats).result_rows[0]
            if total > 0:
                wr = (wins/total)*100
                color = "green" if wr > 50 else "red"
                print(f"Current Win Rate: {colored(f'{wr:.1f}%', color)} ({wins}/{total})")
            else:
                print("No closed trades yet.")

    except Exception as e:
        print(colored(f"❌ Ledger Check Failed: {e}", "red"))

def main():
    print(colored("// KAIROS END-TO-END DIAGNOSTIC //", "magenta", attrs=['bold']))
    client = get_client()
    if not client:
        print(colored("❌ CRITICAL: Cannot connect to ClickHouse.", "red"))
        return

    check_services()
    check_ingestion_health(client)
    check_brain_health(client)
    check_ledger_health(client)
    print("\n" + "="*40 + "\n")

if __name__ == "__main__":
    main()
