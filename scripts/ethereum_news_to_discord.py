import os
import time
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Set, Tuple

# Reuse existing webhook env var (you chose to keep DISCORD_WEBHOOK_ETH)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_ETH")

# Rolling cache (tracked + committed by workflow)
CACHE_FILE = os.path.join("scripts", "last_quantum_posted.txt")

# Post cap (parity with Tech-Watch / AI-Daily)
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "3"))

# Prevent posting old news (>7 days)
DAYS_LIMIT = 7

# Operational knobs
PER_FEED_ENTRY_LIMIT = 8
DISCORD_TIMEOUT_SECS = 12
CACHE_MAX_LINES = 400
SLEEP_BETWEEN_POSTS_SECS = 1

# Quantum Computing RSS sources (mix of direct + keyword-filtered)
FEEDS = [
    # Research (quantum physics category)
    "http://export.arxiv.org/rss/quant-ph",

    # High-quality journals / publishers (subject feeds)
    "https://www.nature.com/subjects/quantum-information.rss",
    "https://www.nature.com/subjects/quantum-physics.rss",

    # Lab / org blogs (often broader—filtered by keywords below)
    "https://research.ibm.com/blog/rss.xml",
    "https://www.microsoft.com/en-us/research/feed/",

    # General tech outlets (filtered)
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.wired.com/feed/rss",
    "https://www.theverge.com/rss/index.xml",
]

# Allowed quantum keywords (must match at least one in title/summary)
QC_KEYWORDS = [
    "quantum computing",
    "quantum computer",
    "quantum processor",
    "quantum chip",
    "qpu",
    "qubit",
    "logical qubit",
    "error correction",
    "quantum error correction",
    "surface code",
    "fault-tolerant",
    "fault tolerant",
    "ion trap",
    "trapped ion",
    "neutral atom",
    "superconducting qubit",
    "photonic",
    "quantum annealing",
    "quantum networking",
    "quantum network",
    "quantum communication",
    "quantum cryptography",
    "post-quantum",
    "post quantum",
    "quantum advantage",
    "quantum supremacy",
]

# Hard blocked words (exclude obvious off-topic or noisy themes)
BLOCKED = [
    "ethereum", "eth", "bitcoin", "btc", "solana", "xrp", "cardano",
    "binance", "tether",
    "scandal", "controversy", "crime",
]


def _utcnow() -> datetime:
    return datetime.utcnow()


def read_cache() -> Set[str]:
    if not os.path.exists(CACHE_FILE):
        return set()
    seen: Set[str] = set()
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url:
                seen.add(url)
    return seen


def write_cache_append(urls: List[str]) -> None:
    """Append newly posted URLs and truncate cache to last CACHE_MAX_LINES."""
    if not urls:
        return

    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        for u in urls:
            f.write(u.strip() + "\n")

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if len(lines) > CACHE_MAX_LINES:
            lines = lines[-CACHE_MAX_LINES:]
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception:
        # Do not break the run if truncation fails
        pass


def parse_entry_datetime(entry) -> Optional[datetime]:
    dt_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not dt_struct:
        return None
    try:
        return datetime(*dt_struct[:6])
    except Exception:
        return None


def is_quantum_article(title: str, summary: str, feed_url: str) -> bool:
    """Return True if article is quantum-computing-related and not junk."""
    blob = f"{title}\n{summary}".lower().strip()

    # Hard block first
    for bad in BLOCKED:
        if bad in blob:
            return False

    # arXiv quant-ph is inherently quantum, but can be broad.
    # We still allow it without keyword gating to keep research flowing.
    if "export.arxiv.org/rss/quant-ph" in feed_url:
        return True

    # Require at least one quantum keyword for general feeds
    return any(k in blob for k in QC_KEYWORDS)


def get_candidates() -> List[Tuple[datetime, str, str]]:
    """Fetch quantum-focused articles across feeds; return newest-first candidates."""
    cutoff = _utcnow() - timedelta(days=DAYS_LIMIT)
    candidates: List[Tuple[datetime, str, str]] = []

    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)

        # Skip broken feeds quietly
        if getattr(feed, "bozo", False):
            continue

        for entry in feed.entries[:PER_FEED_ENTRY_LIMIT]:
            published = parse_entry_datetime(entry)
            if not published or published < cutoff:
                continue

            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()
            summary = (getattr(entry, "summary", "") or getattr(entry, "description", "") or "").strip()

            if not title or not link:
                continue

            if not is_quantum_article(title, summary, feed_url):
                continue

            candidates.append((published, title, link))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates


def post_to_discord(title: str, link: str) -> bool:
    """Neutral, non-branded post format."""
    if not WEBHOOK_URL:
        return False

    content = f"**Quantum-Daily:** {title}\n{link}"
    try:
        resp = requests.post(
            WEBHOOK_URL,
            json={"content": content},
            timeout=DISCORD_TIMEOUT_SECS,
        )
        return 200 <= resp.status_code < 300
    except requests.RequestException:
        return False


def main() -> None:
    if not WEBHOOK_URL:
        return

    seen = read_cache()
    candidates = get_candidates()
    if not candidates:
        return

    posted_urls: List[str] = []
    posted_count = 0

    for _, title, link in candidates:
        if posted_count >= MAX_POSTS_PER_RUN:
            break
        if link in seen:
            continue

        if post_to_discord(title, link):
            posted_urls.append(link)
            seen.add(link)
            posted_count += 1
            time.sleep(SLEEP_BETWEEN_POSTS_SECS)

    if posted_urls:
        write_cache_append(posted_urls)


if __name__ == "__main__":
    main()
