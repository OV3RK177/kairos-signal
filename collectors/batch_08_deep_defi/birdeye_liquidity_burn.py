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
logger = logging.getLogger("birdeye_liquidity_burn")

class BirdeyeLiquidityBurn(KairosCollector):
    def __init__(self):
        super().__init__("birdeye_liquidity_burn")


    def collect(self):
        logger.info(f"🔒 {self.name}: Waiting for Key...")
        while True:
            time.sleep(3600)


if __name__ == "__main__":
    agent = BirdeyeLiquidityBurn()
    agent.collect()
