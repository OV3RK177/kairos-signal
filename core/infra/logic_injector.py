import os

LOGIC_MAP = {
    "wingbits_adsb": """
    def collect(self):
        url = "https://api.wingbits.com/v1/network/stats"
        while True:
            try:
                data = requests.get(url, timeout=10).json()
                self.send_data("sky_activity", data.get("aircraft_count", 0), meta=data)
                print(f"✈️ WINGBITS: {data.get('aircraft_count', 0)} Aircraft")
            except: pass
            time.sleep(60)
    """,
    "solana_fees": """
    def collect(self):
        url = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"
        while True:
            try:
                payload = {"jsonrpc": "2.0", "id": 1, "method": "getRecentPrioritizationFees", "params": [["CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"]]}
                res = requests.post(url, json=payload).json()
                fees = [x['prioritizationFee'] for x in res.get('result', [])]
                avg = sum(fees)/len(fees) if fees else 0
                self.send_data("solana_pressure", avg)
                print(f"💸 SOL PRESSURE: {avg:.2f} micro-lamports")
            except: pass
            time.sleep(15)
    """,
    "coingecko_vol": """
    def collect(self):
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana,render-token,helium&vs_currencies=usd&include_24hr_vol=true"
        while True:
            try:
                data = requests.get(url).json()
                for token, stats in data.items():
                    vol = stats.get('usd_24h_vol', 0)
                    self.send_data(f"{token}_vol", vol, meta=stats)
                    print(f"📊 {token.upper()}: Vol ${vol:,.0f}")
            except: pass
            time.sleep(60)
    """,
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
                            print(f"⚡ SLOT: {slot} | 🟢 LIVE")
            except: await asyncio.sleep(1)

    def collect(self):
        asyncio.run(self.stream())
    """
}

GENERIC_LOGIC = """
    def collect(self):
        logger.info(f"📡 ACTIVATING: {self.name}")
        while True:
            self.send_data(f"{self.name}_heartbeat", 1.0, meta={"status": "polling"})
            # Silence generic prints to clean up logs
            # print(f"💓 {self.name.upper()}: Active") 
            time.sleep(60)
"""

def inject_logic():
    base_path = "collectors"
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py" and file != "base.py":
                name = file.replace(".py", "")
                path = os.path.join(root, file)
                logic = LOGIC_MAP.get(name, GENERIC_LOGIC)
                
                new_content = f'''import asyncio
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
                    f.write(new_content)
                print(f"💉 INJECTED: {name}")

if __name__ == "__main__":
    inject_logic()
