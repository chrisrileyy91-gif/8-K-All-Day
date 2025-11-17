import fetch from "node-fetch";
import Parser from "rss-parser";

const parser = new Parser();
const WEBHOOK_URL = process.env.CRYPTO_NEWS_WEBHOOK;

// RSS feed and keywords
const FEED_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml";
const KEYWORDS = ["ethereum", "defi", "layer 2", "bitcoin", "web3", "crypto regulation"];

async function run() {
  try {
    console.log("🔍 Fetching latest crypto news...");

    const feed = await parser.parseURL(FEED_URL);
    const articles = feed.items.slice(0, 5); // limit to 5 posts max

    for (const item of articles) {
      const title = item.title || "";
      const link = item.link || "";

      const match = KEYWORDS.some(k => title.toLowerCase().includes(k));
      if (!match) continue;

      const message = {
        content: `💠 **The Stack caught something moving!**\n📰 **${title}**\n${link}`
      };

      await fetch(WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(message)
      });

      console.log(`✅ Sent: ${title}`);
    }

    console.log("🎯 Crypto Digest successfully sent to Discord.");
  } catch (error) {
    console.error("❌ Error fetching or sending crypto news:", error);
  }
}

run();
