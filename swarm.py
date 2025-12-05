# --- DNS PATCH START ---
import socket
dns_cache = {}
def getaddrinfo_patched(host, port, family=0, type=0, proto=0, flags=0):
    return socket._original_getaddrinfo(host, port, family, type, proto, flags)
# --- DNS PATCH END ---

import logging
from collectors.solana_batch import SolanaBatchCollector
from collectors.physical_batch import PhysicalBatchCollector
from collectors.grass import GrassCollector
from collectors.infrastructure_batch import InfrastructureBatchCollector
from collectors.polygon_batch import PolygonChainCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("swarm.log"), logging.StreamHandler()]
)
logger = logging.getLogger("KAIROS.SWARM")

def run_full_cycle():
    logger.info("🚀 KAIROS SWARM: INITIATING FULL CYCLE")
    
    # PHASE 1 & 2 DISABLED (API/DNS Issues)
    
    try:
        logger.info("--- PHASE 3: FORENSICS (Solana) ---")
        SolanaBatchCollector().run()
    except Exception as e: logger.error(f"Phase 3 Fail: {e}")

    # PHASE 4 DISABLED (Redundant Price Data / Rate Limits)

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

    logger.info("✅ CYCLE COMPLETE")

if __name__ == "__main__":
    run_full_cycle()
