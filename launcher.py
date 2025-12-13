import multiprocessing
import time
import logging
import sys
import kairos_config as config

# Import Modules
from core.stream_feed import start_feed_process
from core.cortex_engine import run_cortex 

# Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
logger = logging.getLogger("SYSTEM")

if __name__ == "__main__":
    # 1. Memory Manager
    manager = multiprocessing.Manager()
    shared_memory = manager.dict()

    # 2. Asset Loader
    # TODO: Connect this to your real DB query
    assets = config.DEFAULT_WATCHLIST 
    
    # Generate dummy assets to test load if list is small
    if len(assets) < 100:
        logger.warning("⚠️ Using small asset list. Ensure DB query is connected for full 24k swarm.")

    # 3. Process Execution
    p_feed = multiprocessing.Process(target=start_feed_process, args=(shared_memory, assets))
    p_cortex = multiprocessing.Process(target=run_cortex, args=(shared_memory,))

    p_feed.start()
    p_cortex.start()

    logger.info("🚀 KAIROS PREMIUM SWARM STARTED.")

    try:
        p_feed.join()
        p_cortex.join()
    except KeyboardInterrupt:
        p_feed.terminate()
        p_cortex.terminate()
