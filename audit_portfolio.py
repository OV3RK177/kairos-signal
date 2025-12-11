import clickhouse_connect

client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

print("💼 PORTFOLIO AUDIT (The 105 Positions)")
print("---------------------------------------------------------")
print(f"{'ASSET':<12} | {'ENTRY':<10} | {'CURRENT':<10} | {'PnL %':<8}")
print("-" * 55)

try:
    # 1. Fetch Open Positions (Asset + Entry Price)
    ledger_query = "SELECT asset, signal_price FROM signal_ledger WHERE status='OPEN'"
    positions = client.query(ledger_query).result_rows
    
    if not positions:
        print("✅ No open positions found.")
        exit()

    # 2. Fetch Latest Market Prices for these assets
    assets = [f"'{p[0]}'" for p in positions]
    assets_str = ",".join(assets)
    
    price_query = f"""
    SELECT metric_name, argMax(metric_value, timestamp) as latest_price
    FROM metrics 
    WHERE project_slug IN ('stock_swarm', 'omni_sensor')
    AND metric_name IN ({assets_str})
    GROUP BY metric_name
    """
    
    current_prices_raw = client.query(price_query).result_rows
    current_prices = {row[0]: row[1] for row in current_prices_raw}

    # 3. Calculate PnL
    total_pnl = 0
    valid_count = 0
    
    for asset, entry in positions:
        current = current_prices.get(asset, 0)
        
        if current > 0 and entry > 0:
            pnl = ((current - entry) / entry) * 100
            total_pnl += pnl
            valid_count += 1
            
            # Formatting
            flag = "🟢" if pnl > 0 else "🔴"
            if pnl < -5.0: flag = "💀" # Heavy bag
            
            print(f"{flag} {asset:<10} | ${entry:<9.2f} | ${current:<9.2f} | {pnl:>.2f}%")
        else:
            print(f"⚪ {asset:<10} | ${entry:<9.2f} | {'???':<9} | N/A")

    print("-" * 55)
    if valid_count > 0:
        avg_pnl = total_pnl / valid_count
        print(f"📊 AVERAGE PnL: {avg_pnl:.2f}%")
        
        if avg_pnl < -1.5:
             print("\n⚠️  CRITICAL: Portfolio is bleeding.")
             print("    Run 'python3 clean_ledger.py' to liquidate and reset.")
    else:
        print("⚠️  No price data available for held assets (Check Sensor).")

except Exception as e:
    print(f"❌ Error reading ledger: {e}")

print("---------------------------------------------------------")
