import feedparser, requests, os, re

# RSS feed for recent SEC filings
FEED_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&count=100&output=atom"

# Keywords for filtering (AI, Tech, Robotics)
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
            "title": f"🚨 New SEC Fi
