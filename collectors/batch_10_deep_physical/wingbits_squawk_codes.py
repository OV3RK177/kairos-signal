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
logger = logging.getLogger("wingbits_squawk_codes")

class WingbitsSquawkCodes(KairosCollector):
    def __init__(self):
        super().__init__("wingbits_squawk_codes")


    def collect(self):
        logger.info(f"🔒 {self.name}: Waiting for Key...")
        while True:
            time.sleep(3600)


if __name__ == "__main__":
    agent = WingbitsSquawkCodes()
    agent.collect()
