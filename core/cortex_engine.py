import sys
import os
import time
import logging
import statistics

# 🔧 FORCE PATH FIX: Add parent directory to sys.path
# This ensures we find 'kairos_config' even if run from a subprocess
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    import kairos_config as config
except ImportError:
    # Fallback prevents crash if config is temporarily locked
    class config:
        UPDATE_INTERVAL = 1
        RISK_TOLERANCE = 0.02
        MIN_LIQUIDITY = 5000

logger = logging.getLogger("KAIROS_CORTEX")

# 🌍 CONTEXT ASSETS (Read-Only)
# We use these to gauge network health and geopolitical stability
INFRA_KEYWORDS = ["NODE", "VALIDATOR", "RPC", "INFRA", "STAKING", "LIDO", "ROCKET"]
FOREX_KEYWORDS = ["FOREX", "EUR", "JPY", "GBP", "CHF", "AUD", "CAD", "NZD", "KRW"]

def get_asset_type(ticker_name):
    """
    Classifies asset: 'TRADEABLE' or 'CONTEXT_ONLY'
    """
    if not ticker_name: return 'TRADEABLE' 
    
    uname = ticker_name.upper()
    
    # 1. FOREX = CONTEXT ONLY (Geopolitical/Macro Trends)
    for kw in FOREX_KEYWORDS:
        if kw in uname: return 'CONTEXT_ONLY'

    # 2. NODES = CONTEXT ONLY (Network Health)
    for kw in INFRA_KEYWORDS:
        if kw in uname: return 'CONTEXT_ONLY'

    return 'TRADEABLE'

def run_cortex(shared_memory):
    logger.info("🧠 CORTEX ONLINE. Forex & Nodes set to [READ-ONLY] for Context.")
    
    while True:
        try:
            # 1. READ SNAPSHOT
            market_data = dict(shared_memory)
            if not market_data:
                time.sleep(1)
                continue
            
            # 2. CALCULATE MACRO CONTEXT
            # We use ALL valid prices (Tradeable + Forex + Nodes) to feel the pulse
            valid_items = [v for v in market_data.values() if v.get('valid')]
            prices = [d['price'] for d in valid_items]
            
            if not prices: continue

            # Macro Sentiment (Simple Average for now)
            # In V3, we can split this: Forex Volatility vs Crypto Volatility
            global_avg = statistics.mean(prices)
            
            signals = 0
            
            # 3. GENERATE SIGNALS (Selective)
            for token, data in market_data.items():
                price = data.get('price')
                vwap = data.get('vwap')
                
                # Mock Ticker Name (In Prod: db.get_name(token))
                ticker_name = "SOL_TOKEN" 

                asset_class = get_asset_type(ticker_name)

                # 🛡️ CONTEXT ONLY FILTER
                # We monitored them for global_avg above, but we SKIP trading logic here.
                if asset_class == 'CONTEXT_ONLY':
                    # logger.debug(f"🔍 Analyzing Context: {ticker_name}")
                    continue

                # ✅ TRADING LOGIC (Pure Assets Only)
                if vwap and vwap > 0:
                    deviation = (price - vwap) / vwap
                    
                    if abs(deviation) > config.RISK_TOLERANCE:
                        if price > config.MIN_LIQUIDITY:
                            # signals += 1
                            pass

            time.sleep(config.UPDATE_INTERVAL)

        except Exception as e:
            logger.error(f"❌ Cortex Error: {e}")
            time.sleep(1)
