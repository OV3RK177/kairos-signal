import feedparser
import time
import os
from datetime import datetime, timezone
import clickhouse_connect
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
CH_PASS = os.getenv('CLICKHOUSE_PASSWORD', 'kairos')

# --- SOURCES (The Free Dragnet) ---
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    "https://theblockcrypto.com/rss.xml",
    "https://bitcoinmagazine.com/.rss/full/"
]

# --- SETUP ---
analyzer = SentimentIntensityAnalyzer()

try:
    client = clickhouse_connect.get_client(host=CH_HOST, port=8123, username='default', password=CH_PASS)
    # Ensure table exists
    client.query("""
        CREATE TABLE IF NOT EXISTS sentiment_stream (
            timestamp DateTime,
            source String,
            headline String,
            sentiment_score Float32,
            url String
        ) ENGINE = MergeTree() ORDER BY timestamp
    """)
    print("✅ Sentinel Connected to DB")
except Exception as e:
    print(f"❌ DB Error: {e}")
    exit(1)

def process_feeds():
    print("📡 Scanning Global News Feeds...")
    batch = []
    now = datetime.now(timezone.utc)
    
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            # Process top 5 newest articles from each feed
            for entry in feed.entries[:5]:
                title = entry.title
                link = entry.link
                
                # Check if we already have this (simple dedupe by time window could work, 
                # but for now we just rely on ClickHouse speed)
                
                # AI SENTIMENT SCORE (-1.0 to 1.0)
                score = analyzer.polarity_scores(title)['compound']
                
                # Source Name cleanup
                source_name = url.split('.')[1] # e.g. "cointelegraph"
                
                batch.append([now, source_name, title, score, link])
        except Exception as e:
            print(f"⚠️ Feed Error ({url}): {e}")

    if batch:
        try:
            client.insert('sentiment_stream', batch, column_names=['timestamp', 'source', 'headline', 'sentiment_score', 'url'])
            print(f"🗞️ Ingested {len(batch)} Headlines")
        except Exception as e:
            print(f"⚠️ Insert Error: {e}")

if __name__ == "__main__":
    while True:
        process_feeds()
        time.sleep(300) # Check every 5 minutes
