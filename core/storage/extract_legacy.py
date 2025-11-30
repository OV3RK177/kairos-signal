import pandas as pd
import os
from sqlalchemy import create_engine

# CONFIG
DB_URI = "postgresql://postgres:kairos@localhost:5433/kairos_db"
OUTPUT_DIR = "/mnt/volume_nyc3_01/kairos_legacy_processed"

def extract():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    print(f"⛏️  Connecting to TARGET: kairos_db (59GB)...")
    
    try:
        engine = create_engine(DB_URI)
        
        # 1. Find all tables
        tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema='public'", engine)
        table_list = tables['table_name'].tolist()
        print(f"📦 Found Tables: {table_list}")
        
        # 2. Extract each table
        for table in table_list:
            print(f"📥 Extracting Table: {table}...")
            
            chunk_size = 50000
            offset = 0
            
            while True:
                query = f"SELECT * FROM {table} LIMIT {chunk_size} OFFSET {offset}"
                df = pd.read_sql(query, engine)
                
                if df.empty:
                    break
                
                # *** THE FIX: SANITIZE COMPLEX TYPES ***
                # Convert any Object/Struct columns to String to satisfy Parquet
                for col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str)
                
                filename = f"{OUTPUT_DIR}/{table}_part_{offset}.parquet"
                
                # Use 'pyarrow' engine for better compatibility
                df.to_parquet(filename, engine='pyarrow', compression='snappy')
                
                print(f"   💾 Saved chunk: {filename} ({len(df)} rows)")
                offset += chunk_size
                
    except Exception as e:
        print(f"❌ Extraction Failed: {e}")

if __name__ == "__main__":
    extract()
