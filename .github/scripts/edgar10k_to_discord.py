import os
import re
import requests
import feedparser

# === CONFIG ===

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
POSTED_LOG = ".github/data/posted_crypto_filings.txt"

CRYPTO_KEYWORDS = [
    "crypto", "cryptocurrency", "digital asset", "bitcoin", "ethereum",
    "blockchain", "token", "web3", "smart contract", "mining",
    "stablecoin", "ledger", "exchange", "defi"
]

RSS_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcurrent&CIK=&type=&owner=exclude&count=200&output=atom"
)


# === POSTED LOG HANDLING ===
def load_posted():
    if not os.path.exists(POSTED_LOG):
        return set()
    with open(POSTED_LOG, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_posted(posted_set):
    with open(POSTED_LOG, "w") as f:
        for link in posted_set:
            f.write(link + "\n")


# === UTILS ===
def matches_crypto(text: str) -> bool:
    return any(re.search(rf"\b{kw}\b", text, re.IGNORECASE) for kw in CRYPTO_KEYWORDS)


def send_discord_message(entry, match_keyword):
    title = entry.title
    link = entry.link
    summary = entry.get("summary", "")
    company = summary.split(" - ")[0] if " - " in summary else summary[:200]

    embed = {
        "embeds": [{
            "title": f"🛰️ New SEC Filing (Crypto • {match_keyword})",
            "description": f"**{company}**\n\n{title}\n\n[🔗 View Filing]({link})",
            "color": 0x7289DA,
            "footer": {"text": "Crypto + Ethereum Filings Feed • Powered by The Stack"}
        }]
    }

    requests.post(WEBHOOK_URL, json=embed)


# === MAIN ===
def run():
    feed = feedparser.parse(RSS_URL)
    posted_before = load_posted()
    posted_now = set(posted_before)

    for entry in feed.entries:
        link = entry.link
        text = f"{entry.title} {entry.get('summary', '')}"

        # Skip duplicates
        if link in posted_before:
            continue

        # Check for crypto signals
        matched = None
        for kw in CRYPTO_KEYWORDS:
            if re.search(rf"\b{kw}\b", text, re.IGNORECASE):
                matched = kw
                break

        if not matched:
            continue

        # Post to Discord
        send_discord_message(entry, matched)
        posted_now.add(link)

    save_posted(posted_now)


if __name__ == "__main__":
    run()
