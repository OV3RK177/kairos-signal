from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import glob
import subprocess

app = FastAPI(title="Kairos Signal")

# CONFIG
VAULT_PATH = os.getenv("KAIROS_STORAGE_PATH", "/mnt/volume_nyc3_01/kairos_data")

@app.get("/")
def health():
    return {"status": "ONLINE", "system": "Kairos Signal Swarm"}

@app.get("/stats")
def stats():
    try:
        # Count files (Fast approximation of volume)
        files = glob.glob(f"{VAULT_PATH}/*.parquet")
        count = len(files)
        
        # Estimate rows (assuming 50k per file based on HFT settings)
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
    # Tail the conductor log to show live activity
    try:
        # Read last 10 lines of the swarm log
        result = subprocess.check_output("tail -n 10 conductor.log", shell=True).decode()
        return {"live_feed": result.split('\n')}
    except:
        return {"live_feed": "No logs found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
