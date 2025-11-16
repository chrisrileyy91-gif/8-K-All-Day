import os
import requests
import feedparser
from datetime import datetime, timedelta

# -------- Discord Webhook (existing secret) --------
WEBHOOK_URL = os.getenv("EDGAR_THE_8")

# -------- AI Tickers (always allowed) --------
AI_TICKERS = {
    "NVDA","MSFT","GOOGL","META","AMZN","TSLA","SMCI","PLTR","IBM",
    "AMD","AVGO","TSM","AI","AIP","AIQ","AIPO","RGTI","IONQ","QUBT","SNOW"
}

# -------- AI Keyword Detector (Hybrid Mode) --------
AI_KEYWORDS = [
    "artificial intelligence", " ai ", " ai.", "machine learning", "neural",
    "deep learning", "inference", "transformer", "llm", "large language model",
    "automation", "gpu", "cuda", "robotics", "vision model", "generative",
    "quantum", "data center", "accelerator"
]

# -------- SEC Atom Feed --------
FEED_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&"
    "owner=include&output=atom"
)

# -------- Utility Logic --------
def ticker_matches(ticker):
    if not ticker:
        return False
    return ticker.upper() in AI_TICKERS

def contains_ai_keywords(text):
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in AI_KEYWORDS)

# -------- Send to Discord --------
def send_to_discord(title, link, company, ticker):
    embed = {
        "title": f"New AI-Related Filing — {title}",
        "description": f"**{company}** ({ticker})\n\n{link}",
        "color": 0x00FFB3
    }
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]})
    except Exception as e:
        print(f"Discord error: {e}")

# -------- Main Scanner --------
def run():
    feed = feedparser.parse(FEED_URL)

    for entry in feed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        company = entry.get("company", "Unknown Company")
        ticker = entry.get("xbrl_ticker", "")

        # --- RULE 1: ALWAYS allow known AI companies ---
        if ticker_matches(ticker):
            send_to_discord(title, link, company, ticker.upper())
            continue

        # --- RULE 2: If filing mentions AI keywords ---
        if contains_ai_keywords(summary):
            send_to_discord(title, link, company, ticker.upper())
            continue

    print("AI-filtered SEC scan complete.")

if __name__ == "__main__":
    run()
