import os
import random
import feedparser
import requests
from datetime import datetime, timedelta

# Discord webhook
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_AI")

# Reliable AI news RSS feeds
FEEDS = [
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/artificial-intelligence/index.xml",
    "https://www.wired.com/feed/tag/artificial-intelligence/latest/rss"
]

# Stack-style openers
OPENERS = [
    "🛰️ Stack satellites just intercepted an AI broadcast —",
    "🤖 The Stack’s sensors picked up new activity in AI systems —",
    "📡 Transmission received from the neural frontier —",
    "🧠 Stack AI just decoded a new artificial intelligence signal —",
    "🚀 Stack satellites relayed this fresh AI intelligence —",
]

# Prevent posting ancient articles (e.g., >7 days old)
DAYS_LIMIT = 7


def get_latest_entries():
    """Fetch recent AI news articles from multiple sources."""
    entries = []
    cutoff = datetime.utcnow() - timedelta(days=DAYS_LIMIT)

    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            # Skip if there's no date
            if not hasattr(entry, "published_parsed"):
                continue
            published = datetime(*entry.published_parsed[:6])
            if published >= cutoff:
                entries.append(entry)

    # Sort by recency
    entries.sort(ke
