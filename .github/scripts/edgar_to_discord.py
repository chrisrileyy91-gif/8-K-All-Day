import os, pathlib, time, random
import feedparser, requests

# SEC 8-K feed (latest)
FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&count=100&output=atom"

WEBHOOK = os.environ["DISCORD_WEBHOOK"]
CURSOR_FILE = ".cursor"
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "5"))

def send_to_discord(content, max_retries=6):
    """Post to Discord with 429/backoff handling."""
    attempt = 0
    while True:
        resp = requests.post(WEBHOOK, json={"content": content})
        if resp.status_code == 429:
            try:
                retry_after = float(resp.json().get("retry_after", 1.0))
            except Exception:
                retry_after = float(resp.headers.get("Retry-After", "1"))
            time.sleep(retry_after + 0.25)
            attempt += 1
            if attempt >= max_retries:
                resp.raise_for_status()
            continue
        resp.raise_for_status()
        return

def item_id(e):    return str(getattr(e, "id", getattr(e, "link", "")))
def item_title(e): return getattr(e, "title", "New 8-K Filing")
def item_link(e):
    if getattr(e, "link", None): return e.link
    try: return e.links[0]["href"]
    except Exception: return ""

# Load last seen id
last = pathlib.Path(CURSOR_FILE).read_text().strip() if pathlib.Path(CURSOR_FILE).exists() else ""

# Be polite to SEC
fp = feedparser.parse(
    FEED,
    request_headers={"User-Agent": "EDGAR-Bot (youremail@example.com)"}
)
entries = list(reversed(fp.entries))  # oldest -> newest
if not entries:
    raise SystemExit(0)

# First run: only the newest to avoid flooding
if not last:
    newest = entries[-1]
    msg = f"**New 8-K Filing**\n- {item_title(newest)}\n<{item_link(newest)}>"
    send_to_discord(msg)
    pathlib.Path(CURSOR_FILE).write_text(item_id(newest))
    raise SystemExit(0)

# Subsequent runs: post anything newer (with cap + pacing)
new_last = last
posted = 0
for e in entries:
    e
