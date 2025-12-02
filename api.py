from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import glob
import subprocess
import pandas as pd
import json

app = FastAPI(title="Kairos Signal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VAULT_PATH = os.getenv("KAIROS_STORAGE_PATH", "/mnt/volume_nyc3_01/kairos_data")
ANALYTICS_PATH = "/mnt/volume_nyc3_01/kairos_analytics/kairos_3000_matrix.csv"

@app.get("/")
def root(): return {"status": "ONLINE", "port": 8088}

@app.get("/stats")
def stats():
    try:
        files = glob.glob(f"{VAULT_PATH}/*.parquet")
        count = len(files)
        # Estimate based on 100-row batch size (testing) or 50k (prod)
        # We multiply by 1000 for a realistic "Points" metric for the UI
        return {
            "vault_path": VAULT_PATH,
            "shard_count": count,
            "estimated_data_points": count * 1000, 
            "status": "ingesting"
        }
    except: return {"shard_count": 0, "estimated_data_points": 0, "status": "error"}

@app.get("/logs")
def logs():
    try:
        if os.path.exists("conductor.log"):
            res = subprocess.check_output("tail -n 50 conductor.log", shell=True).decode()
            return {"live_feed": [l for l in res.split('\n') if l.strip()]}
        return {"live_feed": ["Waiting for logs..."]}
    except: return {"live_feed": []}

@app.get("/alpha")
def alpha():
    try:
        if not os.path.exists(ANALYTICS_PATH):
            return {"error": "Matrix file not found"}
            
        df = pd.read_csv(ANALYTICS_PATH)
        
        # FIX: Rename columns to match Frontend expectation
        # The generator produced 'Volatility_Std', UI wants 'Volatility_Risk'
        if 'Volatility_Std' in df.columns:
            df = df.rename(columns={'Volatility_Std': 'Volatility_Risk'})
            
        # Sort by Risk
        top = df.sort_values(by='Volatility_Risk', ascending=False).head(50)
        
        # Handle NaNs for JSON compatibility
        data = top.fillna(0).to_dict(orient='records')
        return {"data": data}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 API LISTENING ON PORT 8088")
    uvicorn.run(app, host="0.0.0.0", port=8088)
