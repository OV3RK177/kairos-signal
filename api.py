from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import glob
import subprocess
import json

app = FastAPI(title="Kairos Signal")

# Allow CORS so your Mac can talk to this Droplet
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# CONFIG
# We look in the 100GB Volume for the data
VAULT_PATH = os.getenv("KAIROS_STORAGE_PATH", "/mnt/volume_nyc3_01/kairos_data")

@app.get("/")
def health():
    return {"status": "ONLINE", "system": "Kairos Signal Swarm"}

@app.get("/stats")
def stats():
    try:
        # Count files (Fast approximation)
        files = glob.glob(f"{VAULT_PATH}/*.parquet")
        count = len(files)
        
        # Estimate rows (50k per file based on HFT settings)
        est_rows = count * 50000
        
        return {
            "vault_path": VAULT_PATH,
            "shard_count": count,
            "estimated_data_points": est_rows,
            "status": "ingesting"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/logs")
def logs():
    try:
        # Tail the conductor log to show live activity
        # We grab the last 20 lines
        if os.path.exists("conductor.log"):
            result = subprocess.check_output("tail -n 20 conductor.log", shell=True).decode()
            clean_logs = [line for line in result.split('\n') if line.strip()]
            return {"live_feed": clean_logs}
        else:
            return {"live_feed": ["Log file not found yet... waiting for swarm."]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
