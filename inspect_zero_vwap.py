import sys
import os

# Tries to add current dir to path to locate your modules
sys.path.append(os.getcwd())

def scan_assets():
    print("🧠 KAIROS DIAGNOSTIC: Scanning for Zero-VWAP Assets...")
    
    # ---------------------------------------------------------
    # NOTE: Adjust this import to match where your 'stock_swarm' 
    # dictionary is actually located in your project structure.
    # ---------------------------------------------------------
    try:
        from core.cortex_engine import stock_swarm
    except ImportError:
        try:
            from core.data_loader import stock_swarm
        except ImportError:
            print("❌ Error: Could not auto-import 'stock_swarm'.")
            print("   Please edit this script and correct the import line.")
            return

    bad_assets = []
    
    # Iterate and check
    for ticker, data in stock_swarm.items():
        # Handle if data is dict or object
        vwap = data.get('vwap') if isinstance(data, dict) else getattr(data, 'vwap', None)
        
        if vwap is None or vwap == 0:
            bad_assets.append(ticker)

    # Report
    if bad_assets:
        print(f"\n⚠️ FOUND {len(bad_assets)} ASSETS WITH INVALID VWAP:")
        print("-" * 40)
        print(", ".join(bad_assets[:50])) 
        if len(bad_assets) > 50: print(f"...and {len(bad_assets)-50} more.")
        print("-" * 40)
        print("RECOMMENDATION: Run 'clean_ledger.py' on these specific tickers.")
    else:
        print("\n✅ No zero-VWAP assets found in loaded memory.")

if __name__ == "__main__":
    scan_assets()
