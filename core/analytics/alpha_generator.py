import dask.dataframe as dd
import pandas as pd
import glob
import os
import json
import time
import sys

SOURCE_DIR = "/mnt/volume_nyc3_01/kairos_data"
OUTPUT_DIR = "/mnt/volume_nyc3_01/kairos_analytics"

def parse_meta(row):
    try:
        meta = row['meta']
        if isinstance(meta, str):
            meta = json.loads(meta.replace("'", '"'))
        
        # Priority ID Extraction
        if 'sym' in meta: return f"{row['metric']}_{meta['sym']}"
        if 'station' in meta: return f"{row['metric']}_{meta['station']}"
        if 'sensor_id' in meta: return f"{row['metric']}_{meta['sensor_id']}"
        if 'guild' in meta: return f"{row['metric']}_{meta['guild']}"
        return row['metric']
    except:
        return row['metric']

def generate_true_alpha():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    # 1. Load Recent Data (Last 50 files)
    files = sorted(glob.glob(f"{SOURCE_DIR}/*.parquet"))[-50:] 
    if not files:
        print("⚠️ Vault empty. Waiting for data...")
        return

    # 2. Load & Parse
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_parquet(f))
        except: pass
    
    if not dfs: return
    df = pd.concat(dfs)
    
    # 3. Explode Metadata
    df['unique_id'] = df.apply(parse_meta, axis=1)
    
    # 4. Calculate Metrics
    stats = df.groupby('unique_id')['value'].agg([
        ('Liquidity_Count', 'count'),
        ('Price_Mean', 'mean'),
        ('Volatility_Std', 'std'),
        ('Latest_Value', 'last')
    ]).reset_index()
    
    # 5. Sort & Save
    stats = stats.sort_values(by='Liquidity_Count', ascending=False).head(3000)
    
    csv_path = f"{OUTPUT_DIR}/kairos_3000_matrix.csv"
    stats.to_csv(csv_path, index=False)
    
    print(f"✅ MATRIX UPDATED: {len(stats)} Assets Tracked. (Rows: {len(df)})")

def daemon():
    print("🧠 ANALYST DAEMON ONLINE (5-Minute Loop)")
    while True:
        try:
            generate_true_alpha()
        except Exception as e:
            print(f"❌ Analyst Error: {e}")
        
        # Sleep 5 minutes (300s) to let buffer fill
        # Running this too fast wastes CPU re-calculating the same files
        time.sleep(300)

if __name__ == "__main__":
    # Flush output immediately for logs
    sys.stdout.reconfigure(line_buffering=True)
    daemon()
