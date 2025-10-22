import fetch from "node-fetch";
import Parser from "rss-parser";
import fs from "fs";

const parser = new Parser();
const WEBHOOK_URL = process.env.TECH_WATCH_WEBHOOK;
const CACHE_FILE = "./scripts/.tech_watch_cache.json";

// --- Feeds ---
const FEEDS = [
  "https://techcrunch.com/feed/",
  "https://www.nasdaq.com/feed/rssoutbound?category=Technology",
  "https://venturebeat.com/category/startups/feed/",
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

// --- Rotating captions ---
const CAPTIONS = [
  "⚙️ **New signal from The Stack's Tech Watch.**",
  "🚀 **Emerging tech momentum detected.**",
  "📡 **Future systems pinged on the radar.**",
  "🧠 **The Stack picked up fresh innovation flow.**",
  "🔍 **The next wave of tech just surfaced.**"
];

async function run() {
  console.log("🧩 Fetching latest Tech & NASDAQ innovation news...");

  if (!WEBHOOK_URL) {
    console.error("❌ Missing TECH_WATCH_WEBHOOK environment variable!");
    return;
  }

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
    for (const feedUrl of FEEDS) {
      console.log(`🔍 Fetching feed: ${feedUrl}`);
      const feed = await parser.parseURL(feedUrl);
      allArticles.push(...feed.items.slice(0, 8));
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

      const caption = CAPTIONS[Math.floor(Math.random() * CAPTIONS.length)];
      const payload = {
        content: `${caption}\n📰 **${title}**\n${link}`
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
      } else {
        console.error(`⚠️ Failed to post ${title}: ${res.statusText}`);
      }
    }

    fs.writeFileSync(CACHE_FILE, JSON.stringify([...postedLinks], null, 2));
    console.log(`🎯 Done! ${newPosts} new Tech Watch updates sent to Discord.`);

  } catch (err) {
    console.error("❌ Error fetching or sending tech news:", err);
  }
}

run();
