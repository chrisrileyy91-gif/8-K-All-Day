import os
import random
import feedparser
import requests
from datetime import datetime, timedelta

# Discord webhook
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_ETH")

# File to track last posted Ethereum link
LAST_POSTED_FILE = "last_eth_posted.txt"

# Ethereum-only RSS feeds
FEEDS = [
    "https://blog.ethereum.org/en/feed.xml",
    "https://lido.fi/feed/",
    "https://bankless.ghost.io/rss/",
    "https://www.coinbureau.com/ethereum/feed/",
    "https://decrypt.co/feed/ethereum",
    "https://cointelegraph.com/tags/ethereum/feed",
    "https://thedefiant.io/feed"
]

# Allowed Ethereum keywords
ETH_KEYWORDS = [
    "ethereum", "eth", "layer-2", "l2",
    "arbitrum", "optimism", "base", "scroll",
    "zksync", "starknet", "eip", "staking",
]

# Blocked words (hard filter)
BLOCKED = [
    "bitcoin", "btc", "solana", "xrp", "cardano",
    "binance", "tether", "crime", "scandal", "controversy"
]

# Opening lines
OPENERS = [
    "🛰️ Layer-2 networks just pinged us —",
    "⚡ Ethereum nodes relayed a fresh update —",
    "🔗 The chain just finalized a new transmission —",
    "🧠 ETH validators surfaced new activity —",
    "🚀 Rollup ecosystems just delivered intel —",
]

# Prevent posting old news (>7 days)
DAYS_LIMIT = 7


def read_last_posted():
    """Reads the last posted Ethereum article link."""
    if not os.path.exists(LAST_POSTED_FILE):
        return None
    with open(LAST_POSTED_FILE, "r") as f:
        return f.read().strip()


def write_last_posted(link):
    """Saves the last posted Ethereum article link."""
    with open(LAST_POSTED_FILE, "w") as f:
        f.write(link)


def is_ethereum_article(entry):
    """Return True if article is Ethereum-related and not junk."""
    title = entry.title.lower()

    # Hard block first
    for bad in BLOCKED:
        if bad in title:
            return False

    # Require at least one ETH keyword
    for good in ETH_KEYWORDS:
        if good in title:
            return True

    return False


def get_latest_entries():
    """Fetch Ethereum-focused articles."""
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

            # Filter Ethereum content
            if is_ethereum_article(entry):
                entries.append(entry)

    # Sort by newest first
    entries.sort(key=lambda e: datetime(*e.published_parsed[:6]), reverse=True)
    return entries


def send_to_discord(entry):
    opener = random.choice(OPENERS)
    title = entry.title
    link = entry.link

    content = f"{opener}\n📄 **{title}**\n🔗 {link}"
    requests.post(WEBHOOK_URL, json={"content": content})


def main():
    last_posted = read_last_posted()
    articles = get_latest_entries()

    if not articles:
        return

    newest = articles[0]
    newest_link = newest.link.strip()

    # 🚫 Prevent duplicate posting
    if newest_link == last_posted:
        return  # Skip this cycle — no new article

    # ✅ New article → post it
    send_to_discord(newest)
    write_last_posted(newest_link)


if __name__ == "__main__":
    main()
