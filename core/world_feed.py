import time
import clickhouse_connect
import requests
import random
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 

# Simulated "World" Data for demonstration (Weather, Energy)
# In production, you would swap these for actual API calls (OpenWeather, EIA.gov)
def fetch_world_state():
    return {
        'global_energy_price': 120 + random.uniform(-5, 5), # $/MWh
        'avg_global_temp': 15 + random.uniform(-2, 2),     # Celsius
        'solar_flare_index': random.uniform(0, 10),         # K-index
        'eth_gas_gwei': 25 + random.uniform(-10, 50),       # Congestion
        'nasdaq_volatility': 18 + random.uniform(-1, 3)     # VIX
    }

def main():
    print("🌍 WORLD SENSOR ONLINE: Ingesting Environmental Variables...")
    try:
        client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
        
        while True:
            world_data = fetch_world_state()
            data = []
            now = datetime.now(timezone.utc)
            
            for metric, value in world_data.items():
                # We log this as "GLOBAL" project so it applies to everything
                data.append([now, 'GLOBAL', metric, float(value)])
            
            client.insert('metrics', data, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
            print(f"✅ Injected {len(data)} Environmental datapoints.")
            time.sleep(60)
            
    except Exception as e:
        print(f"❌ World Sensor Failed: {e}")

if __name__ == "__main__":
    main()
