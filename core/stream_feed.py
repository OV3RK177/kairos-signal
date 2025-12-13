import sys
import os
import asyncio
import websockets
import json
import logging

# 🔧 FORCE PATH FIX
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import kairos_config as config

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("KAIROS_SWARM")

class BirdeyeShard:
    """Manages 1 socket for 100 assets"""
    def __init__(self, shard_id, assets, shared_memory):
        self.id = shard_id
        self.assets = assets
        self.shared_memory = shared_memory
        self.url = config.WSS_URL

    async def connect(self):
        backoff = 1
        while True:
            try:
                # 🛡️ PROTOCOL: 'echo-protocol' required
                async with websockets.connect(
                    self.url, 
                    subprotocols=['echo-protocol'],
                    ping_interval=20, 
                    ping_timeout=20
                ) as ws:
                    
                    # SUBSCRIBE
                    unique_assets = list(set(self.assets))
                    sub_msg = {
                        "type": "SUBSCRIBE_PRICE",
                        "data": {
                            "chartType": "1m", 
                            "currency": "usd",
                            "address": ",".join(unique_assets)
                        }
                    }
                    
                    await ws.send(json.dumps(sub_msg))
                    
                    # LISTEN
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            m_type = data.get('type')

                            if m_type == 'PRICE_UPDATE':
                                p = data.get('data', {})
                                tk = p.get('address')
                                val = p.get('value')
                                
                                if tk and val:
                                    self.shared_memory[tk] = {
                                        'price': float(val),
                                        'vwap': float(val), 
                                        'valid': True
                                    }
                            
                            elif m_type == 'PING':
                                await ws.send(json.dumps({"type": "PONG"}))
                                
                        except:
                            continue

            except Exception:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 15)

async def start_swarm(shared_memory, full_asset_list):
    chunk_size = config.SHARD_SIZE
    chunks = [full_asset_list[i:i + chunk_size] for i in range(0, len(full_asset_list), chunk_size)]
    
    # Safety Cap
    if len(chunks) > 450: chunks = chunks[:450]

    logger.info(f"🔥 SWARM: Launching {len(chunks)} sockets...")
    tasks = [BirdeyeShard(i, chunk, shared_memory).connect() for i, chunk in enumerate(chunks)]
    await asyncio.gather(*tasks)

def start_feed_process(shared_memory, asset_list):
    try:
        asyncio.run(start_swarm(shared_memory, asset_list))
    except KeyboardInterrupt:
        pass
