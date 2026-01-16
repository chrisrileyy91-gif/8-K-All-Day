import fetch from "node-fetch";
import Parser from "rss-parser";

const parser = new Parser();
const WEBHOOK_URL = process.env.CRYPTO_NEWS_WEBHOOK;

const FEED_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml";
const KEYWORDS = ["ethereum", "defi", "layer 2", "bitcoin", "web3", "crypto regulation"];

function getEasternHour(date = new Date()) {
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour: "2-digit",
    hour12: false,
  });
  return Number(fmt.format(date));
}

async function run() {
  try {
    if (!WEBHOOK_URL) {
      console.error("❌ Missing CRYPTO_NEWS_WEBHOOK environment variable.");
      process.exit(1);
    }

    const hourET = getEasternHour();
    if (hourET >= 19) {
      console.log("ℹ️ Quiet hours: skipping (after 7:00 PM ET).");
      return;
    }

    const feed = await parser.parseURL(FEED_URL);
    const items = (feed.items || []).slice(0, 5);

    const matches = items.filter((it) => {
      const title = (it.title || "").toLowerCase();
      return KEYWORDS.some((k) => title.includes(k));
    });

    if (matches.length === 0) {
      console.log("ℹ️ No keyword matches in latest items. Nothing sent.");
      return;
    }

    const content = matches
      .map((it, i) => `${i + 1}. **${it.title || ""}**\n${it.link || ""}`)
      .join("\n\n");

    const resp = await fetch(WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });

    if (resp.status >= 300) {
      const text = await resp.text().catch(() => "");
      throw new Error(`Discord webhook failed: ${resp.status} ${text}`);
    }

    console.log(`✅ Sent ${matches.length} headline(s).`);
  } catch (err) {
    console.error("❌ Error:", err);
    process.exit(1);
  }
}

run();
