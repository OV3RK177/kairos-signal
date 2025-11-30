import asyncio
import json
import logging
import os
import sys
import time
import requests
import websockets
from dotenv import load_dotenv

sys.path.append(os.getcwd())
from collectors.base import KairosCollector

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("birdeye_trending_flow")

class BirdeyeTrendingFlow(KairosCollector):
    def __init__(self):
        super().__init__("birdeye_trending_flow")


    def collect(self):
        logger.info(f"🔒 {self.name}: Waiting for Key...")
        while True:
            time.sleep(3600)


if __name__ == "__main__":
    agent = BirdeyeTrendingFlow()
    agent.collect()
