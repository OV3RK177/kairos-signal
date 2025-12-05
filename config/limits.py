# KAIROS SWARM LIMITS
# Define the heartbeat interval (in seconds) for each source

RATE_LIMITS = {
    # High Speed (RPCs)
    "helius": 0.1,       # 10 req/s (Free Tier)
    "iotex": 0.2,        # 5 req/s (Public)
    
    # Mid Speed (APIs)
    "birdeye": 1.0,      # 1 req/s (Public limit)
    "grass": 5.0,        # 1 req/5s (WAF safety)
    
    # Low Speed (Analytical)
    "dune": 4.0,         # 15 req/min
    "the_graph": 30.0,   # 2 req/min
    
    # UNLEASHED (Paid Plan)
    "polygon": 0.01      # 100 req/s (effectively unlimited)
}

# Set global limit pointer
CURRENT_POLYGON_LIMIT = RATE_LIMITS["polygon"]
