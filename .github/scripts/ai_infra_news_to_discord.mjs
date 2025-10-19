import fetch from "node-fetch";
import Parser from "rss-parser";

const parser = new Parser();
const WEBHOOK_URL = process.env.AI_INFRA_NEWS_WEBHOOK;

// --- Feeds ---
const FEEDS = [
  "https://www.techtarget.com/searchdatacenter/rss",
  "https://www.nvidia.com/en-us/about-nvidia/rss/"
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

  try {
    let allArticles = [];

    for (const feedUrl of FEEDS) {
      const feed = await parser.parseURL(feedUrl);
      const articles = feed.items.slice(0, 6);
      allArticles.push(...articles);
    }

    for (const item of allArticles) {
      const title = item.title || "";
      const link = item.link || "";

      const match = KEYWORDS.some(k =>
        title.toLowerCase().includes(k.toLowerCase())
      );
      if (!match) continue;

      const caption =
        CAPTIONS[Math.floor(Math.random() * CAPTIONS.length)];

      const payload = {
        content: `${caption}\n📰 **${title}**\n${link}`
      };

      await fetch(WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      console.log(`✅ Sent: ${title}`);
    }

    console.log("🎯 AI Infrastructure Digest successfully sent to Discord.");
  } catch (error) {
    console.error("❌ Error fetching or sending AI news:", error);
  }
}

run();
