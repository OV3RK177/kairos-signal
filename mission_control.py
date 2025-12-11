import clickhouse_connect
import time
import os
import sys

# Configuration
CH_HOST = "localhost"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_status():
    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password='kairos')
        
        # 1. SENSOR HEALTH (Heartbeat)
        last_beat = client.query("SELECT max(timestamp) FROM metrics WHERE project_slug='stock_swarm'").result_rows[0][0]
        lag = (time.time() - last_beat.timestamp())
        sensor_status = "🟢 ONLINE" if lag < 60 else f"🔴 STALLED ({lag:.0f}s ago)"
        
        # 2. MARKET MEMORY (Depth)
        # Check how many data points we have for a major asset (e.g., BTC or AAPL) to gauge "warmup"
        depth_q = "SELECT count() FROM metrics WHERE project_slug='stock_swarm' AND timestamp > now() - INTERVAL 12 HOUR"
        data_depth = client.query(depth_q).result_rows[0][0]
        
        # 3. TRADER HOLDINGS
        positions = client.query("SELECT count(), sum((current_price - entry_price)/entry_price) FROM signal_ledger WHERE status='OPEN'").result_rows
        count = positions[0][0]
        pnl = positions[0][1] if positions[0][1] else 0.0
        
        return sensor_status, last_beat, data_depth, count, pnl
    except Exception as e:
        return "🔴 CONNECTION LOST", "N/A", 0, 0, 0

while True:
    status, heartbeat, depth, pos_count, pnl = get_status()
    
    clear_screen()
    print("🦁 KAIROS AUTONOMOUS HEDGE FUND | LIVE MONITOR")
    print("==================================================")
    print(f"👁️  SENSOR STATUS:   {status}")
    print(f"    Last Heartbeat:  {heartbeat}")
    print(f"    Data Points:     {depth:,} (12hr Window)")
    print("--------------------------------------------------")
    print(f"🧠  CORTEX STATE:    SEARCHING...")
    print(f"    Strategy:        Trend (200MA) + Momentum (RSI)")
    print("--------------------------------------------------")
    print(f"⚔️  TRADER LEDGER:   {pos_count} Positions")
    if pos_count > 0:
        print(f"    Unrealized PnL:  {pnl:.2f}%")
    else:
        print("    Status:          WAITING FOR PREY")
    print("==================================================")
    print("Press Ctrl+C to exit monitor.")
    
    time.sleep(2)
