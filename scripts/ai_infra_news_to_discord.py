import os
import time
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Set, Tuple

# Discord webhook
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_AI")

# Rolling cache of posted URLs (tracked + committed by workflow)
CACHE_FILE = os.path.join("scripts", "last_ai_posted.txt")

# Max posts per run (parity with Tech-Watch/Crypto News)
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "3"))

# Prevent posting ancient articles (>7 days)
DAYS_LIMIT = 7

# RSS feeds
FEEDS = [
    # Mainstream AI News
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/artificial-intelligence/index.xml",
    "https://www.wired.com/feed/tag/artificial-intelligence/latest/rss",

    # High-cred tech outlets
    "https://arstechnica.com/tag/artificial-intelligence/feed/",
    "https://www.cnbc.com/id/19854910/device/rss/rss.html",  # AI category
    "https://feeds.feedburner.com/thenextweb",  # TNW tech + AI

    # AI Research, Papers, Breakthroughs
    "https://www.marktechpost.com/feed/",
    "https://ai.googleblog.com/feeds/posts/default?alt=rss",
    "https://openai.com/blog/rss.xml",
    "https://deepmind.google/discover/rss.xml",
    "https://huggingface.co/blog/feed.xml",

    # Enterprise AI, ML Ops
    "https://www.infoq.com/ai-ml/rss/",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
    "https://cloud.google.com/blog/topics/ai-ml-feed.xml",
    "https://azure.microsoft.com/en-us/blog/topics/ai/feed/",

    # Academic + ML Research Digests
    "https://machinelearningmastery.com/blog/feed/",
    "https://paperswithcode.com/feeds/latest",
    "https://aiweekly.co/feed",

    # Ethics, Governance, Policy
    "https://www.brookings.edu/tag/artificial-intelligence/feed/",
    "https://www.nature.com/subjects/artificial-intelligence.rss",
]

# Operational knobs
PER_FEED_ENTRY_LIMIT = 6          # how many entries to consider per feed
CACHE_MAX_LINES = 300             # retain last N posted URLs
REQUEST_TIMEOUT_SECS = 12         # Discord post timeout


def _utcnow() -> datetime:
    return datetime.utcnow()


def read_cache() -> Set[str]:
    """Read rolling cache of posted URLs (one per line)."""
    if not os.path.exists(CACHE_FILE):
        return set()

    seen: Set[str] = set()
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url:
                seen.add(url)
    return seen


def write_cache_append(posted_urls: List[str]) -> None:
    """
    Append newly posted URLs to cache file and truncate to last CACHE_MAX_LINES lines.
    """
    if not posted_urls:
        return

    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    # Append
    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        for url in posted_urls:
            f.write(url.strip() + "\n")

    # Truncate
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if len(lines) > CACHE_MAX_LINES:
            lines = lines[-CACHE_MAX_LINES:]
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception:
        # If truncation fails, do not break the run; worst case cache grows until next success.
        pass


def parse_entry_datetime(entry) -> Optional[datetime]:
    """
    Best-effort publish time extraction (UTC-naive).
    feedparser usually provides published_parsed or updated_parsed.
    """
    dt_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not dt_struct:
        return None
    try:
        return datetime(*dt_struct[:6])
    except Exception:
        return None


def get_candidate_entries() -> List[Tuple[datetime, str, str]]:
    """
    Fetch recent entries across feeds, returning sorted candidates:
    (published_datetime, title, link)
    """
    cutoff = _utcnow() - timedelta(days=DAYS_LIMIT)
    candidates: List[Tuple[datetime, str, str]] = []

    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)

        # Skip completely broken feeds quietly
        if getattr(feed, "bozo", False):
            # bozo_exception exists but we keep runs quiet by design
            continue

        for entry in feed.entries[:PER_FEED_ENTRY_LIMIT]:
            published = parse_entry_datetime(entry)
            if not published or published < cutoff:
                continue

            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()

            if not title or not link:
                continue

            candidates.append((published, title, link))

    # newest first
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates


def post_to_discord(title: str, link: str) -> bool:
    """
    Post a neutral, information-first message. Returns True on success.
    """
    if not WEBHOOK_URL:
        return False

    message = f"**AI-Daily:** {title}\n{link}"
    payload = {"content": message}

    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=REQUEST_TIMEOUT_SECS)
        # Discord webhooks typically return 204 No Content on success
        return 200 <= resp.status_code < 300
    except requests.RequestException:
        return False


def main() -> None:
    if not WEBHOOK_URL:
        # Misconfigured environment; fail silently to avoid noisy posts/commits
        return

    seen = read_cache()
    candidates = get_candidate_entries()
    if not candidates:
        return

    posted: List[str] = []
    posted_count = 0

    for _, title, link in candidates:
        if posted_count >= MAX_POSTS_PER_RUN:
            break

        if link in seen:
            continue

        ok = post_to_discord(title, link)
        if ok:
            posted.append(link)
            seen.add(link)
            posted_count += 1
            # small spacing to reduce webhook burst risk
            time.sleep(1)

    # Update rolling cache only if we actually posted something
    if posted:
        write_cache_append(posted)


if __name__ == "__main__":
    main()
