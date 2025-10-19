const fetch = require('node-fetch');
const Parser = require('rss-parser');
const parser = new Parser();

const WEBHOOK_URL = process.env.CRYPTO_NEWS_WEBHOOK;

// Using Coindesk for consistent crypto coverage
const FEED_URL = 'https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml';
const KEYWORDS = ['ethereum', 'defi', 'layer 2', 'bitcoin', 'web3', 'crypto regulation'];

async function run() {
  try {
    const feed = await parser.parseURL(FEED_URL);
    const articles = feed.items.slice(0, 5); // limit to top 5 to avoid spam

    for (const item of articles) {
      const title = item.title || '';
      const link = item.link || '';
      const match = KEYWORDS.some(k => title.toLowerCase().includes(k));

      if (!match) continue;

      const payload = { 
        content: `💠 **New Digest on Crypto — Stack Choice!**\n📰 **${title}**\n${link}` 
      };

      await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      console.log(`Sent: ${title}`);
    }

    console.log('✅ Crypto Digest sent to Discord successfully.');
  } catch (error) {
    console.error('❌ Error fetching or sending crypto news:', error);
  }
}

run();
