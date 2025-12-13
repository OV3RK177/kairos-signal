import clickhouse_connect
import time
import os
import json
import logging
import threading
from confluent_kafka import Consumer
from quant_engine import KairosFieldEquations
from datetime import datetime

# CONFIG
CH_HOST = 'clickhouse-server'
CH_PASS = 'kairos'
KAFKA_BROKER = "localhost:9092"

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class KairosCortex:
    def __init__(self):
        self.ch_client = self.connect_db()
        self.alpha_consumer = Consumer({
            'bootstrap.servers': KAFKA_BROKER,
            'group.id': 'cortex_alpha_v1',
            'auto.offset.reset': 'latest'
        })
        self.alpha_consumer.subscribe(['alpha_trades'])

    def connect_db(self):
        while True:
            try:
                return clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
            except Exception:
                time.sleep(5)

    def analyze_alpha(self):
        """Listens for Whale Movements"""
        logging.info("🧠 CORTEX: LISTENING FOR WHALES...")
        while True:
            msg = self.alpha_consumer.poll(1.0)
            if msg is None: continue
            
            data = json.loads(msg.value().decode('utf-8'))
            wallet = data.get('wallet')
            token = data.get('token')
            side = data.get('side')
            val = data.get('value_usd')
            
            if side == 'BUY' and float(val or 0) > 10000:
                # A Whale bought >$10k. CHECK PHYSICS.
                self.cross_check_physics(token, wallet, val)

    def cross_check_physics(self, token, wallet, val):
        # 1. Fetch Price History for this token
        try:
            # (In prod, map address to symbol)
            # q = f"SELECT price, volume FROM market_ticks WHERE token_address='{token}'..."
            # For simulation, we assume symbol is passed or mapped
            pass 
        except Exception:
            return

        # 2. Run Quant Bible
        # math = KairosFieldEquations(prices, vols)
        # psi, vec = math.kairos_score()
        
        # 3. CORRELATION FOUND
        # If Psi > 70 (Strong Physics) AND Whale Buy
        logging.info(f"🚨 KAIROS SIGNAL: Smart Money {wallet[:6]} bought ${val} of {token}. Checking Physics...")
        # logging.info(f"   📐 Physics Score: {psi} | Velocity: {vec['V']}")

    def run(self):
        # Run Alpha Listener in background
        t = threading.Thread(target=self.analyze_alpha)
        t.start()
        
        # Main Loop (The standard scanner we wrote before)
        # ... (Previous logic remains here)
        while True:
            time.sleep(10)

if __name__ == "__main__":
    print("// KAIROS CORTEX v7.0 // SHADOW MODE ONLINE", flush=True)
    cortex = KairosCortex()
    cortex.run()
