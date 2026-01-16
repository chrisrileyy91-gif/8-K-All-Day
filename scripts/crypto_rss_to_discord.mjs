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

  const hourPart = parts.find((p) => p.type === "hour");
  const hour = Numbe
