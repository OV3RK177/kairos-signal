import duckdb
import boto3
import os
import glob
import time
import sys
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# CONFIG
ROOT_VAULT = "/mnt/volume_nyc3_01/kairos_data"
DB_PATH = "/mnt/volume_nyc3_01/kairos_analytics/kairos_memory.db"
MATRIX_PATH = "/mnt/volume_nyc3_01/kairos_analytics/kairos_3000_matrix.csv"
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
STORAGE_CLASS = "DEEP_ARCHIVE"

# QUANT SETTINGS
DECAY_FACTOR = 0.94 # Standard RiskMetrics Lambda for EWMA

def refine_and_ship():
    print("🏭 REFINERY V3 (QUANT GRADE) ONLINE.")
    
    con = duckdb.connect(DB_PATH)
    
    # 1. Persistent Memory (For calculating Trends/Z-Scores)
    con.execute("""
        CREATE TABLE IF NOT EXISTS asset_memory (
            unique_id VARCHAR PRIMARY KEY,
            last_price DOUBLE,
            ewma_volatility DOUBLE,
            mean_volatility DOUBLE,
            volatility_std DOUBLE,
            sample_count INTEGER,
            last_updated TIMESTAMP
        )
    """)
    
    s3 = boto3.client('s3', region_name=os.getenv("AWS_DEFAULT_REGION"))

    while True:
        files = sorted(glob.glob(f"{ROOT_VAULT}/*.parquet"))
        if not files:
            time.sleep(5)
            continue
            
        print(f"🔥 CRUNCHING BATCH: {len(files)} files.")
        
        # Load batch into temp table
        files_str = "', '".join(files)
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE current_batch AS 
            SELECT 
                CASE 
                    WHEN meta LIKE '%sym%' THEN metric || '_' || json_extract_string(meta, '$.sym')
                    ELSE metric 
                END as unique_id,
                value,
                time
            FROM read_parquet(['{files_str}'])
        """)

        # --- THE QUANT UPGRADE (EWMA Logic) ---
        # 1. Calculate Instant Returns for this batch
        # 2. Update EWMA Volatility (Recursive calculation)
        # 3. Update Long-Term Mean/Std (For Z-Score)
        
        # Note: Doing recursive EWMA in pure SQL is hard, so we simplify:
        # We take the batch volatility and blend it with history.
        
        print("🧠 CALCULATING Z-SCORES & EWMA...")
        
        con.execute(f"""
            INSERT INTO asset_memory
            SELECT 
                unique_id, 
                AVG(value) as last_price,
                STDDEV(value) as ewma_volatility, -- Seed value for new assets
                STDDEV(value) as mean_volatility, 
                0 as volatility_std,
                COUNT(*) as sample_count,
                MAX(time) as last_updated
            FROM current_batch
            GROUP BY unique_id
            ON CONFLICT (unique_id) DO UPDATE SET
                -- EWMA Formula: Vol_New = (1-lambda)*Vol_Current + lambda*Vol_Old
                ewma_volatility = ({1-DECAY_FACTOR} * EXCLUDED.ewma_volatility) + ({DECAY_FACTOR} * asset_memory.ewma_volatility),
                
                -- Update Long Term Stats for Z-Score
                mean_volatility = ((asset_memory.mean_volatility * asset_memory.sample_count) + EXCLUDED.ewma_volatility) / (asset_memory.sample_count + 1),
                sample_count = asset_memory.sample_count + 1,
                last_price = EXCLUDED.last_price,
                last_updated = EXCLUDED.last_updated
        """)

        # --- GENERATE THE MATRIX (With Z-Scores) ---
        con.execute(f"""
            COPY (
                SELECT 
                    unique_id, 
                    CAST(sample_count AS INTEGER) as Liquidity_Count,
                    last_price as Price_Mean,
                    ewma_volatility as Volatility_Risk,
                    
                    -- THE ALPHA: How weird is this volatility right now?
                    CASE WHEN mean_volatility = 0 THEN 0 
                    ELSE (ewma_volatility - mean_volatility) / mean_volatility 
                    END as Z_Score_Anomaly
                    
                FROM asset_memory 
                ORDER BY Z_Score_Anomaly DESC
                LIMIT 3000
            ) TO '{MATRIX_PATH}' (HEADER, DELIMITER ',')
        """)

        # SHIP & PURGE
        for local_file in files:
            try:
                fname = os.path.basename(local_file)
                s3.upload_file(local_file, BUCKET_NAME, f"raw_ingest/{fname}", ExtraArgs={'StorageClass': STORAGE_CLASS})
                os.remove(local_file)
            except: pass

        print("💎 QUANT MATRIX UPDATED.")

if __name__ == "__main__":
    refine_and_ship()
