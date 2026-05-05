#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(projectRoot, '..', '..');

function parseArgs(argv) {
  const args = {
    date: new Date().toISOString().slice(0, 10),
    limit: Number.parseInt(process.env.AUTOPARK_TRENDING_STOCK_LIMIT || '10', 10),
    headed: false,
    browserChannel: process.env.AUTOPARK_BROWSER_CHANNEL || 'chrome',
    cdpEndpoint: process.env.AUTOPARK_CDP_ENDPOINT || null,
    timeoutMs: 60000,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--date') args.date = argv[++i];
    else if (arg === '--limit') args.limit = Number.parseInt(argv[++i], 10);
    else if (arg === '--headed') args.headed = true;
    else if (arg === '--browser-channel') args.browserChannel = argv[++i];
    else if (arg === '--cdp-endpoint') args.cdpEndpoint = argv[++i];
    else if (arg === '--timeout-ms') args.timeoutMs = Number.parseInt(argv[++i], 10);
    else if (arg === '--help') {
        console.log('Usage: collect_yahoo_trending_stocks.mjs [--date YYYY-MM-DD] [--limit 10] [--cdp-endpoint URL]');
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

async function loadPlaywright() {
  try {
    return await import('playwright');
  } catch {
    const candidates = [
      process.env.AUTOPARK_PLAYWRIGHT_PATH,
      path.join(repoRoot, 'node_modules', 'playwright', 'index.mjs'),
      path.join(repoRoot, 'node_modules', 'playwright', 'index.js'),
      path.join(process.env.HOME || '', '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'node', 'node_modules', 'playwright', 'index.mjs'),
      path.join(process.env.HOME || '', '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'node', 'node_modules', 'playwright', 'index.js'),
    ].filter(Boolean);
    for (const candidate of candidates) {
      if (fs.existsSync(candidate)) return import(pathToFileURL(candidate).href);
    }
    throw new Error('Playwright is unavailable.');
  }
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function normalizeSpace(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function isTicker(value) {
  return /^[A-Z][A-Z0-9.-]{0,6}$/.test(value || '') && !['NEWS', 'ETF', 'USD'].includes(value);
}

async function extractTrendingRows(page, limit) {
  return page.evaluate((rowLimit) => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const isSymbol = (value) => /^[A-Z][A-Z0-9.-]{0,6}$/.test(value || '') && !['NEWS', 'ETF', 'USD'].includes(value);
    const cellText = (row, name) => clean(row.querySelector(`[data-testid-cell="${name}"]`)?.innerText || '');
    const rows = [];
    const seen = new Set();
    const push = (row) => {
      const ticker = clean(row.ticker || row.symbol || '').toUpperCase();
      if (!isSymbol(ticker) || seen.has(ticker)) return;
      seen.add(ticker);
      rows.push({
        rank: rows.length + 1,
        ticker,
        company: clean(row.company || row.name || ''),
        price: clean(row.price || ''),
        change: clean(row.change || ''),
        percent_change: clean(row.percent_change || ''),
        volume: clean(row.volume || ''),
        market_cap: clean(row.market_cap || ''),
        source_url: row.source_url || `https://finance.yahoo.com/quote/${encodeURIComponent(ticker)}`,
      });
    };

    const tableRows = Array.from(document.querySelectorAll('[data-testid="data-table-v2-row"], tr[data-testid-row], table tbody tr'));
    for (const tr of tableRows) {
      const anchor = tr.querySelector('[data-testid="table-cell-ticker"], a[href*="/quote/"]');
      const ticker = clean(
        tr.querySelector('[data-testid-cell="ticker"] .symbol')?.textContent
        || anchor?.textContent
        || ''
      ).toUpperCase();
      const href = anchor ? new URL(anchor.getAttribute('href'), location.href).href : '';
      push({
        ticker,
        company: cellText(tr, 'companyshortname.raw') || clean(anchor?.getAttribute('title') || anchor?.getAttribute('aria-label') || ''),
        price: cellText(tr, 'intradayprice'),
        change: cellText(tr, 'intradaypricechange'),
        percent_change: cellText(tr, 'percentchange'),
        volume: cellText(tr, 'dayvolume'),
        avg_volume_3m: cellText(tr, 'avgdailyvol3m'),
        market_cap: cellText(tr, 'intradaymarketcap'),
        pe_ratio_ttm: cellText(tr, 'peratio.lasttwelvemonths'),
        fifty_two_week_change_percent: cellText(tr, 'fiftytwowkpercentchange'),
        fifty_two_week_range: cellText(tr, 'fiftyTwoWeekRange'),
        source_url: href,
      });
      if (rows.length >= rowLimit) break;
    }

    if (rows.length === 0) {
      for (const anchor of Array.from(document.querySelectorAll('a[href*="/quote/"]'))) {
        const match = anchor.href.match(/\/quote\/([^/?#]+)/);
        if (!match) continue;
        const ticker = decodeURIComponent(match[1]).toUpperCase();
        const container = anchor.closest('li, tr, div') || anchor;
        push({
          ticker,
          company: clean(anchor.textContent).toUpperCase() === ticker ? '' : clean(anchor.textContent),
          source_url: anchor.href,
          summary: clean(container.innerText),
        });
        if (rows.length >= rowLimit) break;
      }
    }
    return rows.slice(0, rowLimit);
  }, limit);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const { chromium } = await loadPlaywright();
  let browser = null;
  let context = null;
  const sourceUrl = 'https://finance.yahoo.com/markets/stocks/trending/';
  try {
    if (args.cdpEndpoint) {
      browser = await chromium.connectOverCDP(args.cdpEndpoint, { timeout: args.timeoutMs });
      context = browser.contexts()[0] || await browser.newContext({ viewport: { width: 1440, height: 1400 } });
    } else {
      const launchOptions = { headless: !args.headed };
      if (args.browserChannel) launchOptions.channel = args.browserChannel;
      browser = await chromium.launch(launchOptions);
      context = await browser.newContext({ viewport: { width: 1440, height: 1400 }, locale: 'en-US' });
    }
    const page = await context.newPage();
    await page.goto(sourceUrl, { waitUntil: 'domcontentloaded', timeout: args.timeoutMs });
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(2500);
    const items = (await extractTrendingRows(page, args.limit)).filter((row) => isTicker(row.ticker));
    const processedDir = path.join(projectRoot, 'data', 'processed', args.date);
    ensureDir(processedDir);
    const payload = {
      ok: items.length > 0,
      target_date: args.date,
      source: 'yahoo_finance_trending_stocks',
      source_url: sourceUrl,
      captured_at: new Date().toISOString(),
      limit: args.limit,
      item_count: items.length,
      items,
    };
    const output = path.join(processedDir, 'yahoo-trending-stocks.json');
    fs.writeFileSync(output, `${JSON.stringify(payload, null, 2)}\n`);
    console.log(JSON.stringify({ ok: payload.ok, output, item_count: items.length, tickers: items.map((row) => row.ticker) }, null, 2));
    if (!payload.ok) process.exitCode = 2;
  } finally {
    if (context && !args.cdpEndpoint) await context.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
  }
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exit(1);
});
