import fetch from "node-fetch";
import Parser from "rss-parser";
import fs from "fs";

const parser = new Parser({
  timeout: 15000 // ⏱️ 15s timeout per feed — keeps runs snappy
});

const WEBHOOK_URL = process.env.TECH_WATCH_WEBHOOK;
const CACHE_FILE = "./.tech_watch_cache.json";
const MAX_POSTS_PER_RUN = parseInt(process.env.MAX_POSTS_PER_RUN || "3", 10);

// Hard cutoff: do not post after 7:00 PM Eastern
const TZ = "America/New_York";
const CUTOFF_HOUR_ET = 19; // 7 PM

function isAfterCutoffET(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: TZ,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).formatToParts(date);

  const hour = Number(parts.find(p => p.type === "hour")?.value ?? "0");
  return hour >= CUTOFF_HOUR_ET;
}

// --- Feeds ---
const FEEDS = [
  "https://www.reutersagency.com/feed/?best-topics=technology",
  "https://feeds.arstechnica.com/arstechnica/technology-lab",
  "https://techcrunch.com/feed/",
  "https://www.datacenterdynamics.com/en/rss/",
  "https://www.prnewswire.com/rss/technology-latest-news.rss"
];

// --- Keywords ---
const KEYWORDS = [
  "nasdaq",
  "ai",
  "machine learning",
  "infrastructure",
  "cloud",
  "startup",
  "hardware",
  "software",
  "platform",
  "semiconductor",
  "data center",
  "robotics",
  "chip",
  "quantum"
];

async function run() {
  // Quiet hours guardrail (covers workflow mistakes + manual dispatch)
  if (isAfterCutoffET()) {
    console.log("ℹ️ Quiet hours: skipping Tech Watch post (after 7:00 PM ET).");
    return;
  }

  console.log("🧩 Fetching latest Tech & NASDAQ innovation news...");

  if (!WEBHOOK_URL) {
    console.error("❌ Missing TECH_WATCH_WEBHOOK environment variable!");
    return;
  }

  // --- Load cache ---
  let postedLinks = new Set();
  if (fs.existsSync(CACHE_FILE)) {
    try {
      const data = JSON.parse(fs.readFileSync(CACHE_FILE, "utf8"));
      postedLinks = new Set(data);
    } catch {
      console.warn("⚠️ Could not read cache file, starting fresh.");
    }
  }

  try {
    let allArticles = [];

    console.log("⚙️ Fetching feeds in parallel...");
    const feeds = await Promise.allSettled(
      FEEDS.map(async (url) => {
        try {
          const feed = await parser.parseURL(url);
          return feed;
        } catch (err) {
          console.warn(`⚠️ Feed failed (${url}):`, err.message);
          return null;
        }
      })
    );

    for (const result of feeds) {
      if (result.status === "fulfilled" && result.value) {
        const feed = result.value;
        allArticles.push(...feed.items.slice(0, 8));
      }
    }

    let newPosts = 0;

    for (const item of allArticles) {
      const title = item.title || "";
      const link = item.link || "";
      if (!title || !link) continue;
      if (postedLinks.has(link)) continue;

      const match = KEYWORDS.some(k =>
        title.toLowerCase().includes(k.toLowerCase())
      );
      if (!match) continue;

      // Headline-only output: no caption, no preamble
      const payload = {
        content: `**${title}**\n${link}`
      };

      const res = await fetch(WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        postedLinks.add(link);
        newPosts++;
        console.log(`✅ Sent: ${title}`);
        if (newPosts >= MAX_POSTS_PER_RUN) break;
      } else {
        console.error(`⚠️ Failed to post ${title}: ${res.status} ${res.statusText}`);
      }
    }

    // --- Save cache ---
    fs.writeFileSync(CACHE_FILE, JSON.stringify([...postedLinks], null, 2));
    console.log(`🎯 Done! ${newPosts} new Tech Watch updates sent to Discord.`);
  } catch (err) {
    console.error("❌ Error fetching or sending tech news:", err);
  }
}

run();
