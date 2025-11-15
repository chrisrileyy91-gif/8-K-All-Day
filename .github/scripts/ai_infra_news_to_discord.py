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
        for entry in feed.entries[:5]:
            # Skip entries without a publication date
            if not hasattr(entry, "published_parsed"):
                continue

            published = datetime(*entry.published_parsed[:6])

            # Only keep fresh articles
            if published >= cutoff:
                entries.append((published, entry))

    # Sort by most recent
    entries.sort(key=lambda x: x[0], reverse=True)
    return [e[1] for e in entries]


def send_to_discord(title, link):
    """Post a formatted AI update to Discord."""
    if not WEBHOOK_URL:
        print("❌ ERROR: DISCORD_WEBHOOK_AI is not set.")
        return

    opener = random.choice(OPENERS)
    message = f"{opener}\n\n**{title}**\n{link}"

    payload = {"content": message}
    r = requests.post(WEBHOOK_URL, json=payload)

    if r.status_code == 204:
        print("✅ Successfully posted to Discord.")
    else:
        print(f"❌ Discord returned status {r.status_code}: {r.text}")


def main():
    print("🔍 Fetching AI news...")
    entries = get_latest_entries()

    if not entries:
        print("⚠️ No fresh AI articles found.")
        return

    # Pick the top (most recent) article
    entry = entries[0]
    title = entry.title
    link = entry.link

    print(f"📨 Posting: {title}")
    send_to_discord(title, link)


if __name__ == "__main__":
    main()
