# KAIROS SWARM LIMITS (V27)
# Derived from User Research & Official Docs

RATE_LIMITS = {
    # --- HIGH VELOCITY (Public/Blockchain) ---
    # Helium Blockchain API: 10 req/sec
    "helium_public": 0.1,  
    
    # DePINscan: 100 req/min
    "depinscan": 0.6,
    
    # --- MEDIUM VELOCITY (App APIs) ---
    # WeatherXM: 100 req/min
    "weatherxm": 0.6,
    
    # Nodle: 100 req/min
    "nodle": 0.6,
    
    # --- LOW VELOCITY (Commercial/Strict) ---
    # DIMO: 1000 req/hour
    "dimo": 3.6,
    
    # Hivemapper: 10,000 req/day
    "hivemapper": 8.6,
    
    # --- FINANCIAL ---
    "birdeye": 1.0,      # 1 req/s
    "dune": 4.0,         # 15 req/min
    "polygon": 0.01      # Unlimited (Paid)
}

# Global Pointer
CURRENT_POLYGON_LIMIT = RATE_LIMITS["polygon"]
