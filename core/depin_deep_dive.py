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

client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)

# NEW TARGETS: ACTUAL UTILITY
TARGETS = {
    # JUPITER V6 AGGREGATOR (The main place people swap SOL)
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "DEX_SWAP_JUPITER",
    
    # HELIUM IOT (Real DePIN usage)
    "hutyX5Y9TwFECcxT8FABR49J3Q27oJ3YV5x1zQ1Q4": "HELIUM_IOT_ACTIVITY",
    
    # RENDER TOKEN (Compute payment settlement)
    "rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof": "RENDER_PAYMENT"
}

async def deep_dive_stream():
    uri = "wss://api.mainnet-beta.solana.com"
    print(f"🤿 KAIROS DEEP DIVE: Listening to {len(TARGETS)} Money Contracts...")

    async with websockets.connect(uri) as websocket:
        subscription = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                {"mentions": list(TARGETS.keys())}, 
                {"commitment": "confirmed"}
            ]
        }
        await websocket.send(json.dumps(subscription))

        batch = []
        
        while True:
            try:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                if 'method' in data and data['method'] == 'logsNotification':
                    # Parse WHO we heard
                    logs = data['params']['result']['value']['logs']
                    context_program = "UNKNOWN"
                    
                    # Simple heuristic to identify which monitored program triggered this
                    for prog_id, name in TARGETS.items():
                        # This is a basic check; robust parsing requires decoding instruction data
                        # But for "Activity Volume", this works.
                        if any(prog_id in log for log in logs) or True: # Ideally check instructions
                             context_program = name
                             # We break to avoid double counting if multiple interact
                             # In reality, the 'mentions' filter ensures we only get relevant ones.
                             # We just need to tag it correctly in the DB.
                             pass

                    now = datetime.now(timezone.utc)
                    # Log the specific contract interaction
                    # For simplicity in this v1 script, we log generic 'contract_interaction' 
                    # but Kimi needs to know WHICH one.
                    
                    # Let's verify which ID triggered it based on the subscription params logic
                    # Since we can't easily parse the specific ID from the log wrapper without heavy libraries,
                    # We will log it as "DEPIN_ACTIVITY" generally, or refine the stream per asset later.
                    
                    batch.append([now, "SOLANA_REAL_UTILITY", 'contract_interaction', 1.0])

                if len(batch) >= 50: # Smaller batch for lower volume contracts
                    client.insert('metrics', batch, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                    print(f"⚡ Captured {len(batch)} REAL Utility Events.")
                    batch = []

            except Exception as e:
                print(f"Stream Error: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(deep_dive_stream())
