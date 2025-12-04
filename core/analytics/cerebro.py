import duckdb
import boto3
import os
import glob
import time
import json
import subprocess
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# CONFIG
ROOT_VAULT = "/mnt/volume_nyc3_01/kairos_data"
DB_PATH = "/mnt/volume_nyc3_01/kairos_analytics/kairos_memory.db"
MATRIX_PATH = "/mnt/volume_nyc3_01/kairos_analytics/kairos_3000_matrix.csv"
LEDGER_PATH = "/mnt/volume_nyc3_01/kairos_analytics/ledger.json"
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
STORAGE_CLASS = "DEEP_ARCHIVE"

last_ai_run = 0

def run_cerebro():
    print("🧠 CEREBRO V3 (QUANT) ONLINE.")
    
    con = duckdb.connect(DB_PATH)
    try:
        s3 = boto3.client('s3', region_name=os.getenv("AWS_DEFAULT_REGION"))
    except: s3 = None

    # Ensure Tables Exist
    con.execute("CREATE TABLE IF NOT EXISTS raw_signals (time TIMESTAMP, project VARCHAR, metric VARCHAR, value DOUBLE, meta VARCHAR)")
    con.execute("""
        CREATE TABLE IF NOT EXISTS metrics_history (
            timestamp TIMESTAMP, 
            unique_id VARCHAR, 
            price_mean DOUBLE, 
            volatility_risk DOUBLE, 
            liquidity_count INTEGER,
            latest_value DOUBLE
        )
    """)

    while True:
        # --- 1. INGESTION ---
        files = sorted(glob.glob(f"{ROOT_VAULT}/*.parquet"))
        if files:
            print(f"🔥 PROCESSING {len(files)} FILES...")
            for local_file in files:
                try:
                    con.execute(f"INSERT INTO raw_signals SELECT time, project, metric, value, CAST(meta AS VARCHAR) FROM read_parquet('{local_file}')")
                    if s3:
                        fname = os.path.basename(local_file)
                        s3.upload_file(local_file, BUCKET_NAME, f"raw_ingest/{fname}", ExtraArgs={'StorageClass': STORAGE_CLASS})
                    os.remove(local_file)
                except: pass
            
            # --- 2. QUANT ANALYSIS (The Upgrade) ---
            print("📊 CALCULATING Z-SCORES & VELOCITY...")
            
            # We calculate stats over a 24h rolling window from the raw signals + history
            # Note: For true production speed, we'd use incremental aggregates, but this SQL is robust for <1B rows.
            
            con.execute(f"""
                COPY (
                    WITH window_stats AS (
                        SELECT 
                            CASE WHEN meta LIKE '%sym%' THEN metric || '_' || json_extract_string(meta, '$.sym') ELSE metric END as unique_id,
                            AVG(value) as mean_24h,
                            STDDEV(value) as std_24h,
                            COUNT(*) as count_24h,
                            LAST(value) as current_val
                        FROM raw_signals
                        GROUP BY 1
                    )
                    SELECT 
                        unique_id,
                        count_24h as Liquidity_Count,
                        mean_24h as Price_Mean,
                        std_24h as Volatility_Risk,
                        
                        -- Z-SCORE (How weird is this price?)
                        CASE WHEN std_24h = 0 THEN 0 
                             ELSE (current_val - mean_24h) / std_24h 
                        END as Z_Score,
                        
                        current_val as Latest_Value
                    FROM window_stats
                    ORDER BY Volatility_Risk DESC
                    LIMIT 3000
                ) TO '{MATRIX_PATH}' (HEADER, DELIMITER ',')
            """)
            
            # Persist this batch to history
            con.execute("INSERT INTO metrics_history SELECT now(), unique_id, Price_Mean, Volatility_Risk, Liquidity_Count, Latest_Value FROM read_csv_auto('" + MATRIX_PATH + "')")
            con.execute("DELETE FROM raw_signals") # Flush RAM

        # --- 3. AI ANALYST (Hourly) ---
        global last_ai_run
        if time.time() - last_ai_run > 3600:
            print("🤖 RUNNING AI ANALYST...")
            try:
                if os.path.exists(MATRIX_PATH):
                    df = pd.read_csv(MATRIX_PATH)
                    # We feed the AI the Z-Score now!
                    top_risk = df[['unique_id', 'Price_Mean', 'Volatility_Risk', 'Z_Score']].head(15).to_string(index=False)
                    
                    prompt = f"ANALYZE MARKET DATA. Focus on Z-Score anomalies (>3 is critical). Return JSON: {{'headline': '...', 'anomaly': '...', 'trade': '...', 'risk': '...'}}\n\nDATA:\n{top_risk}"
                    
                    cmd = ["ollama", "run", "kimi-k2-thinking:cloud", prompt]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    raw = result.stdout
                    start, end = raw.find('{'), raw.rfind('}') + 1
                    if start != -1:
                        entry = {"timestamp": str(datetime.now()), "report": json.loads(raw[start:end])}
                        history = []
                        if os.path.exists(LEDGER_PATH):
                            with open(LEDGER_PATH, 'r') as f: history = json.load(f)
                        history.insert(0, entry)
                        with open(LEDGER_PATH, 'w') as f: json.dump(history[:50], f)
                        last_ai_run = time.time()
            except: pass

        time.sleep(5)

if __name__ == "__main__":
    run_cerebro()
