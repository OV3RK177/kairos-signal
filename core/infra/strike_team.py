import subprocess
import sys
import time
import os

# Define the Elite Squad (5 High-Value Targets Only)
TARGETS = [
    "core/storage/parquet_writer.py",         # The Catcher
    "core/storage/glacier_shipper.py",        # The Drain
    "collectors/batch_12_firehose/helius_global_stream.py", # Solana Firehose
    "collectors/batch_27_global_firehose/polygon_crypto_stream.py", # Crypto Firehose
    "collectors/batch_02_physical_sky/wingbits_adsb.py" # Sky Data
]

def launch():
    print("🚀 LAUNCHING STRIKE TEAM (Lean Mode)...")
    procs = []
    for script in TARGETS:
        if not os.path.exists(script):
            print(f"❌ MISSING: {script}")
            continue
            
        print(f"⚡ Activating: {script}")
        # Launch in background
        p = subprocess.Popen([sys.executable, script])
        procs.append(p)
        time.sleep(2)
    
    print(f"✅ TEAM ACTIVE ({len(procs)} Agents). Press Ctrl+C to stop.")
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 ABORTING MISSION...")
        for p in procs: p.terminate()

if __name__ == "__main__":
    launch()
