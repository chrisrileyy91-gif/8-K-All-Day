import os, pathlib, time
import feedparser, requests

# SEC 8-K feed (latest)
FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&count=100&output=atom"

# Injected by GitHub Actions
WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# Cursor to remember the last item we've posted
CURSOR_FILE = ".cursor"
last = pathlib.Path(CURSOR_FILE).read_text().strip() if pathlib.Path(CURSOR_FILE).exists() else ""

# Be polite to SEC: include a User-Agent (put an email you check)
fp = feedparser.parse(
    FEED,
    request_headers={"User-Agent": "EDGAR-Bot (youremail@example.com)"}
)
entries = list(reversed(fp.entries))  # oldest -> newest

if not entries:
    raise SystemExit(0)

def item_id(e):
    return str(getattr(e, "id", getattr(e, "link", "")))

def item_title(e):
    return getattr(e, "title", "New 8-K Filing")

def item_link(e):
    if getattr(e, "link", None):
        return e.link
    try:
        return e.links[0]["href"]
    except Exception:
        return ""

# First run: post only newest so we don't flood
if not last:
    newest = entries[-1]
    msg = f"**New 8-K Filing**\n- {item_title(newest)}\n<{item_link(newest)}>"
    r = requests.post(WEBHOOK, json={"content": msg})
    r.raise_for_status()
    pathlib.Path(CURSOR_FILE).write_text(item_id(newest))
    raise SystemExit(0)

# Subsequent runs: post anything newer than the cursor
new_last = last
posted = 0
for e in entries:
    eid = item_id(e)
    if eid == last:
        continue
    msg = f"**New 8-K Filing**\n- {item_title(e)}\n<{item_link(e)}>"
    r = requests.post(WEBHOOK, json={"content": msg})
    r.raise_for_status()
    posted += 1
    new_last = eid
    time.sleep(1)  # gentle pacing

if posted:
    pathlib.Path(CURSOR_FILE).write_text(new_last)
