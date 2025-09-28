import os, pathlib, time
import feedparser, requests

# SEC 8-K RSS feed (latest filings)
FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&count=100&output=atom"

# Grab webhook URL from GitHub Secret
WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# File to keep track of last seen entry so we don't double post
CURSOR_FILE = ".cursor"
last = ""
if pathlib.Path(CURSOR_FILE).exists():
    last = pathlib.Path(CURSOR_FILE).read_text().strip()

# Parse the feed
d = feedparser.parse(FEED)
entries = list(reversed(d.entries))  # oldest first

new_last = last
posted = 0

for e in entries:
    eid = getattr(e, "id", e.link)
    if eid == last:
        continue  # stop when we reach the last posted entry

    title = e.title
    link = e.link
    payload = {
        "content": f"📄 **New 8-K Filing**\n{title}\n🔗 {link}"
    }

    r = requests.post(WEBHOOK, json=payload)
    r.raise_for_status()

    posted += 1
    new_last = eid
    time.sleep(1)  # short pause to avoid hammering Discord

# Update cursor if new filings were posted
if posted:
    pathlib.Path(CURSOR_FILE).write_text(new_last)
