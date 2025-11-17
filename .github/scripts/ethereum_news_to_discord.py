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
    "🔗 The ch
