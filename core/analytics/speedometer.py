import os
import glob
import time
import pyarrow.parquet as pq

# TARGET: The Live Vault (New Data)
VAULT = "/mnt/volume_nyc3_01/kairos_data"

def check_speed():
    print("⏱️  MEASURING SWARM VELOCITY (Scanning last 60 seconds)...")
    
    now = time.time()
    one_min_ago = now - 60
    
    recent_files = []
    total_rows = 0
    
    # Scan directory
    files = glob.glob(f"{VAULT}/*.parquet")
    
    for f in files:
        if os.path.getmtime(f) > one_min_ago:
            recent_files.append(f)
            try:
                meta = pq.read_metadata(f)
                total_rows += meta.num_rows
            except: pass

    print("\n" + "="*40)
    print(f"🚀 KAIROS LIVE VELOCITY")
    print("="*40)
    print(f"📂 Files/Min:      {len(recent_files)}")
    print(f"⚡ Rows Per Minute: {total_rows:,}")
    print(f"📅 Projected Daily: {total_rows * 60 * 24:,}")
    print("="*40)

if __name__ == "__main__":
    check_speed()
