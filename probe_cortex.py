import sys
import random

# We will modify the engine to print 'Reasons for Rejection'
file_path = 'core/cortex_engine.py'

print(f"💉 INJECTING PROBE into {file_path}...")

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
injected = False

for line in lines:
    new_lines.append(line)
    
    # We look for the start of the analysis loop to inject our debug flag
    # Assuming the loop starts with something like "for ticker, data in stock_swarm.items():"
    if "for ticker, data" in line and not injected:
        # Add a debug flag that triggers only once per loop
        new_lines.append("        # --- PROBE INJECTION ---\n")
        new_lines.append("        debug_mode = (random.random() < 0.0001) # 1 in 10k chance to log\n")
        new_lines.append("        if debug_mode: print(f'🔎 PROBE [{ticker}]: Price={current_price}, VWAP={vwap}, Vol={volume}')\n")
        injected = True

# Write back
with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("✅ PROBE INSTALLED. Restart Cortex to see sample decision logic.")
