import dask.dataframe as dd
import os
import glob
import time

# CONFIG
SOURCE_DIR = "/mnt/volume_nyc3_01/kairos_legacy_processed"

def generate_report():
    print("📊 ANALYST ENGINE STARTING...")
    
    # 1. Locate Shards
    files = glob.glob(f"{SOURCE_DIR}/*.parquet")
    if not files:
        print("❌ No data found in legacy vault.")
        print(f"   Checked: {SOURCE_DIR}")
        return

    print(f"📦 Loading {len(files)} data shards from {SOURCE_DIR}...")
    
    try:
        # 2. Lazy Load (Dask)
        df = dd.read_parquet(files, engine='pyarrow')
        
        # 3. Compute Schema
        print("🔎 Analyzing Data Structure...")
        print(f"   Columns: {list(df.columns)}")
        
        # 4. The Heavy Lift (Count Rows)
        print("🧮 Crunching Total Volume (This relies on Disk I/O)...")
        start = time.time()
        total_rows = len(df)
        duration = time.time() - start
        
        print("\n" + "="*50)
        print("   KAIROS SIGNAL: PRELIMINARY INTELLIGENCE   ")
        print("="*50)
        print(f"🔥 TOTAL DATA POINTS: {total_rows:,}")
        print(f"⏱️  Processing Time:  {duration:.2f}s")
        
        # 5. Node Count (If applicable)
        if 'ip_address' in df.columns:
            print("👥 Calculating Unique Network Nodes...")
            unique_nodes = df['ip_address'].nunique().compute()
            print(f"🌍 UNIQUE NODES TRACKED: {unique_nodes:,}")
        
        # 6. Time Range
        if 'timestamp' in df.columns:
             print("⏳ Calculating Time Horizon...")
             min_time = df['timestamp'].min().compute()
             max_time = df['timestamp'].max().compute()
             print(f"📅 Timeframe: {min_time} to {max_time}")
            
        print("="*50)
        print("✅ Ready for publication.")
        
    except Exception as e:
        print(f"❌ Analysis Error: {e}")

if __name__ == "__main__":
    generate_report()
