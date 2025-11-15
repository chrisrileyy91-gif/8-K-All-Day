import os
import random
import feedparser
import requests
from datetime import datetime, timedelta

# Discord webhook
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_ETH")

# Ethereum ecosystem RSS feeds
FEEDS = [
    "https://decrypt.co/feed/ethereum",
    "https://cointelegraph.com/rss/tag/ethereum",
    "https://news.bitcoin.com/feed/",
    "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml&tags=ethereum",
    "https://thedefiant.io/feed"  # lots of ETH defi coverage
]

# Stack-style openers
OPENERS = [
    "🔗 Ethereum signal detected —",
    "🌐 New transmission from the ETH ecosystem —",
    "🚀 Layer-2 networks just pinged us —",
    "🧩 Smart contract activity spike —",
    "⚡ Fresh ETH intel uploaded to The Stack —",
]

# Prevent posting ancient articles (>7 days old)
DAYS_LIMIT = 7


def get_latest_entries():
    """Fetch recent Ethereum news articles."""
    entries = []
    cutoff = datetime.utcnow() - timedelta(days=DAYS_LIMIT)

    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            if not hasattr(entry, "published_parsed"):
                continue
            published = datetime(*entry.published_parsed[:6])
            if published >= cutoff:
                entries.append(entry)

    # Sort newest → oldest
    entries.sort(key=lambda x: datetime(*x.published_parsed[:6]), reverse=True)
    return entries


def format_message(entry):
    """Format a Discord message."""
    opener = random.choice(OPENERS)
    title = entry.title
    link = entry.link

    return f"**{opener}**\n📰 **{title}**\n🔗 {link}"


def post_to_discord(message):
    """Send message to Discord webhook."""
    if not WEBHOOK_URL:
        raise ValueError("Missing DISCORD_WEBHOOK_ETH environment variable")

    data = {"content": message}
    response = requests.post(WEBHOOK_URL, json=data)
    response.raise_for_status()


def main():
    entries = get_latest_entries()
    if not entries:
        print("No new Ethereum news found.")
        return

    # Pick the most recent article
    message = format_message(entries[0])
    post_to_discord(message)
    print("Posted Ethereum news update to Discord.")


if __name__ == "__main__":
    main()
