import asyncio
import websockets
import json
import clickhouse_connect
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 

# CLICKHOUSE CLIENT (The only DB fast enough for this)
client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)

async def solana_stream():
    uri = "wss://api.mainnet-beta.solana.com"
    
    print(f"🔌 CONNECTING TO SOLANA WSS: {uri}")
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to "Slot" (New Block) updates - occurs every ~400ms
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "slotSubscribe"
        }))
        
        # Subscribe to "Vote" (Consensus) - MASSIVE VOLUME
        # Warn: This is the true firehose.
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "voteSubscribe"
        }))

        print("🚀 FIREHOSE ACTIVE. STREAMING RAW DATA...")
        
        batch = []
        last_flush = datetime.now()

        while True:
            try:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                if 'method' in data and data['method'] == 'slotNotification':
                    # Extract Slot Info
                    slot = data['params']['result']['slot']
                    parent = data['params']['result']['parent']
                    root = data['params']['result']['root']
                    
                    # 1. SLOT METRIC
                    batch.append([datetime.now(), 'SOLANA_CHAIN', 'slot_height', float(slot)])
                    
                    # 2. VELOCITY METRIC (Slot Delta)
                    batch.append([datetime.now(), 'SOLANA_CHAIN', 'slot_delta', float(slot - root)])
                
                elif 'method' in data and data['method'] == 'voteNotification':
                     # Just counting raw votes as "Network Activity" proxy
                     # We don't log every vote content (too big), just the TICK
                     batch.append([datetime.now(), 'SOLANA_CHAIN', 'consensus_tick', 1.0])

                # BATCH INSERT (To prevent crashing)
                if len(batch) >= 5000:
                    client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                    print(f"⚡ Flushed {len(batch)} raw data points to ClickHouse.")
                    batch = []

            except Exception as e:
                print(f"Stream Error: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(solana_stream())
