import sys
import os
import time
import logging
import json
import websocket
from datetime import datetime

# Ensure parent directory is in path to import BaseCollector
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from collectors.base import BaseCollector

# --- CONFIG ---
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "YOUR_KEY_HERE") # Ensure this is in .env if needed
WS_URL = "wss://socket.polygon.io/stocks"

class PolygonFirehose(BaseCollector):
    def __init__(self):
        super().__init__("PolygonFirehose")
        self.ws = None

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            for event in data:
                if event.get('ev') == 'T': # Trade Event
                    symbol = event.get('sym')
                    price = event.get('p')
                    size = event.get('s')
                    
                    # LOG VISIBLY (So we know it's working)
                    print(f"📈 TRADE: {symbol} ${price}")
                    
                    # SAVE TO DB (The Missing Link)
                    self.save_metric(
                        metric_name="stock_price",
                        value=float(price),
                        tags={"project": "wallstreet", "symbol": symbol, "size": str(size)}
                    )
        except Exception as e:
            logging.error(f"Parse Error: {e}")

    def on_error(self, ws, error):
        logging.error(f"WS Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logging.warning("WS Closed. Reconnecting...")
        time.sleep(5)
        self.run()

    def on_open(self, ws):
        logging.info("WS Connected. Subscribing...")
        auth_data = {"action": "auth", "params": POLYGON_API_KEY}
        ws.send(json.dumps(auth_data))
        sub_data = {"action": "subscribe", "params": "T.NVDA,T.SPY,T.COIN,T.TSLA,T.AAPL,T.MSFT"}
        ws.send(json.dumps(sub_data))

    def run(self):
        # websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(WS_URL,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()

if __name__ == "__main__":
    collector = PolygonFirehose()
    collector.run()
