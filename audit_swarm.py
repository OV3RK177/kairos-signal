import os

def audit():
    print("🔍 AUDITING SWARM LOGIC...")
    real_count = 0
    ghost_count = 0
    
    for root, dirs, files in os.walk("collectors"):
        for file in files:
            if file.endswith(".py") and "__" not in file and "base" not in file:
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                    
                # If it contains the generic placeholder text
                if 'logger.info("📡 STARTED: {project_name}")' in content or 'placeholder' in content:
                    # It's a Ghost
                    ghost_count += 1
                elif 'requests.get' in content or 'websockets.connect' in content:
                    # It's Real
                    print(f"✅ REAL: {file}")
                    real_count += 1
                else:
                    ghost_count += 1

    print("-" * 30)
    print(f"💀 GHOSTS (Templates): {ghost_count}")
    print(f"⚔️  SOLDIERS (Real):   {real_count}")
    print("-" * 30)

if __name__ == "__main__":
    audit()
