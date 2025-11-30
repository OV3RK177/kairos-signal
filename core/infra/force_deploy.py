import os

# CONFIGURATION
BASE_DIR = "collectors"
KEYS = {
    "POLYGON": os.getenv("POLYGON_API_KEY"),
    "HELIUS": os.getenv("HELIUS_API_KEY")
}

# 1. POLYGON STOCKS (Wall Street Firehose)
STOCKS_CODE = """import asyncio
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
logger = logging.getLogger("PolygonStocks")

class PolygonStocksStream(KairosCollector):
    def __init__(self):
        super().__init__("polygon_stocks_stream")

    async def stream(self):
        if not POLYGON_KEY:
            logger.error("❌ NO POLYGON KEY")
            return
        
        url = "wss://socket.polygon.io/stocks"
        while True:
            try:
                async with websockets.connect(url) as ws:
                    await ws.send(json.dumps({"action": "auth", "params": POLYGON_KEY}))
                    await ws.send(json.dumps({"action": "subscribe", "params": "T.*"}))
                    logger.info("🌊 POLYGON STOCKS: CONNECTED")
                    
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        for event in data:
                            if event.get("ev") == "T":
                                # Send to Redpanda
                                self.send_data("stock_trade", event.get("p"), meta=event)
                                # Log Blue Chips Only to console (reduce noise)
                                if event.get("sym") in ["SPY", "NVDA", "TSLA", "AAPL"]:
                                    print(f"📈 TRADE: {event.get('sym')} ${event.get('p')} (x{event.get('s')})")
            except Exception as e:
                logger.error(f"Connection Error: {e}")
                await asyncio.sleep(5)

    def collect(self):
        asyncio.run(self.stream())

if __name__ == "__main__":
    PolygonStocksStream().collect()
"""

# 2. POLYGON CRYPTO (24/7 Activity)
CRYPTO_CODE = """import asyncio
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
"""

# 3. HELIUS FIREHOSE (Solana)
HELIUS_CODE = """import asyncio
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
"""

# WRITE FILES
def deploy():
    print("🚀 FORCE DEPLOYING WARHEADS...")
    
    # Write Polygon Stocks
    with open("collectors/batch_27_global_firehose/polygon_stocks_stream.py", "w") as f:
        f.write(STOCKS_CODE)
    print("✅ Wrote: polygon_stocks_stream.py")
    
    # Write Polygon Crypto
    with open("collectors/batch_27_global_firehose/polygon_crypto_stream.py", "w") as f:
        f.write(CRYPTO_CODE)
    print("✅ Wrote: polygon_crypto_stream.py")
    
    # Write Helius
    with open("collectors/batch_12_firehose/helius_global_stream.py", "w") as f:
        f.write(HELIUS_CODE)
    print("✅ Wrote: helius_global_stream.py")

if __name__ == "__main__":
    deploy()
