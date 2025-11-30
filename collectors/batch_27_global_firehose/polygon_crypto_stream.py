import asyncio
import websockets
import json
import logging
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.getcwd())
from collectors.base import KairosCollector

load_dotenv()
POLYGON_KEY = os.getenv("POLYGON_API_KEY")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PolygonCrypto")

class PolygonCryptoStream(KairosCollector):
    def __init__(self):
        super().__init__("polygon_crypto_stream")

    async def stream(self):
        if not POLYGON_KEY: return
        url = "wss://socket.polygon.io/crypto"
        while True:
            try:
                async with websockets.connect(url) as ws:
                    await ws.send(json.dumps({"action": "auth", "params": POLYGON_KEY}))
                    await ws.send(json.dumps({"action": "subscribe", "params": "XT.*"}))
                    logger.info("🌊 POLYGON CRYPTO: CONNECTED")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        for event in data:
                            if event.get("ev") == "XT":
                                print(f"🪙 CRYPTO: {event.get('pair')} ${event.get('p')}")
                                self.send_data("crypto_trade", event.get("p"), meta=event)
            except: await asyncio.sleep(5)

    def collect(self):
        asyncio.run(self.stream())

if __name__ == "__main__":
    PolygonCryptoStream().collect()
