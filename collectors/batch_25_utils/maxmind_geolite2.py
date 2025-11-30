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
logger = logging.getLogger("maxmind_geolite2")

class MaxmindGeolite2(KairosCollector):
    def __init__(self):
        super().__init__("maxmind_geolite2")


    def collect(self):
        logger.info(f"🔒 {self.name}: Waiting for Key...")
        while True:
            time.sleep(3600)


if __name__ == "__main__":
    agent = MaxmindGeolite2()
    agent.collect()
