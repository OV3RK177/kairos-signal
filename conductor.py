import subprocess
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
COLLECTOR_DIR = "/root/kairos-signal/collectors"

def ignite_swarm():
    print(f"🔥 KAIROS SWARM: INITIALIZING...")
    
    # 1. FIND THE MISSIONS
    missions = []
    for root, dirs, files in os.walk(COLLECTOR_DIR):
        for file in files:
            if file.endswith(".py") and file != "__init__.py" and file != "base.py":
                path = os.path.join(root, file)
                missions.append(path)
    
    if not missions:
        print(f"❌ CRITICAL: No collectors found in {COLLECTOR_DIR}")
        return

    print(f"📋 MISSION MANIFEST: {len(missions)} Units Found.")
    print(f"   - Batch 01 (Foundation): {sum('batch_01' in m for m in missions)} units")
    print(f"   - Batch 10 (Physical):   {sum('batch_10' in m for m in missions)} units")
    print(f"   - Batch 27 (Firehose):   {sum('batch_27' in m for m in missions)} units")
    
    # 2. LAUNCH THE SWARM
    procs = []
    for script in missions:
        try:
            # Run each collector in the background
            p = subprocess.Popen(["/root/kairos-signal/venv/bin/python3", script])
            procs.append(p)
        except Exception as e:
            print(f"   ⚠️ FAILED TO LAUNCH {os.path.basename(script)}: {e}")
            
    print(f"✅ SWARM ACTIVE. {len(procs)} Collectors Running.")
    
    try:
        while True: time.sleep(10)
    except KeyboardInterrupt:
        print("🛑 STOPPING SWARM...")
        for p in procs: p.terminate()

if __name__ == "__main__":
    ignite_swarm()
