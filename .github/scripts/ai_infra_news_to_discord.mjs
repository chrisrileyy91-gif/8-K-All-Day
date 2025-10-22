import fetch from "node-fetch";
import Parser from "rss-parser";
import fs from "fs";

const parser = new Parser();
const WEBHOOK_URL = process.env.AI_INFRA_NEWS_WEBHOOK;
const CACHE_FILE = "./scripts/.ai_infra_cache.json";

// --- Feeds ---
const FEEDS = [
  "https://venturebeat.com/category/ai/feed/",
  "https://techcrunch.com/category/artificial-intelligence/feed/",
  "https://www.datacenterdynamics.com/en/rss/",
  "https://www.nvidia.com/en-us/about-nvidia/rss/",
  "https://www.techtarget.com/searchdatacenter/rss"
];

// --- Keywords ---
const KEYWORDS = [
  "ai",
  "artificial intelligence",
  "data center",
  "infrastructure",
  "cloud",
  "hyperscaler",
  "nvidia",
  "amd",
  "intel",
  "chips",
  "semiconductor",
  "training",
  "inference"
];

// --- Rotating captions ---
const CAPTIONS = [
  "📡 **Signal from the AI grid—The Stack picked this up.**",
  "💡 **The Stack logged a movement in the AI circuit.**",
  "⚙️ **Infra pulse detected—The Stack noticed activity.**",
  "🚀 **The Stack caught new momentum in AI.**",
  "🧠 **The Stack spotted something building across the AI network.**"
];

async function run() {
  console.log("🧠 Fetching latest AI & Infrastructure news...");

  if (!WEBHOOK_URL) {
    console.error("❌ Missing AI_INFRA_NEWS_WEBHOOK environment variable!");
    return;
  }

  // Load cache
  let postedLinks = new Set();
  if (fs.existsSync(CACHE_FILE)) {
    try {
      const data = JSON.parse(fs.readFileSync(CACHE_FILE, "utf8"));
      postedLinks = new Set(data);
    } catch (err) {
      console.warn("⚠️ Could not read cache file, starting fresh.");
    }
  }

  try {
    let allArticles = [];

    for (const feedUrl of FEEDS) {
      console.log(`🔍 Fetching feed: ${feedUrl}`);
      const feed = await parser.parseURL(feedUrl);
      const articles = feed.items.slice(0, 8);
      allArticles.push(...articles);
    }

    let newPosts = 0;

    for (const item of allArticles) {
      const title = item.title || "";
      const link = item.link || "";

      if (!title || !link) continue;
      if (postedLinks.has(link)) continue; // skip duplicates

      const match = KEYWORDS.some(k =>
        title.toLowerCase().includes(k.toLowerCase())
      );
      if (!match) continue;

      console.log("✅ New Match:", title);

      const caption =
        CAPTIONS[Math.floor(Math.random() * CAPTIONS.length)];

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
        console.log(`🚀 Posted to Discord: ${title}`);
      } else {
        console.error(`⚠️ Failed to post ${title}: ${res.statusText}`);
      }
    }

    // Save cache
    fs.writeFileSync(CACHE_FILE, JSON.stringify([...postedLinks], null, 2));
    console.log(`🎯 Done! ${newPosts} new articles sent to Discord.`);

  } catch (error) {
    console.error("❌ Error fetching or sending AI news:", error);
  }
}

run();
