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
HELIUS_KEY = os.getenv("HELIUS_API_KEY")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HeliusFirehose")

class HeliusGlobalStream(KairosCollector):
    def __init__(self):
        super().__init__("helius_global_stream")
        self.url = f"wss://mainnet.helius-rpc.com/?api-key={HELIUS_KEY}"

    async def stream(self):
        while True:
            try:
                async with websockets.connect(self.url) as ws:
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "slotSubscribe"}))
                    logger.info("✅ HELIUS: CONNECTED")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if "params" in data:
                            slot = data["params"]["result"]["slot"]
                            self.send_data("solana_slot", slot)
                            print(f"⚡ SLOT: {slot} | 🟢 LIVE")
            except: await asyncio.sleep(1)

    def collect(self):
        asyncio.run(self.stream())

if __name__ == "__main__":
    HeliusGlobalStream().collect()
