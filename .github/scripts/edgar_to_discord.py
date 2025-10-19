import feedparser, requests, os, re

# RSS feed for recent SEC filings
FEED_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&count=100&output=atom"

# Keywords for filtering
KEYWORDS = [
    "AI", "Artificial Intelligence", "Robotics", "Automation",
    "Semiconductor", "Chip", "Technology", "Software", "Hardware",
    "Data Center", "Machine Learning", "Neural Network"
]

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def matches_sector(text):
    return any(re.search(rf"\b{kw}\b", text, re.IGNORECASE) for kw in KEYWORDS)

def send_discord_message(entry):
    title = entry.get("title", "Untitled Filing")
    link = entry.get("link", "")
    company = entry.get("summary", "Unknown").split(" - ")[0]
    filing_type = title.split(" - ")[-1] if " - " in title else title
    message = {
        "embeds": [{
            "title": f"🚨 New SEC Filing: {filing_type}",
            "description": f"**{company}** just filed a **{filing_type}**.\n\n[View Filing on SEC.gov]({link})",
            "color": 5814783,
            "footer": {"text": "Edgar’s Edge | AI • Tech • Robotics"}
        }]
    }
    requests.post(WEBHOOK_URL, json=message)

def main():
    feed = feedparser.parse(FEED_URL)
    for entry in feed.entries:
        text = f"{entry.title} {entry.summary}"
        if matches_sector(text):
            send_discord_message(entry)

if __name__ == "__main__":
    main()
