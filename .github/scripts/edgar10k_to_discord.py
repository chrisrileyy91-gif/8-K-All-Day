import os, pathlib, time
import feedparser, requests

# SEC 10-K RSS feed
FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=10-K&count=100&output=atom"

# Webhook is injected by the workflow (do NOT hardcode)
WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# Separate cursor so it doesn't clash with 8-K
CURSOR_FILE = ".cursor_10k"
last = pathlib.Path(CURSOR_FILE).read_text().strip() if pathlib.Path(CURSOR_FILE).exists() else ""

feed = feedparser.parse(FEED)
entries = list(reversed(feed.entries))  # oldest -> newest
if not entries:
    raise SystemExit(0)

# First run: post only the newest item so you don't flood the channel
if not last:
    newest = entries[-1]
    title = getattr(newest, "title", "New 10-K Filing")
    link = getattr(newest, "link", "")
    r = requests.post(WEBHOOK, json={"content": f"📄 **New 10-K Filing**\n{title}\n🔗 {link}"})
    r.raise_for_status()
    pathlib.Path(CURSOR_FILE).write_text(getattr(newest, "id", link))
    raise SystemExit(0)

# Later runs: post everything newer than the cursor
new_last = last
posted = 0
for e in entries:
    eid = getattr(e, "id", getattr(e, "link", ""))
    if eid == last:
        continue
    title = getattr(e, "title", "New 10-K Filing")
    link = getattr(e, "link", "")
    r = requests.post(WEBHOOK, json={"content": f"📄 **New 10-K Filing**\n{title}\n🔗 {link}"})
    r.raise_for_status()
    posted += 1
    new_last = eid
    time.sleep(1)  # polite pacing

if posted:
    pathlib.Path(CURSOR_FILE).write_text(new_last)
