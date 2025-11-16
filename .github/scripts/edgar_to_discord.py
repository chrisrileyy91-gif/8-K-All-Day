import os
import requests
import feedparser

# === CONFIG ===

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

AI_TICKERS = [
    "NVDA", "AMD", "AVGO", "SMCI", "TSLA", "GOOGL", "MSFT", "META",
    "AMZN", "AAPL", "IBM", "QCOM", "DELL", "MU", "PLTR", "ADBE",
    "ORCL", "SNOW", "CRWD", "NET", "DDOG", "ZS", "PATH", "AI",
    "UPST", "SOFI", "RBLX", "DOCN", "IONQ", "AEHR", "UI", "CLSK"
]

POSTED_LOG = ".github/data/posted_filings.txt"

RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&owner=exclude&count=100&output=atom"


# === LOAD ALREADY POSTED FILINGS ===
def load_posted():
    if not os.path.exists(POSTED_LOG):
        return set()

    with open(POSTED_LOG, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_posted(posted_set):
    with open(POSTED_LOG, "w") as f:
        for url in posted_set:
            f.write(url + "\n")


# === DISCORD POST ===
def send_discord_message(title, link, company):
    data = {
        "content": f"📄 **New SEC Filing (AI Sector)**\n**{company}** — {title}\n{link}"
    }
    requests.post(WEBHOOK_URL, json=data)


# === MAIN ===
def run():
    print("Fetching SEC feed…")
    feed = feedparser.parse(RSS_URL)

    posted_before = load_posted()
    posted_now = set(posted_before)

    for entry in feed.entries:
        title = entry.title
        link = entry.link

        # Skip if already posted
        if link in posted_before:
            continue

        # Extract ticker if present (SEC Atom format often puts it in title)
        ticker = None
        words = title.replace(",", "").split()
        for w in words:
            if w.upper() in AI_TICKERS:
                ticker = w.upper()
                break

        # If no AI ticker → skip
        if ticker is None:
            continue

        # Post to Discord
        company_name = entry.get("company", "Unknown Company")
        send_discord_message(title, link, ticker)

        # Add to log
        posted_now.add(link)

    # Save updated log
    save_posted(posted_now)
    print("Done.")


if __name__ == "__main__":
    run()
