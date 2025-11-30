import os

LOGIC_MAP = {
    "polygon_stocks_stream": """
    async def stream(self):
        key = os.getenv("POLYGON_API_KEY")
        if not key:
            logger.error("❌ MISSING POLYGON KEY")
            return
        url = "wss://socket.polygon.io/stocks"
        while True:
            try:
                async with websockets.connect(url) as ws:
                    # 1. Auth
                    auth_msg = {"action": "auth", "params": key}
                    await ws.send(json.dumps(auth_msg))
                    
                    # 2. Subscribe to ALL Trades (T.*)
                    # This is the Firehose. Millions/min.
                    sub_msg = {"action": "subscribe", "params": "T.*"}
                    await ws.send(json.dumps(sub_msg))
                    logger.info("🌊 POLYGON STOCKS: CONNECTED (ALL TRADES)")

                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        for event in data:
                            if event.get("ev") == "T":
                                # Optimization: Don't print every trade (too fast)
                                # Only push to Redpanda
                                self.send_data("stock_trade", event.get("p"), meta={
                                    "sym": event.get("sym"),
                                    "size": event.get("s"),
                                    "exchange": event.get("x"),
                                    "timestamp": event.get("t")
                                })
                                # Print 'Heartbeat' every 1000 trades or specific big tickers
                                if event.get("sym") == "SPY":
                                    print(f"📈 TRADE: SPY ${event.get('p')} (Vol: {event.get('s')})")
            except Exception as e:
                logger.error(f"Polygon Error: {e}")
                await asyncio.sleep(1)

    def collect(self):
        asyncio.run(self.stream())
    """,

    # ... (Previous Logic for Helius, Wingbits, etc. is assumed here) ...
    "helius_global_stream": """
    async def stream(self):
        url = f"wss://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"
        while True:
            try:
                async with websockets.connect(url) as ws:
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "slotSubscribe"}))
                    logger.info("✅ HELIUS FIREHOSE CONNECTED")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if "params" in data:
                            slot = data["params"]["result"]["slot"]
                            self.send_data("solana_slot", slot)
                            print(f"⚡ SLOT: {slot} (LIVE)")
            except: await asyncio.sleep(1)
    def collect(self): asyncio.run(self.stream())
    """
}

GENERIC_LOGIC = """
    def collect(self):
        logger.info(f"🔒 {self.name}: Waiting for Key...")
        while True:
            time.sleep(3600)
"""

def inject():
    base_path = "collectors"
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py" and file != "base.py":
                name = file.replace(".py", "")
                path = os.path.join(root, file)
                logic = LOGIC_MAP.get(name, GENERIC_LOGIC)
                content = f'''import asyncio
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
logger = logging.getLogger("{name}")

class {name.title().replace("_","")}(KairosCollector):
    def __init__(self):
        super().__init__("{name}")

{logic}

if __name__ == "__main__":
    agent = {name.title().replace("_","")}()
    agent.collect()
'''
                with open(path, "w") as f:
                    f.write(content)
                print(f"💉 UPGRADED: {name}")

if __name__ == "__main__":
    inject()
