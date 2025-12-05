import feedparser

TOPICS = ["depin", "render network", "helium network", "hivemapper", "akash network"]

def scrape_social():
    batch = []
    # Scrape Reddit via RSS (No API Key needed)
    for topic in TOPICS:
        feed = feedparser.parse(f"https://www.reddit.com/r/{topic.replace(' ', '')}/new/.rss")
        count = len(feed.entries)
        if count > 0:
            batch.append(("social_sentiment", "reddit_activity_1h", count, {"topic": topic}))
            
        # Simple Sentiment Analysis (Keyword Match)
        bullish = sum(1 for x in feed.entries if "buy" in x.title.lower() or "moon" in x.title.lower())
        if bullish > 0:
            batch.append(("social_sentiment", "bullish_posts", bullish, {"topic": topic}))
            
    return batch
