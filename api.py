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
BRIEFING_PATH = "/mnt/volume_nyc3_01/kairos_analytics/daily_briefing.md"
DEEP_PATH = "/mnt/volume_nyc3_01/kairos_analytics/deep_correlations.json"
LEDGER_PATH = "/mnt/volume_nyc3_01/kairos_analytics/ledger.json"

@app.get("/stats")
def stats():
    try:
        files = glob.glob(f"{VAULT_PATH}/*.parquet")
        count = len(files)
        return {"estimated_data_points": count * 1000, "shard_count": count, "status": "ingesting"}
    except: return {"status": "error"}

@app.get("/logs")
def logs():
    try:
        if os.path.exists("conductor.log"):
            res = subprocess.check_output("tail -n 50 conductor.log", shell=True).decode()
            return {"live_feed": [l for l in res.split('\n') if l.strip()]}
        return {"live_feed": []}
    except: return {"live_feed": []}

@app.get("/alpha")
def alpha():
    try:
        if os.path.exists(ANALYTICS_PATH):
            df = pd.read_csv(ANALYTICS_PATH)
            if 'Volatility_Std' in df.columns: df = df.rename(columns={'Volatility_Std': 'Volatility_Risk'})
            top = df.sort_values(by='Volatility_Risk', ascending=False).head(50)
            return {"data": top.fillna(0).to_dict(orient='records')}
        return {"data": []}
    except: return {"data": []}

@app.get("/briefing")
def briefing():
    try:
        if os.path.exists(LEDGER_PATH):
            with open(LEDGER_PATH, "r") as f:
                return {"history": json.load(f)}
        return {"history": []}
    except: return {"history": []}

@app.get("/deep-alpha")
def deep_alpha():
    try:
        if os.path.exists(DEEP_PATH):
            with open(DEEP_PATH, "r") as f:
                return json.load(f)
        return {"factors": []}
    except: return {"factors": []}

if __name__ == "__main__":
    import uvicorn
    print("🚀 API LISTENING ON PORT 8088")
    uvicorn.run(app, host="0.0.0.0", port=8088)
