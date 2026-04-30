#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(projectRoot, '..', '..');
const bundledPlaywrightCandidates = [
  process.env.AUTOPARK_PLAYWRIGHT_PATH,
  path.join(repoRoot, 'node_modules', 'playwright', 'index.mjs'),
  path.join(process.env.HOME || '', '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'node', 'node_modules', 'playwright', 'index.mjs'),
  path.join(process.env.HOME || '', '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'node', 'node_modules', 'playwright', 'index.js'),
].filter(Boolean);

function parseArgs(argv) {
  const args = {
    endpoint: 'http://127.0.0.1:9222',
    url: 'https://x.com/wallstengine',
    outDir: path.join(projectRoot, 'runtime', 'screenshots', 'cdp-x-test'),
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--endpoint') args.endpoint = argv[++i];
    else if (arg === '--url') args.url = argv[++i];
    else if (arg === '--out-dir') args.outDir = path.resolve(argv[++i]);
    else if (arg === '--help') {
      console.log('Usage: test_chrome_cdp_x.mjs [--endpoint http://127.0.0.1:9222] [--url https://x.com/wallstengine]');
      process.exit(0);
    }
    else throw new Error(`Unknown argument: ${arg}`);
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

function simplify(text) {
  return String(text || '').replace(/\s+/g, ' ').trim();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  fs.mkdirSync(args.outDir, { recursive: true });
  const playwright = await loadPlaywright();
  const chromium = playwright.chromium || playwright.default?.chromium;
  if (!chromium) throw new Error('Playwright chromium is unavailable');
  const browser = await chromium.connectOverCDP(args.endpoint);
  const context = browser.contexts()[0] || await browser.newContext();
  let page = context.pages().find((p) => p.url().includes('x.com')) || context.pages()[0];
  if (!page) page = await context.newPage();

  await page.goto(args.url, { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
  await page.waitForTimeout(8000);

  const data = await page.evaluate(() => {
    const articleNodes = Array.from(document.querySelectorAll('article'));
    const articles = articleNodes.slice(0, 12).map((article) => {
      const text = article.innerText || '';
      const time = article.querySelector('time');
      const link = time ? time.closest('a') : article.querySelector('a[href*="/status/"]');
      const images = Array.from(article.querySelectorAll('img'))
        .map((img) => img.src)
        .filter((src) => src && !src.includes('profile_images') && !src.includes('emoji'));
      return {
        text,
        time: time?.getAttribute('datetime') || time?.textContent || '',
        href: link?.href || '',
        image_count: images.length,
      };
    });
    return {
      title: document.title,
      url: location.href,
      logged_in_hint: !document.body.innerText.includes('로그인') && !document.body.innerText.includes('Sign in'),
      article_count: articleNodes.length,
      articles,
    };
  });

  const screenshotPath = path.join(args.outDir, 'wallstengine-cdp.png');
  await page.screenshot({ path: screenshotPath, fullPage: false }).catch(() => {});
  await browser.close();

  const payload = {
    ok: true,
    endpoint: args.endpoint,
    requested_url: args.url,
    screenshot_path: path.relative(repoRoot, screenshotPath),
    ...data,
    articles: data.articles.map((article) => ({
      ...article,
      text: simplify(article.text).slice(0, 800),
    })),
  };
  console.log(JSON.stringify(payload, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exit(1);
});
