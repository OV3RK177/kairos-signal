import os, sys, time, requests, ccxt
import clickhouse_connect
from datetime import datetime
from dotenv import load_dotenv
from fredapi import Fred
from polygon import RESTClient
from newsapi import NewsApiClient
from textblob import TextBlob
from colorama import Fore, Style, init

init(autoreset=True)
load_dotenv()

# DB Connection
CH_HOST = "localhost"
client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password='kairos')

class KairosAdvancedSensor:
    def __init__(self):
        print(f"{Fore.CYAN}>>> KAIROS SENSOR: ONLINE & WATCHING...", flush=True)
        try:
            self.fred = Fred(api_key=os.getenv('FRED_API_KEY'))
            self.polygon = RESTClient(os.getenv('POLYGON_API_KEY'))
            self.news_api = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
            self.weather_key = os.getenv('OPENWEATHER_KEY')
        except Exception as e:
            print(f"{Fore.RED}[CRITICAL] Auth Failed: {e}", flush=True)
            sys.exit(1)

        self.proxies = {
            'SPY': 'SPY', 'QQQ': 'QQQ', 'MSTR': 'MSTR', 
            'USO': 'USO', 'GLD': 'GLD', 'HYG': 'HYG'
        }
        self.metrics = []

    def log(self, metric, value):
        """Buffers data for DB insertion"""
        if value is None: return
        print(f"{Fore.GREEN}   -> {metric}: {value}", flush=True)
        self.metrics.append([datetime.now(), 'omni_sensor', metric, float(value), 'SENSOR_FUSION'])

    def run_cycle(self):
        self.metrics = [] # Reset buffer
        print(f"\n{Fore.YELLOW}--- SCANNING REALITY [{datetime.now().strftime('%H:%M:%S')}] ---", flush=True)

        # 1. WEATHER (Physical Demand)
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat=35.98&lon=-96.76&appid={self.weather_key}&units=imperial"
            res = requests.get(url, timeout=5).json()
            if res.get('cod') == 200:
                temp = res['main']['temp']
                self.log('cushing_temp_f', temp)
                # Binary flag: 1 = Extreme Weather (High Energy Demand), 0 = Normal
                is_extreme = 1.0 if (temp < 32 or temp > 95) else 0.0
                self.log('energy_demand_risk', is_extreme)
        except: pass

        # 2. MACRO (Yields)
        try:
            yc = self.fred.get_series('T10Y2Y').iloc[-1]
            self.log('yield_curve_10y2y', yc)
        except: pass

        # 3. MARKET (Polygon)
        for name, ticker in self.proxies.items():
            try:
                snap = self.polygon.get_snapshot_ticker("stocks", ticker)
                price = snap.day.close
                change = snap.todays_change_percent
                self.log(f"{name.lower()}_price", price)
                self.log(f"{name.lower()}_change_pct", change)
            except: pass

        # 4. SENTIMENT (NewsAPI)
        try:
            news = self.news_api.get_top_headlines(category='business', language='en', country='us')
            articles = news.get('articles', [])
            score = 0
            count = 0
            for a in articles:
                if a['title']:
                    score += TextBlob(a['title']).sentiment.polarity
                    count += 1
            avg_score = score / count if count > 0 else 0
            self.log('global_sentiment_score', avg_score)
        except: pass

        # 5. FLUSH TO DB
        if self.metrics:
            try:
                client.insert('metrics', self.metrics, column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value', 'source'])
                print(f"{Fore.CYAN}>>> SYNCED {len(self.metrics)} DATAPOINTS TO CORE.", flush=True)
            except Exception as e:
                print(f"{Fore.RED}DB WRITE ERROR: {e}", flush=True)

if __name__ == "__main__":
    sensor = KairosAdvancedSensor()
    while True:
        try:
            sensor.run_cycle()
            time.sleep(60) # Scan every 60 seconds
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"LOOP ERROR: {e}")
            time.sleep(10)
