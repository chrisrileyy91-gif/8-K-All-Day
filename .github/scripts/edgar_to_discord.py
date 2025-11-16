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

RSS_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent"
    "&CIK=&type=&company=&owner=exclude&count=100&output=atom"
)


# === LOAD ALREADY POSTED FILINGS ===
def load_posted():
    if not os.path.exists(POSTED_LOG):
        print("DEBUG: posted_filings.txt not found — creating a new one.")
        os.makedirs(".github/data", exist_ok=True)
        open(POSTED_LOG, "w").close()
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
        "content": (
            "📄 **New SEC Filing (AI Sector)**\n"
            f"**{company}** — {title}\n{link}"
        )
    }
    r = requests.post(WEBHOOK_URL, json=data)
    print("DEBUG: Discord POST status:", r.status_code)


# === MAIN ===
def run():
    print("Fetching SEC feed…")
    feed = feedparser.parse(RSS_URL)

    posted_before = load_posted()
    posted_now = set(posted_before)

    print("DEBUG: Loaded posted filings:", len(posted_before))

    ai_hits = 0

    for entry in feed.entries:
        title = entry.title
        link = entry.link

        print("\n------------------------------")
        print("DEBUG: Checking filing:", title)
        print("DEBUG: Link:", link)

        # SKIP if already posted
        if link in posted_before:
            print("DEBUG: Already posted — skipping")
            continue

        # Extract ticker from title text
        ticker = None
        words = title.replace(",", "").replace("(", "").replace(")", "").split()
        upper_words = [w.upper() for w in words]

        for w in upper_words:
            if w in AI_TICKERS:
                ticker = w
                break

        print("DEBUG: Detected ticker:", ticker)

        # Skip if not AI-related
        if ticker is None:
            print("DEBUG: Not AI — skipping")
            continue

        ai_hits += 1

        # SEC Atom sometimes includes company name under entry.summary
        company_name = entry.get("company", None)
        if not company_name:
            # Try to extract from summary if formatted like "Company Name (CIK)"
            summary = entry.get("summary", "")
            if "(" in summary:
                company_name = summary.split("(")[0].strip()
            else:
                company_name = "Unknown Company"

        print("DEBUG: Posting to Discord:", company_name)

        # Send message
        send_discord_message(title, link, company_name)

        # Store in posted log
        posted_now.add(link)

    # Save posted log
    save_posted(posted_now)

    print("\n==============================")
    print("DEBUG: Script finished.")
    print("DEBUG: New AI filings posted:", ai_hits)
    print("DEBUG: Total stored filings:", len(posted_now))
    print("==============================\n")


if __name__ == "__main__":
    run()
