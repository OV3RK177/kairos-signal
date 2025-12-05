# --- DNS PATCH START ---
import socket
dns_cache = {}
def getaddrinfo_patched(host, port, family=0, type=0, proto=0, flags=0):
    return socket._original_getaddrinfo(host, port, family, type, proto, flags)
# --- DNS PATCH END ---

import logging
from collectors.depinscan_batch import DePINScanCollector
from collectors.solana_batch import SolanaBatchCollector
from collectors.market_batch import MarketBatchCollector
from collectors.deep_networks import DeepNetworkCollector
from collectors.physical_batch import PhysicalBatchCollector
from collectors.grass import GrassCollector
from collectors.infrastructure_batch import InfrastructureBatchCollector
from collectors.polygon_batch import PolygonChainCollector
from collectors.macro_batch import MacroBatchCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("swarm.log"), logging.StreamHandler()]
)
logger = logging.getLogger("KAIROS.SWARM")

def run_full_cycle():
    logger.info("🚀 KAIROS SWARM: INITIATING FULL CYCLE")
    
    try:
        logger.info("--- PHASE 1: GLOBAL SCAN (DePINscan) ---")
        DePINScanCollector().run()
    except Exception as e: logger.error(f"Phase 1 Fail: {e}")

    try:
        logger.info("--- PHASE 2: DEEP NETWORKS (Public APIs) ---")
        DeepNetworkCollector().run()
    except Exception as e: logger.error(f"Phase 2 Fail: {e}")

    try:
        logger.info("--- PHASE 3: FORENSICS (Solana) ---")
        SolanaBatchCollector().run()
    except Exception as e: logger.error(f"Phase 3 Fail: {e}")

    try:
        logger.info("--- PHASE 4: MARKET SWEEP ---")
        MarketBatchCollector().run()
    except Exception as e: logger.error(f"Phase 4 Fail: {e}")

    try:
        logger.info("--- PHASE 5: PHYSICAL REALITY ---")
        PhysicalBatchCollector().run()
    except Exception as e: logger.error(f"Phase 5 Fail: {e}")

    try:
        logger.info("--- PHASE 6: SPECIAL OPS (Grass) ---")
        GrassCollector().run()
    except Exception as e: logger.error(f"Phase 6 Fail: {e}")

    try:
        logger.info("--- PHASE 7: INFRASTRUCTURE (Proven Endpoints) ---")
        InfrastructureBatchCollector().run()
    except Exception as e: logger.error(f"Phase 7 Fail: {e}")

    try:
        logger.info("--- PHASE 8: POLYGON CHAIN ---")
        PolygonChainCollector().run()
    except Exception as e: logger.error(f"Phase 8 Fail: {e}")

    try:
        logger.info("--- PHASE 9: MACRO & SOCIAL (Tier 3) ---")
        MacroBatchCollector().run()
    except Exception as e: logger.error(f"Phase 9 Fail: {e}")

    logger.info("✅ CYCLE COMPLETE")

if __name__ == "__main__":
    run_full_cycle()
