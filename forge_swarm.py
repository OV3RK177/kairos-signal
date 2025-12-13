import time
import json
import random
import logging
import numpy as np
from confluent_kafka import Producer

# CONFIG
KAFKA_BROKER = 'localhost:9092'
BATCH_SIZE = 50

# ASSET MANIFEST (The sectors we are tracking)
ASSETS = {
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "HNT-USD", "MOBILE-USD"],
    "STOCKS": ["TSLA", "NVDA", "AAPL", "AMD", "COIN"],
    "DEPIN":  ["DIMO", "HONEY", "IOT", "POKT", "FIL"]
}

logging.basicConfig(format='%(asctime)s [%(levelname)s] SWARM: %(message)s', level=logging.INFO)

def get_producer():
    return Producer({'bootstrap.servers': KAFKA_BROKER})

def generate_price_walk(last_price):
    # Random Walk (Brownian Motion)
    shock = np.random.normal(0, 1)
    drift = 0
    change = last_price * (drift + shock * 0.002)
    return max(0.01, last_price + change)

def run_swarm():
    p = get_producer()
    prices = {ticker: random.uniform(10, 1000) for cat in ASSETS.values() for ticker in cat}
    
    logging.info("🔥 SWARM ACTIVATED: Streaming Market Data...")
    
    while True:
        try:
            for category, tickers in ASSETS.items():
                for ticker in tickers:
                    # 1. Simulate Price Move
                    prices[ticker] = generate_price_walk(prices[ticker])
                    
                    # 2. Create Packet
                    payload = {
                        "timestamp": time.time(),
                        "symbol": ticker,
                        "price": round(prices[ticker], 2),
                        "volume": random.randint(100, 5000),
                        "sector": category
                    }
                    
                    # 3. Fire to Kafka
                    # We send to 'market_ticks' which Cortex listens to
                    p.produce('market_ticks', json.dumps(payload).encode('utf-8'))
            
            p.flush()
            time.sleep(0.5) # Throttle (simulate 2 ticks/sec per asset)
            
        except KeyboardInterrupt:
            print("\n🛑 Swarm Stopped")
            break
        except Exception as e:
            logging.error(f"Swarm Jammed: {e}")
            time.sleep(1)

if __name__ == "__main__":
    run_swarm()
