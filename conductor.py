import subprocess
import os
import sys
import time

def find_collectors():
    collectors = []
    for root, dirs, files in os.walk("collectors"):
        for file in files:
            if file.endswith(".py") and file != "__init__.py" and file != "base.py":
                collectors.append(os.path.join(root, file))
    return collectors

def ignite_swarm():
    scripts = find_collectors()
    if not scripts:
        print("❌ NO COLLECTORS FOUND.")
        return

    print(f"🔥 IGNITING SWARM: {len(scripts)} Units detected.")
    
    processes = []
    try:
        for script in scripts:
            print(f"🚀 Launching {script}...")
            p = subprocess.Popen([sys.executable, script])
            processes.append(p)
            time.sleep(0.2) # Fast launch
            
        print(f"✅ SWARM ACTIVE ({len(processes)} Threads). Press Ctrl+C to kill all.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 KILLING SWARM...")
        for p in processes:
            p.terminate()

if __name__ == "__main__":
    ignite_swarm()
