import os

# Target file
file_path = 'core/cortex_engine.py'

# The bugged line (exact match)
target = 'vwap_div = (current_price - vwap) / vwap'

# The safe replacement (One-line conditional)
replacement = 'vwap_div = (current_price - vwap) / vwap if (vwap and vwap != 0) else 0.0'

if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    if target in content:
        new_content = content.replace(target, replacement)
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"✅ PATCH APPLIED: {file_path}")
        print(f"   Replaced unsafe division with safe check.")
    else:
        print(f"⚠️ TARGET NOT FOUND: Logic may already be patched or line differs.")
else:
    print(f"❌ FILE NOT FOUND: {file_path}")
