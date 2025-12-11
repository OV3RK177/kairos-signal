import clickhouse_connect
from tabulate import tabulate
import os
from dotenv import load_dotenv

load_dotenv()
try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')
    print("\n💰 KAIROS PERFORMANCE REPORT")
    print("="*50)

    # 1. GET STATS
    stats = client.query("""
        SELECT 
            count() as total,
            countIf(pnl_percent > 0) as wins,
            avg(pnl_percent) as avg_pnl,
            max(pnl_percent) as best
        FROM signal_ledger 
        WHERE action = 'BUY'
    """).result_rows[0]
    
    total, wins, avg_pnl, best = stats
    win_rate = (wins / total * 100) if total > 0 else 0.0
    
    print(f"🏆 WIN RATE:    {win_rate:.1f}%")
    print(f"📊 TOTAL TRADES: {total}")
    print(f"📈 AVG PnL:      {avg_pnl:+.2f}%")
    print(f"🚀 BEST TRADE:   {best:+.2f}%")
    print("="*50 + "\n")

    # 2. GET LATEST TRADES
    print("📜 LATEST TRADES:")
    trades = client.query("""
        SELECT timestamp, asset, signal_price, current_price, pnl_percent 
        FROM signal_ledger 
        WHERE action = 'BUY' 
        ORDER BY timestamp DESC 
        LIMIT 5
    """).result_rows
    
    table = []
    for t in trades:
        ts = t[0].strftime("%H:%M")
        pnl = f"{t[4]:+.2f}%"
        table.append([ts, t[1], f"${t[2]:.2f}", f"${t[3]:.2f}", pnl])
        
    print(tabulate(table, headers=["Time", "Asset", "Entry", "Curr", "PnL"], tablefmt="simple"))
    print("\n")

except Exception as e:
    print(f"⚠️ CALCULATION ERROR: {e}")
