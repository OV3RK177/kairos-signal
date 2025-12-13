import multiprocessing
import time
import os
import sys

# Import the Polygon Firehose
sys.path.append(os.getcwd())
from collectors.batch_27_global_firehose.polygon_stocks_stream import PolygonFirehose
# Import the BirdEye Swarm
from core.stream_feed import start_feed_process
import kairos_config as config

def run_polygon():
    print("🚀 LAUNCHING POLYGON FIREHOSE...")
    p = PolygonFirehose()
    p.run()

def run_birdeye():
    print("🚀 LAUNCHING BIRDEYE SWARM...")
    manager = multiprocessing.Manager()
    shared_mem = manager.dict()
    start_feed_process(shared_mem, config.DEFAULT_WATCHLIST)

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_polygon)
    p2 = multiprocessing.Process(target=run_birdeye)

    p1.start()
    p2.start()

    try:
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        p1.terminate()
        p2.terminate()
