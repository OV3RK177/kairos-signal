import os
import time
import json
import clickhouse_connect
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')

# --- TARGETS ---
TARGETS = {
    'HELIUM': 'hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux',
    'HIVEMAPPER': '4vMsoUT2BWatFweudnQM1xedRLfJgJ7hswhcpz4xgBTy',
    'RENDER': 'rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof',
    'IO_NET': 'BZLbGTNnFdPrKh82qYCgtF2t3pG5U7F7j5C6x8k5token',
    'SHDW': 'SHDWyBxihqiCj6YekG2GUr7wqKLeLAMK1gHZck9pL6y',
    'MOBILE': 'mb1eu7TzEc71KxDpsmsKoucSSuuoGLv1drys1oP2jh6'
}

# --- RPC POOL MANAGER ---
class RPCPool:
    def __init__(self):
        self.endpoints = ["https://api.mainnet-beta.solana.com"]
        try:
            if os.path.exists('config/rpc_pool.json'):
                with open('config/rpc_pool.json', 'r') as f:
                    loaded = json.load(f)
                    if loaded: self.endpoints = loaded
        except Exception as e:
            print(f"⚠️ Config Load Error: {e}")
        self.current_index = 0

    def get_client(self):
        url = self.endpoints[self.current_index]
        # print(f"🔌 RPC: {url}") 
        return Client(url)

    def rotate(self):
        self.current_index = (self.current_index + 1) % len(self.endpoints)
        print(f"🔄 Rotating RPC >> {self.endpoints[self.current_index]}")

# --- DB CONNECTION ---
def get_db():
    return clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)

def init_db():
    try:
        client = get_db()
        client.command("""
        CREATE TABLE IF NOT EXISTS solana_firehose (
            timestamp DateTime,
            asset String,
            signature String,
            slot UInt64,
            err String
        ) ENGINE = MergeTree()
        ORDER BY (asset, timestamp)
        """)
    except Exception as e:
        print(f"CRITICAL DB ERROR: {e}")

# --- MAIN LOOP ---
def engage_firehose():
    pool = RPCPool()
    init_db()
    client = get_db()
    
    print("🔥 SOLANA FIREHOSE: ENGAGED")
    
    while True:
        rpc = pool.get_client()
        
        for asset, mint in TARGETS.items():
            try:
                pubkey = Pubkey.from_string(mint)
                # Gentle tap (limit 5) to avoid instant 429s
                resp = rpc.get_signatures_for_address(pubkey, limit=5)
                
                data = []
                # Check if we got valid signatures
                if resp.value:
                    for sig in resp.value:
                        row = [datetime.now(), asset, str(sig.signature), sig.slot, str(sig.err) if sig.err else "None"]
                        data.append(row)
                
                if data:
                    client.insert('solana_firehose', data, column_names=['timestamp', 'asset', 'signature', 'slot', 'err'])
                    print(f"⚡ {asset}: Captured {len(data)} sigs")
                
                # Pace ourselves
                time.sleep(2) 
                
            except Exception as e:
                print(f"🛑 Error on {asset}: {e}")
                pool.rotate()
                time.sleep(5)

if __name__ == "__main__":
    engage_firehose()
