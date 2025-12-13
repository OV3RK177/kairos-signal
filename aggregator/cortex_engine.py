import clickhouse_connect
import time
import os
import json
import logging
import sys
import numpy as np
from scipy.stats import entropy, linregress
from confluent_kafka import Consumer
from datetime import datetime

# CONFIG
CH_HOST = os.getenv('CH_HOST', 'clickhouse-server')
CH_PASS = os.getenv('CH_PASS', 'kairos')
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kairos_redpanda:9092')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] CORTEX: %(message)s', handlers=[logging.StreamHandler(sys.stdout)])

class TradeExecutor:
    def __init__(self, db_client):
        self.client = db_client
        self.positions = {} # { 'BTC-USD': {'entry': 50000, 'size': 1.0} }

    def execute(self, symbol, price, score):
        # 1. BUY LOGIC (Long Entry)
        if symbol not in self.positions and score > 80:
            self.positions[symbol] = {'entry': price, 'size': 1.0} # Fixed size for now
            self.record_trade(symbol, 'BUY', price, 1.0, 0.0, 'OPEN')
            logging.info(f"🚀 EXECUTE BUY: {symbol} @ {price} | Score: {score:.1f}")

        # 2. SELL LOGIC (Take Profit / Stop Loss)
        elif symbol in self.positions:
            entry = self.positions[symbol]['entry']
            # Close if Score drops below 50 OR Stop Loss hit (-2%)
            if score < 50:
                pnl = (price - entry) * self.positions[symbol]['size']
                self.record_trade(symbol, 'SELL', price, 1.0, pnl, 'CLOSED')
                del self.positions[symbol]
                logging.info(f"💰 EXECUTE SELL: {symbol} @ {price} | PnL: {pnl:.2f}")

    def record_trade(self, symbol, side, price, size, pnl, status):
        row = [datetime.now(), symbol, side, price, size, pnl, status]
        try:
            self.client.insert('kairos.trades', [row])
        except Exception as e:
            logging.error(f"Ledger Write Fail: {e}")

class KairosFieldEquations:
    def __init__(self, prices, volumes, window=20):
        self.prices = np.array(prices, dtype=np.float64)
        self.volumes = np.array(volumes, dtype=np.float64)
        self.window = window
        self.epsilon = 1e-10

    def kairos_score(self):
        try:
            if len(self.prices) < 5: return 50.0
            
            # 1. Velocity (Slope)
            slope, _, _, _, _ = linregress(np.arange(5), self.prices[-5:])
            V = (slope / self.prices[-1]) * 10000 

            # 2. Gravity (Mean Reversion)
            vwap = np.average(self.prices[-20:], weights=self.volumes[-20:])
            std = np.std(self.prices[-20:])
            G = 0.0 if std == 0 else (self.prices[-1] - vwap) / std

            # 3. Score Calc
            psi = 50.0 + (V * 0.5) - (G * 5.0)
            return max(0.0, min(100.0, psi))
        except: return 50.0

def run_cortex():
    logging.info(f"// KAIROS CORTEX v9.0 // EXECUTION ONLINE")
    
    # DB Connection
    client = None
    while not client:
        try:
            client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
            logging.info("✅ LEDGER CONNECTED")
        except: time.sleep(5)

    # Kafka Connection
    try:
        c = Consumer({'bootstrap.servers': KAFKA_BROKER, 'group.id': 'cortex_exec_v1', 'auto.offset.reset': 'latest'})
        c.subscribe(['market_ticks'])
    except Exception as e:
        logging.error(f"Kafka Fail: {e}")
        return

    # Init Executors
    trader = TradeExecutor(client)
    price_buffer = {}
    volume_buffer = {}
    
    while True:
        msg = c.poll(1.0)
        if msg is None: continue
        if msg.error(): continue

        try:
            data = json.loads(msg.value().decode('utf-8'))
            sym = data.get('symbol')
            p = float(data.get('price', 0))
            v = float(data.get('volume', 0))

            if sym not in price_buffer: 
                price_buffer[sym] = []
                volume_buffer[sym] = []
            
            price_buffer[sym].append(p)
            volume_buffer[sym].append(v)
            
            if len(price_buffer[sym]) > 50:
                price_buffer[sym].pop(0)
                volume_buffer[sym].pop(0)

            if len(price_buffer[sym]) >= 20:
                engine = KairosFieldEquations(price_buffer[sym], volume_buffer[sym])
                score = engine.kairos_score()
                
                # EXECUTE TRADE
                trader.execute(sym, p, score)

        except Exception as e:
            logging.error(f"Loop Error: {e}")

if __name__ == "__main__":
    run_cortex()
