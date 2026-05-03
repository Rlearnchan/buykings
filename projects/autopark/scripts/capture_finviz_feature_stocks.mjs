#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(projectRoot, '..', '..');
const bundledPlaywrightCandidates = [
  process.env.AUTOPARK_PLAYWRIGHT_PATH,
  path.join(repoRoot, 'node_modules', 'playwright', 'index.mjs'),
  path.join(repoRoot, 'node_modules', 'playwright', 'index.js'),
  path.join(process.env.HOME || '', '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'node', 'node_modules', 'playwright', 'index.mjs'),
  path.join(process.env.HOME || '', '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'node', 'node_modules', 'playwright', 'index.js'),
].filter(Boolean);
const fallbackChromiumCandidates = [
  process.env.AUTOPARK_CHROME_PATH,
  process.env.AUTOPARK_CHROMIUM,
  path.join(process.env.HOME || '', 'Library', 'Caches', 'ms-playwright', 'chromium_headless_shell-1200', 'chrome-headless-shell-mac-arm64', 'chrome-headless-shell'),
].filter(Boolean);

const defaultTickers = ['ISRG', 'UAL', 'MSFT', 'PANW', 'AMD', 'COIN', 'CSCO', 'MRVL', 'ON', 'COHR'];

function parseArgs(argv) {
  const args = {
    date: new Date().toISOString().slice(0, 10),
    tickers: defaultTickers,
    headed: false,
    useAuthProfile: true,
    browserChannel: null,
    cdpEndpoint: null,
    timeoutMs: 45000,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--date') args.date = argv[++i];
    else if (arg === '--tickers') args.tickers = argv[++i].split(',').map((ticker) => ticker.trim().toUpperCase()).filter(Boolean);
    else if (arg === '--headed') args.headed = true;
    else if (arg === '--no-auth-profile') args.useAuthProfile = false;
    else if (arg === '--browser-channel') args.browserChannel = argv[++i];
    else if (arg === '--cdp-endpoint') args.cdpEndpoint = argv[++i];
    else if (arg === '--timeout-ms') args.timeoutMs = Number.parseInt(argv[++i], 10);
    else if (arg === '--help') {
      console.log('Usage: capture_finviz_feature_stocks.mjs [--date YYYY-MM-DD] [--tickers AAPL,MSFT] [--headed] [--browser-channel chrome]');
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
    for (const candidate of bundledPlaywrightCandidates) {
      if (fs.existsSync(candidate)) return import(pathToFileURL(candidate).href);
    }
    throw new Error('Playwright is unavailable. Run `npm install` in the repo root.');
  }
}

function fallbackChromiumPath() {
  return fallbackChromiumCandidates.find((candidate) => fs.existsSync(candidate)) || null;
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function cleanStaleProfileLocks(profilePath) {
  if (String(process.env.AUTOPARK_PROFILE_LOCK_CLEANUP || '1').toLowerCase() === '0') return;
  for (const name of ['SingletonLock', 'SingletonSocket', 'SingletonCookie']) {
    try {
      fs.rmSync(path.join(profilePath, name), { force: true, recursive: true });
    } catch {
      // Chromium will surface a launch error if the profile is genuinely active.
    }
  }
}

async function createContext(chromium, args) {
  const options = {
    viewport: { width: 1440, height: 1400 },
    deviceScaleFactor: 1,
    locale: 'en-US',
    colorScheme: 'light',
  };
  if (args.cdpEndpoint) {
    const browser = await chromium.connectOverCDP(args.cdpEndpoint);
    const context = browser.contexts()[0] || await browser.newContext(options);
    return { context, browser, shouldCloseContext: false, shouldCloseBrowser: true };
  }
  if (args.useAuthProfile) {
    const profilePath = path.join(projectRoot, 'runtime', 'profiles', 'finviz');
    ensureDir(profilePath);
    const persistentOptions = { ...options, headless: !args.headed };
    if (args.browserChannel) {
      persistentOptions.channel = args.browserChannel;
    } else {
      const executablePath = fallbackChromiumPath();
      if (executablePath) persistentOptions.executablePath = executablePath;
    }
    let context;
    try {
      context = await chromium.launchPersistentContext(profilePath, persistentOptions);
    } catch (error) {
      if (!/profile appears to be in use|process_singleton/i.test(error.message || '')) throw error;
      cleanStaleProfileLocks(profilePath);
      context = await chromium.launchPersistentContext(profilePath, persistentOptions);
    }
    return {
      context,
      browser: null,
      shouldCloseContext: true,
      shouldCloseBrowser: false,
    };
  }

  const launchOptions = { headless: !args.headed };
  if (args.browserChannel) {
    launchOptions.channel = args.browserChannel;
  } else {
    const executablePath = fallbackChromiumPath();
    if (executablePath) launchOptions.executablePath = executablePath;
  }
  const browser = await chromium.launch(launchOptions);
  return {
    context: await browser.newContext(options),
    browser,
    shouldCloseContext: true,
    shouldCloseBrowser: true,
  };
}

async function dismissOverlays(page) {
  for (const label of ['Accept', 'Accept All', 'I Accept', 'Agree', 'Continue', 'Got it']) {
    const button = page.getByRole('button', { name: label, exact: false }).first();
    try {
      if (await button.isVisible({ timeout: 400 })) {
        await button.click({ timeout: 1200 });
        await page.waitForTimeout(400);
      }
    } catch {
      // Best effort. Finviz occasionally changes consent widgets.
    }
  }
  await page.keyboard.press('Escape').catch(() => {});
}

function normalizeSpace(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}

async function forceFinvizLightMode(page) {
  await page.emulateMedia({ colorScheme: 'light' }).catch(() => {});
  await page
    .evaluate(() => {
      for (const key of ['theme', 'finviz_theme', 'fv_theme', 'darkMode', 'color-theme']) {
        try {
          localStorage.setItem(key, key === 'darkMode' ? 'false' : 'light');
          sessionStorage.setItem(key, key === 'darkMode' ? 'false' : 'light');
        } catch {
          // Storage can be blocked by hardened profiles.
        }
      }
      try {
        document.cookie = 'theme=light; path=/; max-age=31536000';
        document.cookie = 'chartsTheme=light; path=/; max-age=31536000';
        document.cookie = 'darkMode=false; path=/; max-age=31536000';
      } catch {
        // Cookie writes can fail without hurting capture.
      }
      document.documentElement.classList.remove('dark', 'theme-dark');
      document.body?.classList.remove('dark', 'theme-dark');
    })
    .catch(() => {});
}

function clampClip(clip, viewport) {
  const x = Math.max(0, Math.round(clip.x));
  const y = Math.max(0, Math.round(clip.y));
  const right = Math.min(viewport.width, Math.round(clip.x + clip.width));
  const bottom = Math.min(viewport.height, Math.round(clip.y + clip.height));
  return {
    x,
    y,
    width: Math.max(1, right - x),
    height: Math.max(1, bottom - y),
  };
}

function isUsefulIssueLine(line) {
  if (!line || line.length < 40 || line.length > 360) return false;
  if (/Upgrade to Finviz Elite|Start Free Trial|Date Action Analyst|Rating Change|Price Target Change/i.test(line)) return false;
  if (/\b(Upgrade|Downgrade|Initiated|Reiterated|Maintained)\b.*(?:→|\$)/i.test(line)) return false;
  if (/^(News|Charts|Insider|Financials|Earnings|Analyst|Options|SEC Filings)$/i.test(line)) return false;
  const hasIssueVerb =
    /\b(announced|reports|reported|discloses|guidance|shares|stock|earnings|revenue|acquisition|upgrade|downgrade|price target|order|contract|partnership|launches|cancels|cancelled|falls|jumps|slump|tumble|plunge)\b/i.test(
      line,
    );
  const hasTimestamp = /\b(?:Today|Yesterday|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Jan|Feb|Mar)\b/i.test(line);
  return hasIssueVerb && (hasTimestamp || /[A-Z]{2,6}/.test(line));
}

async function extractNews(page) {
  return page
    .locator('table.news-table tr')
    .evaluateAll((rows) =>
      rows
        .map((row) => {
          const cells = [...row.querySelectorAll('td')].map((cell) => cell.textContent.replace(/\s+/g, ' ').trim());
          const anchor = row.querySelector('a');
          if (!anchor || cells.length < 2) return null;
          return {
            time: cells[0],
            headline: anchor.textContent.replace(/\s+/g, ' ').trim(),
            url: anchor.href,
          };
        })
        .filter(Boolean)
        .slice(0, 8),
    )
    .catch(() => []);
}

async function extractQuoteSummary(page) {
  const bodyText = await page.locator('body').innerText({ timeout: 3000 }).catch(() => '');
  const lines = bodyText
    .split('\n')
    .map(normalizeSpace)
    .filter(Boolean);
  const summaryLines = lines.filter(isUsefulIssueLine);
  return [...new Set(summaryLines)].slice(0, 3);
}

async function captureDailyChart(page, ticker, screenshotDir) {
  const viewport = page.viewportSize() || { width: 1440, height: 1400 };
  const canvasBoxes = await page.locator('canvas').evaluateAll((items) =>
    items
      .map((el) => {
        const rect = el.getBoundingClientRect();
        return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
      })
      .filter((rect) => rect.width >= 700 && rect.height >= 300 && rect.y < 900)
      .sort((a, b) => b.width * b.height - a.width * a.height),
  ).catch(() => []);
  if (canvasBoxes.length) {
    const rect = canvasBoxes[0];
    const filePath = path.join(screenshotDir, `finviz-${ticker.toLowerCase()}-daily.png`);
    const topPadding = 210;
    const bottomPadding = 36;
    const top = Math.max(0, Math.round(rect.y - topPadding));
    await page.screenshot({
      path: filePath,
      clip: clampClip({
        x: Math.max(0, Math.round(rect.x - 16)),
        y: top,
        width: Math.round(rect.width + 32),
        height: Math.round(rect.height + (rect.y - top) + bottomPadding),
      }, viewport),
    });
    return path.relative(repoRoot, filePath);
  }

  const candidates = [
    `img[src*="quote.ashx"][src*="t=${ticker}"]`,
    `img[src*="chart.ashx"][src*="t=${ticker}"]`,
    'img[src*="chart.ashx"]',
  ];
  for (const selector of candidates) {
    const locator = page.locator(selector).first();
    if (!(await locator.isVisible({ timeout: 2000 }).catch(() => false))) continue;
    const box = await locator.boundingBox().catch(() => null);
    if (!box || box.width < 450 || box.height < 250) continue;
    const filePath = path.join(screenshotDir, `finviz-${ticker.toLowerCase()}-daily.png`);
    await page.screenshot({
      path: filePath,
      clip: clampClip({
        x: box.x - 16,
        y: box.y - 210,
        width: box.width + 32,
        height: box.height + 250,
      }, viewport),
    });
    return path.relative(repoRoot, filePath);
  }

  const filePath = path.join(screenshotDir, `finviz-${ticker.toLowerCase()}-quote.png`);
  await page.screenshot({ path: filePath, fullPage: false });
  return path.relative(repoRoot, filePath);
}

async function captureTicker(context, args, ticker, screenshotDir) {
  const page = await context.newPage();
  await page.setViewportSize({ width: 1440, height: 1400 }).catch(() => {});
  const url = `https://finviz.com/quote.ashx?t=${encodeURIComponent(ticker)}&p=d`;
  try {
    await page.emulateMedia({ colorScheme: 'light' }).catch(() => {});
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: args.timeoutMs });
    await forceFinvizLightMode(page);
    await page.reload({ waitUntil: 'domcontentloaded', timeout: args.timeoutMs }).catch(() => {});
    await dismissOverlays(page);
    await page.waitForLoadState('networkidle', { timeout: 12000 }).catch(() => {});
    await page.waitForTimeout(2000);
    await dismissOverlays(page);

    const title = await page.title();
    const bodyText = await page.locator('body').innerText({ timeout: 3000 }).catch(() => '');
    const blocked = /just a moment|security verification|not a bot/i.test(`${title}\n${bodyText}`);
    if (blocked) {
      return { ticker, url, status: 'blocked', title };
    }

    const screenshotPath = await captureDailyChart(page, ticker, screenshotDir);
    const news = await extractNews(page);
    const quoteSummary = await extractQuoteSummary(page);
    return {
      ticker,
      url,
      status: 'ok',
      title,
      captured_at: new Date().toISOString(),
      screenshot_path: screenshotPath,
      news,
      quote_summary: quoteSummary,
    };
  } catch (error) {
    return { ticker, url, status: 'error', error: error.message };
  } finally {
    await page.close().catch(() => {});
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const { chromium } = await loadPlaywright();
  const session = await createContext(chromium, args);
  const { context, browser } = session;
  const screenshotDir = path.join(projectRoot, 'runtime', 'screenshots', args.date, 'feature-stocks');
  const processedDir = path.join(projectRoot, 'data', 'processed', args.date);
  ensureDir(screenshotDir);
  ensureDir(processedDir);

  const items = [];
  try {
    for (const ticker of args.tickers) {
      const result = await captureTicker(context, args, ticker, screenshotDir);
      items.push(result);
      console.error(JSON.stringify({ ticker, status: result.status, screenshot_path: result.screenshot_path || null }));
    }
  } finally {
    if (session.shouldCloseContext) await context.close().catch(() => {});
    if (session.shouldCloseBrowser && browser) await browser.close().catch(() => {});
  }

  const payload = {
    ok: items.every((item) => item.status === 'ok'),
    target_date: args.date,
    source: 'finviz',
    captured_at: new Date().toISOString(),
    items,
  };
  const output = path.join(processedDir, 'finviz-feature-stocks.json');
  fs.writeFileSync(output, `${JSON.stringify(payload, null, 2)}\n`);
  console.log(JSON.stringify({ ok: payload.ok, output, items }, null, 2));
  if (!payload.ok) process.exitCode = 2;
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exit(1);
});
