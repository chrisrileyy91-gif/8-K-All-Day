import os
import requests
import feedparser

# === CONFIG ===

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
FORCE_TEST = os.getenv("FORCE_TEST", "0") == "1"  # <--- TEST MODE SWITCH

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


# === LOAD / SAVE ===
def load_posted():
    if not os.path.exists(POSTED_LOG):
        print("DEBUG: posted_filings.txt not found — creating it.")
        os.makedirs(".github/data", exist_ok=True)
        open(POSTED_LOG, "w").close()
        return set()

    with open(POSTED_LOG, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_posted(posted_set):
    with open(POSTED_LOG, "w") as f:
        for url in posted_set:
            f.write(url + "\n")


# === DISCORD POSTER ===
def send_discord_message(title, link, company):
    msg = {
        "content": (
            f"📄 **New SEC Filing (AI Sector)**\n"
            f"**{company}** — {title}\n{link}"
        )
    }
    r = requests.post(WEBHOOK_URL, json=msg)
    print("DEBUG: Discord POST status", r.status_code)
    return r.status_code


# === TEST MODE ===
def run_test_post():
    print("\n⚠️ TEST MODE ENABLED — Sending a fake AI SEC filing…")

    fake_title = "8-K — NVIDIA Corporation (NVDA) — Test Filing"
    fake_link = "https://www.sec.gov/fake_test_filing_nvda"
    fake_company = "NVIDIA Corporation"

    send_discord_message(fake_title, fake_link, fake_company)

    print("⚠️ Test post sent successfully (not logged, no duplicates).")
    print("⚠️ Exiting test mode.\n")


# === MAIN ===
def run():
    # Test mode override
    if FORCE_TEST:
        run_test_post()
        return

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
        print("DEBUG: Checking:", title)
        print("DEBUG: Link:", link)

        # Skip duplicates
        if link in posted_before:
            print("DEBUG: Already posted — skipping")
            continue

        # Extract ticker
        ticker = None
        cleaned = (
            title.replace(",", "")
                 .replace("(", "")
                 .replace(")", "")
        )
        for word in cleaned.split():
            if word.upper() in AI_TICKERS:
                ticker = word.upper()
                break

        print("DEBUG: Extracted ticker:", ticker)

        if ticker is None:
            print("DEBUG: Not AI — skipping")
            continue

        ai_hits += 1

        # Extract company name
        company_name = entry.get("company", None)
        if not company_name:
            summary = entry.get("summary", "")
            if "(" in summary:
                company_name = summary.split("(")[0].strip()
            else:
                company_name = "Unknown Company"

        print("DEBUG: Posting:", company_name)

        send_discord_message(title, link, company_name)

        # Log as posted
        posted_now.add(link)

    save_posted(posted_now)

    print("\n==============================")
    print("DEBUG: Script finished.")
    print("DEBUG: New AI filings posted:", ai_hits)
    print("DEBUG: Total stored filings:", len(posted_now))
    print("==============================\n")


if __name__ == "__main__":
    run()
