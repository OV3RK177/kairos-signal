import asyncio
import aiohttp
import clickhouse_connect
import time
import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# CONFIG
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos') 
# API KEYS (Add these to .env later for full power)
OPENWEATHER_KEY = os.getenv('OPENWEATHER_KEY', '') 

class PlanetarySense:
    def __init__(self):
        self.client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
        self.buffer = []
        
    async def flush_buffer(self):
        if self.buffer:
            try:
                self.client.insert('metrics', self.buffer, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value'])
                print(f"⚡ [IoT] Flushed {len(self.buffer)} physics data points.")
                self.buffer = []
            except Exception as e:
                print(f"Write Error: {e}")

    async def fetch_open_aq(self, session):
        """Global Air Quality (Free - No Key)"""
        try:
            # Get latest measurements from major cities
            url = "https://api.openaq.org/v2/latest?limit=50&order_by=lastUpdated&sort=desc"
            async with session.get(url) as resp:
                data = await resp.json()
                now = datetime.now(timezone.utc)
                for result in data.get('results', []):
                    city = result['city'].replace(' ', '_').upper() if result.get('city') else "UNKNOWN"
                    for m in result['measurements']:
                        # Metric: IOT_AQI_NYC_PM25
                        slug = f"IOT_AQI_{city}"
                        metric = f"pm_{m['parameter']}"
                        self.buffer.append([now, slug, metric, float(m['value'])])
        except Exception as e:
            print(f"OpenAQ Error: {e}")

    async def fetch_weather_samples(self, session):
        """Weather Samples (Requires Free Key or uses wttr.in backup)"""
        # Using wttr.in JSON for keyless testing, acts as a proxy for global weather
        cities = ["New York", "London", "Tokyo", "Singapore"]
        now = datetime.now(timezone.utc)
        
        for city in cities:
            try:
                async with session.get(f"https://wttr.in/{city}?format=j1") as resp:
                    data = await resp.json()
                    current = data['current_condition'][0]
                    
                    slug = f"IOT_WEATHER_{city.upper()}"
                    self.buffer.append([now, slug, 'temp_c', float(current['temp_C'])])
                    self.buffer.append([now, slug, 'humidity', float(current['humidity'])])
                    self.buffer.append([now, slug, 'pressure', float(current['pressure'])])
            except:
                pass # Rate limits are common on free tiers

    async def fetch_solar_data(self, session):
        """NOAA Solar Data (Space Weather) - Affects Electronics/Radio"""
        try:
            # NOAA SWPC JSON feed
            url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
            async with session.get(url) as resp:
                data = await resp.json()
                if data:
                    latest = data[-1]
                    now = datetime.now(timezone.utc)
                    # K-Index (Geomagnetic Storm Level)
                    self.buffer.append([now, "IOT_SPACE_WEATHER", 'k_index', float(latest['kp_index'])])
        except Exception as e:
            print(f"Solar Error: {e}")

    async def run(self):
        print("🌍 IOT COLLECTOR RUNNING (Air, Weather, Space)...")
        async with aiohttp.ClientSession() as session:
            while True:
                # Run tasks concurrently
                await asyncio.gather(
                    self.fetch_open_aq(session),
                    self.fetch_weather_samples(session),
                    self.fetch_solar_data(session)
                )
                
                # Flush to ClickHouse
                await self.flush_buffer()
                
                # Respect Free Tier Limits (Run every 5 mins)
                print("💤 Sleeping 300s to respect free tiers...")
                await asyncio.sleep(300)

if __name__ == "__main__":
    collector = PlanetarySense()
    asyncio.run(collector.run())
