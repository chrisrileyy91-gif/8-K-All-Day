import os
import random
import feedparser
import requests
from datetime import datetime, timedelta

# Discord webhook
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_AI")

# File to track last posted AI link
LAST_POSTED_FILE = "last_ai_posted.txt"

# 🚀 MASSIVE AI NEWS RSS SUPERSET
FEEDS = [
    # Mainstream AI News
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/artificial-intelligence/index.xml",
    "https://www.wired.com/feed/tag/artificial-intelligence/latest/rss",

    # High-cred tech outlets
    "https://arstechnica.com/tag/artificial-intelligence/feed/",
    "https://www.cnbc.com/id/19854910/device/rss/rss.html",  # AI category
    "https://feeds.feedburner.com/thenextweb",  # TNW tech + AI

    # AI Research, Papers, Breakthroughs
    "https://www.marktechpost.com/feed/",
    "https://ai.googleblog.com/feeds/posts/default?alt=rss",
    "https://openai.com/blog/rss.xml",
    "https://deepmind.google/discover/rss.xml",
    "https://huggingface.co/blog/feed.xml",

    # Enterprise AI, ML Ops
    "https://www.infoq.com/ai-ml/rss/",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
    "https://cloud.google.com/blog/topics/ai-ml-feed.xml",
    "https://azure.microsoft.com/en-us/blog/topics/ai/feed/",

    # Academic + ML Research Digests
    "https://machinelearningmastery.com/blog/feed/",
    "https://paperswithcode.com/feeds/latest",
    "https://aiweekly.co/feed",

    # Ethics, Governance, Policy
    "https://www.brookings.edu/tag/artificial-intelligence/feed/",
    "https://www.nature.com/subjects/artificial-intelligence.rss",
]

# Stack-style openers (unchanged)
OPENERS = [
    "🛰️ Stack satellites just intercepted an AI broadcast —",
    "🤖 The Stack’s sensors picked up new activity in AI systems —",
    "📡 Transmission received from the neural frontier —",
    "🧠 Stack AI just decoded a new artificial intelligence signal —",
    "🚀 Stack satellites relayed this fresh AI intelligence —",
]

# Prevent posting ancient articles (>7 days)
DAYS_LIMIT = 7


def read_last_posted():
    """Reads last posted AI article URL."""
    if not os.path.exists(LAST_POSTED_FILE):
        return None
    with open(LAST_POSTED_FILE, "r") as f:
        return f.read().strip()


def write_last_posted(link):
    """Saves last posted AI article URL."""
    with open(LAST_POSTED_FILE, "w") as f:
        f.write(link)


def get_latest_entries():
    """Fetch AI-focused articles."""
    entries = []
    cutoff = datetime.utcnow() - timedelta(days=DAYS_LIMIT)

    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            if not hasattr(entry, "published_parsed"):
                continue

            published = datetime(*entry.published_parsed[:6])
            if published < cutoff:
                continue

            entries.append((published, entry))

    entries.sort(key=lambda x: x[0], reverse=True)
    return [e[1] for e in entries]


def send_to_discord(title, link):
    """Send formatted AI news to Discord."""
    opener = random.choice(OPENERS)
    message = f"{opener}\n\n**{title}**\n{link}"

    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)


def main():
    last_posted = read_last_posted()
    entries = get_latest_entries()

    if not entries:
        return

    entry = entries[0]
    title = entry.title
    link = entry.link.strip()

    # 🚫 Prevent duplicate posting
    if last_posted == link:
        return

    # ✅ Post new AI intelligence
    send_to_discord(title, link)
    write_last_posted(link)


if __name__ == "__main__":
    main()
