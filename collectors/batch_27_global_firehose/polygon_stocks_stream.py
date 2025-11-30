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
