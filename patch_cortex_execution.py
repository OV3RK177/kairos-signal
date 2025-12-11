import os

file_path = 'core/cortex_engine.py'

# We look for the print statement and add a DB insert right after it
target_line = 'print(f"🚨 SIGNAL: {sig}", flush=True)'

# The code to inject (SQL Insert)
injection = """
                # --- AUTO EXECUTION (GLOBAL LEDGER) ---
                parts = sig.split('|')
                side_asset = parts[0].strip().split(' ') # ['BUY', 'BTC_USD']
                price_str = parts[0].split('@ $')[1] # '95000.00'
                
                side = side_asset[0]
                asset = side_asset[1]
                price = float(price_str)
                
                try:
                    client.command(f"INSERT INTO signal_ledger (timestamp, asset, signal_type, signal_price, entry_price, status) VALUES (now(), '{asset}', '{side}', {price}, {price}, 'OPEN')")
                    print(f"⚔️  ORDER SENT: {asset} to Ledger.", flush=True)
                except Exception as e:
                    print(f"❌ ORDER FAILED: {e}")
                # --------------------------------------
"""

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if target_line in line:
        # Add the injection with correct indentation
        new_lines.append(injection)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("✅ CORTEX PATCHED: Now executing trades directly to Ledger.")
