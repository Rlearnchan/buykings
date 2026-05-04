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
  path.join(process.env.HOME || process.env.USERPROFILE || '', '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'node', 'node_modules', 'playwright', 'index.mjs'),
  path.join(process.env.HOME || process.env.USERPROFILE || '', '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'node', 'node_modules', 'playwright', 'index.js'),
].filter(Boolean);

function parseArgs(argv) {
  const args = {
    url: '',
    profile: 'syukafriends',
    limit: 80,
    timeoutMs: 45000,
    headed: false,
    browserChannel: 'chrome',
    profileDirectory: process.env.AUTOPARK_SYUKAFRIENDS_PROFILE_DIRECTORY || '',
    bootstrap: false,
    bootstrapWaitMs: 120000,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--url') args.url = argv[++i];
    else if (arg === '--profile') args.profile = argv[++i];
    else if (arg === '--limit') args.limit = Number.parseInt(argv[++i], 10);
    else if (arg === '--timeout-ms') args.timeoutMs = Number.parseInt(argv[++i], 10);
    else if (arg === '--headed') args.headed = true;
    else if (arg === '--browser-channel') args.browserChannel = argv[++i];
    else if (arg === '--profile-directory') args.profileDirectory = argv[++i];
    else if (arg === '--bootstrap') {
      args.bootstrap = true;
      args.headed = true;
    } else if (arg === '--bootstrap-wait-ms') args.bootstrapWaitMs = Number.parseInt(argv[++i], 10);
    else throw new Error(`Unknown argument: ${arg}`);
  }
  if (!args.url) throw new Error('Missing --url');
  return args;
}

async function loadPlaywright() {
  try {
    return await import('playwright');
  } catch {
    for (const candidate of bundledPlaywrightCandidates) {
      if (fs.existsSync(candidate)) return import(pathToFileURL(candidate).href);
    }
    throw new Error('Playwright is unavailable.');
  }
}

function authProfilePath(profile) {
  if (profile === 'syukafriends' && process.env.AUTOPARK_SYUKAFRIENDS_PROFILE_PATH) {
    return process.env.AUTOPARK_SYUKAFRIENDS_PROFILE_PATH;
  }
  if (process.env.AUTOPARK_AUTH_PROFILE_ROOT && !path.isAbsolute(profile)) {
    return path.join(process.env.AUTOPARK_AUTH_PROFILE_ROOT, profile);
  }
  return path.isAbsolute(profile) ? profile : path.join(projectRoot, 'runtime', 'profiles', profile);
}

function normalizeSpace(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const { chromium } = await loadPlaywright();
  const profilePath = authProfilePath(args.profile);
  fs.mkdirSync(profilePath, { recursive: true });
  const context = await chromium.launchPersistentContext(profilePath, {
    headless: !args.headed,
    channel: args.browserChannel || undefined,
    args: args.profileDirectory ? [`--profile-directory=${args.profileDirectory}`] : [],
    viewport: { width: 1440, height: 1100 },
    locale: 'en-US',
    colorScheme: 'light',
  });
  const page = await context.newPage();
  const startedAt = new Date().toISOString();
  try {
    await page.goto(args.url, { waitUntil: 'domcontentloaded', timeout: args.timeoutMs });
    await page.waitForTimeout(2500);
    if (args.bootstrap) {
      console.error(`Bootstrap mode: use the opened browser if login or consent is needed. Waiting ${args.bootstrapWaitMs}ms before extraction.`);
      await page.waitForTimeout(args.bootstrapWaitMs);
    }
    const result = await page.evaluate((limit) => {
      const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
      const metaDescription = clean(document.querySelector('meta[name="description"]')?.getAttribute('content') || '');
      const seen = new Set();
      const items = [];
      for (const anchor of Array.from(document.querySelectorAll('a[href]'))) {
        const title = clean(anchor.innerText || anchor.getAttribute('aria-label') || anchor.getAttribute('title') || '');
        if (!title || title.length < 12) continue;
        let href = '';
        try {
          href = new URL(anchor.getAttribute('href'), location.href).toString();
        } catch {
          continue;
        }
        const key = `${title} ${href}`;
        if (seen.has(key)) continue;
        seen.add(key);
        items.push({ title, url: href, summary: '' });
        if (items.length >= limit) break;
      }
      return {
        title: clean(document.title),
        final_url: location.href,
        meta_description: metaDescription,
        items,
      };
    }, args.limit);
    console.log(JSON.stringify({
      ok: true,
      source_url: args.url,
      profile: args.profile,
      profile_path: path.relative(repoRoot, profilePath),
      captured_at: new Date().toISOString(),
      started_at: startedAt,
      title: normalizeSpace(result.title),
      final_url: result.final_url,
      meta_description: normalizeSpace(result.meta_description),
      items: result.items,
      policy: {
        sanitized_only: true,
        raw_html_excluded: true,
        full_article_body_excluded: true,
      },
    }, null, 2));
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  console.log(JSON.stringify({ ok: false, error: String(error?.message || error) }, null, 2));
  process.exit(1);
});
