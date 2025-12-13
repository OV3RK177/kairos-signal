import os

# ------------------------------------------------------------------
# 🔑 PRODUCTION KEYS
# ------------------------------------------------------------------
# You stated you provided the key. Ensure it is paste here.
BIRDEYE_API_KEY = "YOUR_KEY_GOES_HERE" 

# ------------------------------------------------------------------
# ⚙️ SYSTEM SETTINGS (PREMIUM PLUS TIER)
# ------------------------------------------------------------------
# Documentation standard: WSS URL with Key parameter
WSS_URL = f"wss://public-api.birdeye.so/socket/solana?x-api-key={BIRDEYE_API_KEY}"

# Logic Settings
UPDATE_INTERVAL = 0.5   # 500ms cycle (High Frequency)
RISK_TOLERANCE = 0.02   # 2% Deviation trigger
SHARD_SIZE = 100        # STRICT LIMIT per socket (from docs)

# ------------------------------------------------------------------
# 📋 ASSET DATABASE (MOCKED FOR LAUNCH)
# ------------------------------------------------------------------
# In production, this pulls from your 'stock_swarm' database.
# This placeholder ensures the swarm initializes even if DB is locked.
DEFAULT_WATCHLIST = [
    "So11111111111111111111111111111111111111112", # SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", # USDC
]
