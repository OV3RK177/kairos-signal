import clickhouse_connect
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='kairos')

# Inject a fake BUY order for SOL
# We set the price low ($100) so it shows a massive profit immediately
print("💉 INJECTING TEST SIGNAL...", flush=True)
try:
    client.insert('signal_ledger', 
                  [[datetime.now(), 'SOL', 'BUY', 100.00, 'TEST_SIGNAL']], 
                  column_names=['timestamp', 'asset', 'action', 'signal_price', 'reason'])
    print("✅ Test Signal Injected: BOUGHT SOL @ $100.00")
except Exception as e:
    print(f"❌ Error: {e}")
