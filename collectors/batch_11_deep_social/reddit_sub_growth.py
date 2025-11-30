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
logger = logging.getLogger("reddit_sub_growth")

class RedditSubGrowth(KairosCollector):
    def __init__(self):
        super().__init__("reddit_sub_growth")


    def collect(self):
        logger.info(f"🔒 {self.name}: Waiting for Key...")
        while True:
            time.sleep(3600)


if __name__ == "__main__":
    agent = RedditSubGrowth()
    agent.collect()
