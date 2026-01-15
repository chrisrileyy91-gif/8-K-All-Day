import fetch from "node-fetch";
import Parser from "rss-parser";

const parser = new Parser();
const WEBHOOK_URL = process.env.CRYPTO_NEWS_WEBHOOK;

// RSS feed and keywords
const FEED_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml";
const KEYWORDS = ["ethereum", "defi", "layer 2", "bitcoin", "web3", "crypto regulation"];

// Hard cutoff: do not post after 7:00 PM Eastern
const TZ = "America/New_York";
const CUTOFF_HOUR = 19; // 7 PM

function isAfterCutoffET(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: TZ,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(date);

  const hour = Number(parts.find(p => p.type === "hour")?.value ?? "0");
  return hour >= CUTOFF_HOUR;
}

async function postToDiscord(content) {
  if (!WEBHOOK_URL) {
    console.error("❌ Missing CRYPTO_NEWS_WEBHOOK environment variable.");
    return;
  }

  const resp = await fetch(WEBHOOK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });

  if (resp.status >= 300) {
    const text = await resp.text().catch(() => "");
    throw new Error(`Discord webhook failed: ${resp.status} ${text}`);
  }
}

async function run() {
  try {
    // Quiet hours guardrail (covers workflow mistakes + manual dispatch)
    if (isAfterCutoffET()) {
      console.log("ℹ️ Quiet hours: skipping crypto post (after 7:00 PM ET).");
      return;
    }

    console.log("🔍 Fetching latest crypto news...");

    const feed = await parser.parseURL(FEED_URL);
    const articles = (feed.items || []).slice(0, 5); // keep your 5-item cap

    const matched = [];
    for (const item of articles) {
      const title = item.title || "";
      const link = item.link || "";
      const lower = title.toLowerCase();

      const match = KE
