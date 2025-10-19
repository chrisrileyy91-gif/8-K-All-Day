const fetch = require('node-fetch');
const Parser = require('rss-parser');
const parser = new Parser();
const WEBHOOK_URL = process.env.CRYPTO_NEWS_WEBHOOK;

const FEED_URL = 'https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml';
const KEYWORDS = ['ethereum', 'defi', 'layer 2', 'bitcoin', 'web3', 'crypto regulation'];

async function run() {
  try {
    const feed = await parser.parseURL(FEED_URL);
    const articles = feed.items.slice(0, 5); // limit to avoid spam

    for (const item of articles) {
      const title = item.title || '';
      const link = item.link || '';
      const match = KEYWORDS.some(k => title.toLowerCase().includes(k));
      if (!match) continue;

      const payload = { content: `📰 **${title}**\n${link}` };

      await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      await new Promise(r => setTimeout(r, 2000)); // gentle pacing
    }
  } catch (err) {
    console.error('RSS to Discord error:', err);
  }
}

run();
