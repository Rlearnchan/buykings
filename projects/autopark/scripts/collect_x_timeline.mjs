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
const defaultSourceIds = [
  'x-kobeissiletter',
  'x-investinq',
  'x-lizannsonders',
  'x-bespokeinvest',
  'x-nicktimiraos',
];
const sourceProfiles = {
  core: defaultSourceIds,
  market: ['x-kobeissiletter', 'x-investinq', 'x-bespokeinvest', 'x-lizannsonders', 'x-charliebilello'],
  headline_news: ['x-reuters', 'x-bloomberg', 'x-cnbc', 'x-wsj', 'x-ft', 'x-marketwatch'],
  analysis_fixed: [
    'x-kobeissiletter',
    'x-wallstengine',
    'x-lizannsonders',
    'x-charliebilello',
    'x-nicktimiraos',
    'x-zerohedge',
    'x-theeconomist',
  ],
  market_radar: [
    'x-kobeissiletter',
    'x-wallstengine',
    'x-charliebilello',
    'x-lizannsonders',
    'x-nicktimiraos',
    'x-zerohedge',
    'x-theeconomist',
    'x-reuters',
    'x-bloomberg',
    'x-cnbc',
    'x-wsj',
    'x-ft',
    'x-marketwatch',
  ],
  macro: ['x-lizannsonders', 'x-bespokeinvest', 'x-nicktimiraos', 'x-charliebilello', 'x-kevrgordon'],
  earnings: ['fixed-earnings-calendar', 'x-investinq', 'x-kobeissiletter', 'x-stocktwits', 'x-unusualwhales'],
  side_dish: ['x-reuters', 'x-bloomberg', 'x-wsj', 'x-ft', 'x-ap', 'x-cnbc', 'x-theeconomist', 'x-deitaone'],
  expanded: [
    'x-kobeissiletter',
    'x-investinq',
    'x-lizannsonders',
    'x-bespokeinvest',
    'x-nicktimiraos',
    'x-charliebilello',
    'x-kevrgordon',
    'x-zerohedge',
    'x-unusualwhales',
    'x-deitaone',
    'x-reuters',
    'x-bloomberg',
    'x-wsj',
    'x-ft',
    'x-ap',
    'x-cnbc',
  ],
};

function parseArgs(argv) {
  const args = {
    config: path.join(projectRoot, 'config', 'today_misc_sources.json'),
    date: new Date().toISOString().slice(0, 10),
    sourceIds: [],
    sourceProfile: 'core',
    runName: 'x-timeline',
    headed: false,
    browserChannel: null,
    cdpEndpoint: null,
    profile: path.join(projectRoot, 'runtime', 'profiles', 'x'),
    bootstrap: false,
    bootstrapWaitMs: 120000,
    maxPosts: 8,
    minTextLength: 40,
    scrolls: 2,
    lookbackHours: 24,
    timeoutMs: 45000,
    downloadImages: true,
    searchFallback: false,
    dryRun: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--config') args.config = argv[++i];
    else if (arg === '--date') args.date = argv[++i];
    else if (arg === '--source') args.sourceIds.push(argv[++i]);
    else if (arg === '--source-profile') args.sourceProfile = argv[++i];
    else if (arg === '--run-name') args.runName = argv[++i];
    else if (arg === '--headed') args.headed = true;
    else if (arg === '--browser-channel') args.browserChannel = argv[++i];
    else if (arg === '--cdp-endpoint') args.cdpEndpoint = argv[++i];
    else if (arg === '--profile') args.profile = path.resolve(argv[++i]);
    else if (arg === '--bootstrap') {
      args.bootstrap = true;
      args.headed = true;
    }
    else if (arg === '--bootstrap-wait-ms') args.bootstrapWaitMs = Number.parseInt(argv[++i], 10);
    else if (arg === '--max-posts') args.maxPosts = Number.parseInt(argv[++i], 10);
    else if (arg === '--min-text-length') args.minTextLength = Number.parseInt(argv[++i], 10);
    else if (arg === '--scrolls') args.scrolls = Number.parseInt(argv[++i], 10);
    else if (arg === '--lookback-hours') args.lookbackHours = Number.parseInt(argv[++i], 10);
    else if (arg === '--timeout-ms') args.timeoutMs = Number.parseInt(argv[++i], 10);
    else if (arg === '--no-download-images') args.downloadImages = false;
    else if (arg === '--search-fallback') args.searchFallback = true;
    else if (arg === '--dry-run') args.dryRun = true;
    else if (arg === '--help') {
      console.log('Usage: collect_x_timeline.mjs [--source-profile core|headline_news|analysis_fixed|market_radar|macro|earnings|side_dish|expanded] [--source x-kobeissiletter] [--headed] [--browser-channel chrome] [--cdp-endpoint http://127.0.0.1:9222]');
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

function loadSources(configPath, sourceIds, sourceProfile) {
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const profileIds = sourceProfiles[sourceProfile];
  if (!sourceIds.length && !profileIds) {
    throw new Error(`Unknown source profile: ${sourceProfile}`);
  }
  const wanted = new Set(sourceIds.length ? sourceIds : profileIds);
  const sources = (config.sources || []).filter((source) => wanted.has(source.id));
  const found = new Set(sources.map((source) => source.id));
  const missing = [...wanted].filter((id) => !found.has(id));
  if (missing.length) {
    console.error(JSON.stringify({ warning: 'missing_x_sources', source_profile: sourceProfile, missing }));
  }
  return sources;
}

function safeName(value) {
  return value.replace(/[^a-zA-Z0-9_-]+/g, '-').replace(/^-+|-+$/g, '') || 'x-timeline';
}

function sourceHandle(source) {
  const urlMatch = (source.url || '').match(/(?:x|twitter)\.com\/([^/?#]+)/i);
  const nameMatch = (source.name || '').match(/@([a-zA-Z0-9_]+)/);
  const handle = (urlMatch?.[1] || nameMatch?.[1] || '').replace(/^@/, '');
  if (!handle || ['search', 'i', 'home', 'explore'].includes(handle.toLowerCase())) return '';
  return handle;
}

function searchUrlForSource(source) {
  const handle = sourceHandle(source);
  if (!handle) return '';
  const query = encodeURIComponent(`from:${handle}`);
  return `https://x.com/search?q=${query}&src=typed_query&f=live`;
}

function postDateFromRelative(relativeText, capturedAt) {
  const lowered = (relativeText || '').toLowerCase();
  if (!lowered) return null;
  if (/\bnow\b|just now|방금/.test(lowered)) return capturedAt;
  let match = lowered.match(/\b(\d+)\s*(m|min|mins|minute|minutes)\b|(\d+)\s*분/);
  if (match) {
    const minutes = Number.parseInt(match[1] || match[4], 10);
    return new Date(capturedAt.getTime() - minutes * 60 * 1000);
  }
  match = lowered.match(/\b(\d+)\s*(h|hr|hrs|hour|hours)\b|(\d+)\s*시간/);
  if (match) {
    const hours = Number.parseInt(match[1] || match[4], 10);
    return new Date(capturedAt.getTime() - hours * 60 * 60 * 1000);
  }
  match = lowered.match(/\b(\d+)\s*(d|day|days)\b|(\d+)\s*일/);
  if (match) {
    const days = Number.parseInt(match[1] || match[4], 10);
    return new Date(capturedAt.getTime() - days * 24 * 60 * 60 * 1000);
  }
  return null;
}

function isRecent(post, capturedAt, lookbackHours) {
  const created = post.created_at ? new Date(post.created_at) : postDateFromRelative(post.relative_time, capturedAt);
  if (!created || Number.isNaN(created.getTime())) return false;
  post.created_at_inferred = created.toISOString();
  return capturedAt.getTime() - created.getTime() <= lookbackHours * 60 * 60 * 1000;
}

function cleanPostText(text) {
  return (text || '')
    .replace(/\n+/g, '\n')
    .replace(/\s+\n/g, '\n')
    .replace(/\n\s+/g, '\n')
    .trim();
}

function imageExtension(url, contentType) {
  if (/png/i.test(contentType || '')) return '.png';
  if (/webp/i.test(contentType || '')) return '.webp';
  if (/gif/i.test(contentType || '')) return '.gif';
  if (/jpe?g/i.test(contentType || '')) return '.jpg';
  const formatMatch = (url || '').match(/[?&]format=([a-z0-9]+)/i);
  if (formatMatch) return `.${formatMatch[1].toLowerCase().replace('jpeg', 'jpg')}`;
  return '.jpg';
}

async function downloadPostImages(context, posts, assetsDir, runName) {
  ensureDir(assetsDir);
  for (const post of posts) {
    const statusId = (post.url || '').match(/\/status\/(\d+)/)?.[1] || safeName(post.source_id || runName);
    const refs = [];
    for (let index = 0; index < (post.images || []).length; index += 1) {
      const image = post.images[index];
      if (!image.src) continue;
      try {
        const response = await context.request.get(image.src, { timeout: 20000 });
        if (!response.ok()) {
          refs.push({ ...image, download_status: 'error', error: `HTTP ${response.status()}` });
          continue;
        }
        const contentType = response.headers()['content-type'] || '';
        const extension = imageExtension(image.src, contentType);
        const filename = `${safeName(post.source_id || runName)}-${statusId}-${index + 1}${extension}`;
        const filePath = path.join(assetsDir, filename);
        fs.writeFileSync(filePath, await response.body());
        refs.push({
          ...image,
          download_status: 'ok',
          local_path: path.relative(repoRoot, filePath),
          content_type: contentType,
        });
      } catch (error) {
        refs.push({ ...image, download_status: 'error', error: error.message });
      }
    }
    post.image_refs = refs;
  }
}

async function extractPosts(page, source, capturedAt, lookbackHours, maxPosts, minTextLength = 40) {
  const posts = await page.locator('article').evaluateAll((articles) =>
    articles.map((article) => {
      const statusLink = [...article.querySelectorAll('a[href*="/status/"]')]
        .map((anchor) => anchor.href)
        .find((href) => /\/status\/\d+/.test(href));
      const timeEl = article.querySelector('time');
      const images = [...article.querySelectorAll('img')]
        .map((img) => ({ alt: img.alt || '', src: img.currentSrc || img.src || '' }))
        .filter((img) => img.src && !/profile_images|emoji|abs.twimg.com\/hashflags/.test(img.src));
      const tweetText = [...article.querySelectorAll('[data-testid="tweetText"]')]
        .map((el) => el.innerText || el.textContent || '')
        .join('\n');
      return {
        url: statusLink || null,
        created_at: timeEl?.getAttribute('datetime') || null,
        relative_time: timeEl?.textContent || null,
        text: tweetText || article.innerText || '',
        raw_text: article.innerText || '',
        image_count: images.length,
        images: images.slice(0, 4),
      };
    }),
  );

  const seen = new Set();
  const cleaned = [];
  for (const post of posts) {
    const key = post.url || post.text.slice(0, 160);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    const text = cleanPostText(post.text);
    if (!text || text.length < minTextLength) continue;
    if (/메인에 올림|pinned|가입하기|로그인/.test(text)) continue;
    const normalized = {
      ...post,
      source_id: source.id,
      source_name: source.name || source.id,
      account_url: source.url,
      text,
      captured_at: capturedAt.toISOString(),
    };
    if (!isRecent(normalized, capturedAt, lookbackHours)) continue;
    cleaned.push(normalized);
    if (cleaned.length >= maxPosts) break;
  }
  return cleaned;
}

async function collectPostsFromUrl(page, source, url, args, capturedAt) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: args.timeoutMs });
  await page.waitForTimeout(4500);
  const collected = [];
  const seen = new Set();
  const addPosts = async () => {
    const posts = await extractPosts(page, source, capturedAt, args.lookbackHours, args.maxPosts, args.minTextLength);
    for (const post of posts) {
      const key = post.url || post.text.slice(0, 160);
      if (!key || seen.has(key)) continue;
      seen.add(key);
      collected.push(post);
      if (collected.length >= args.maxPosts) return;
    }
  };
  await addPosts();
  for (let i = 0; i < args.scrolls; i += 1) {
    if (collected.length >= args.maxPosts) break;
    await page.mouse.wheel(0, 900);
    await page.waitForTimeout(1200);
    await addPosts();
  }
  return collected.slice(0, args.maxPosts);
}

async function inspectVisibleArticles(page) {
  return page
    .locator('article')
    .evaluateAll((articles) =>
      articles.slice(0, 8).map((article) => {
        const statusLink = [...article.querySelectorAll('a[href*="/status/"]')]
          .map((anchor) => anchor.href)
          .find((href) => /\/status\/\d+/.test(href));
        const timeEl = article.querySelector('time');
        const tweetText = [...article.querySelectorAll('[data-testid="tweetText"]')]
          .map((el) => el.innerText || el.textContent || '')
          .join('\n');
        return {
          url: statusLink || null,
          created_at: timeEl?.getAttribute('datetime') || null,
          relative_time: timeEl?.textContent || null,
          text_length: (tweetText || article.innerText || '').trim().length,
          text_preview: (tweetText || article.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 260),
        };
      }),
    )
    .catch((error) => [{ error: error.message }]);
}

function renderReview(postsBySource, targetDate) {
  const lines = [
    `# X 타임라인 후보 ${targetDate}`,
    '',
    '브라우저 기반 1차 후보입니다. 단일 X 게시물은 교차 확인 전까지 확정 소재가 아닙니다.',
    '',
  ];
  let index = 1;
  for (const result of postsBySource) {
    if (!result.posts.length) continue;
    for (const post of result.posts) {
      const preview = post.text.split('\n').slice(0, 5).join(' ');
      lines.push(`## 후보 ${index}. ${result.name}`);
      lines.push('');
      lines.push(`- URL: ${post.url || result.url}`);
      lines.push(`- 시간: ${post.created_at || post.relative_time || post.created_at_inferred || '-'}`);
      lines.push(`- 이미지: ${post.image_count}`);
      lines.push(`- 내용: ${preview.slice(0, 500)}`);
      lines.push('');
      index += 1;
    }
  }
  if (index === 1) lines.push('- 후보 없음');
  return `${lines.join('\n')}\n`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const sources = loadSources(path.resolve(repoRoot, args.config), args.sourceIds, args.sourceProfile);
  const { chromium } = await loadPlaywright();
  let browser = null;
  let context = null;
  let shouldCloseContext = true;
  if (args.cdpEndpoint) {
    browser = await chromium.connectOverCDP(args.cdpEndpoint);
    context = browser.contexts()[0] || await browser.newContext({ viewport: { width: 1280, height: 1000 }, locale: 'ko-KR' });
    shouldCloseContext = false;
  } else {
    ensureDir(args.profile);
    const contextOptions = {
      headless: !args.headed,
      viewport: { width: 1280, height: 1000 },
      locale: 'ko-KR',
    };
    if (args.browserChannel) {
      contextOptions.channel = args.browserChannel;
    } else {
      const executablePath = fallbackChromiumPath();
      if (executablePath) contextOptions.executablePath = executablePath;
    }
    context = await chromium.launchPersistentContext(args.profile, contextOptions);
  }
  const capturedAt = new Date();
  const runName = safeName(args.runName);
  const rawDir = path.join(projectRoot, 'data', 'raw', args.date, runName);
  const processedDir = path.join(projectRoot, 'data', 'processed', args.date);
  const notionDir = path.join(projectRoot, 'runtime', 'notion', args.date);
  const assetsDir = path.join(projectRoot, 'runtime', 'assets', args.date, runName);
  const results = [];

  try {
    if (args.bootstrap) {
      const bootstrapPage = await context.newPage();
      const bootstrapUrl = sources[0]?.url || 'https://x.com/home';
      await bootstrapPage.goto(bootstrapUrl, { waitUntil: 'domcontentloaded', timeout: args.timeoutMs }).catch(() => {});
      console.error(
        JSON.stringify(
          {
            ok: true,
            mode: 'bootstrap',
            profile_path: path.relative(repoRoot, args.profile),
            url: bootstrapUrl,
            wait_ms: args.bootstrapWaitMs,
            message: 'Complete X login/profile checks in the browser window. Collection will continue after the wait.',
          },
          null,
          2,
        ),
      );
      await bootstrapPage.waitForTimeout(args.bootstrapWaitMs);
      await bootstrapPage.close().catch(() => {});
    }
    for (const source of sources) {
      const started = Date.now();
      const page = await context.newPage();
      try {
        const fallbackEnabled = args.searchFallback || source.id === 'x-wallstengine';
        let collection_url = source.url;
        let collection_method = 'profile';
        let posts = await collectPostsFromUrl(page, source, source.url, args, capturedAt);
        if (!posts.length && fallbackEnabled) {
          const searchUrl = searchUrlForSource(source);
          if (searchUrl) {
            collection_url = searchUrl;
            collection_method = 'search_fallback';
            posts = await collectPostsFromUrl(page, source, searchUrl, args, capturedAt);
          }
        }
        const zero_debug = posts.length ? undefined : await inspectVisibleArticles(page);
        if (args.downloadImages && !args.dryRun) {
          await downloadPostImages(context, posts, assetsDir, runName);
        }
        results.push({
          source_id: source.id,
          name: source.name || source.id,
          url: source.url,
          collection_url,
          collection_method,
          status: 'ok',
          zero_debug,
          elapsed_seconds: Number(((Date.now() - started) / 1000).toFixed(2)),
          posts,
        });
      } catch (error) {
        results.push({
          source_id: source.id,
          name: source.name || source.id,
          url: source.url,
          status: 'error',
          error: error.message,
          elapsed_seconds: Number(((Date.now() - started) / 1000).toFixed(2)),
          posts: [],
        });
      } finally {
        await page.close().catch(() => {});
      }
    }
  } finally {
    if (shouldCloseContext) await context.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
  }

  const payload = {
    ok: true,
    target_date: args.date,
    run_name: runName,
    source_profile: args.sourceIds.length ? 'custom' : args.sourceProfile,
    captured_at: capturedAt.toISOString(),
    browser_mode: args.cdpEndpoint ? 'cdp' : 'persistent_context',
    cdp_endpoint: args.cdpEndpoint || undefined,
    profile_path: args.cdpEndpoint ? undefined : path.relative(repoRoot, args.profile),
    lookback_hours: args.lookbackHours,
    assets_path: args.downloadImages ? path.relative(repoRoot, assetsDir) : null,
    source_results: results.map((result) => ({
      source_id: result.source_id,
      name: result.name,
      url: result.url,
      collection_url: result.collection_url,
      collection_method: result.collection_method,
      status: result.status,
      error: result.error || undefined,
      post_count: result.posts.length,
      zero_debug: result.zero_debug || undefined,
      elapsed_seconds: result.elapsed_seconds,
    })),
    posts: results.flatMap((result) => result.posts),
  };

  if (!args.dryRun) {
    ensureDir(rawDir);
    ensureDir(processedDir);
    ensureDir(notionDir);
    for (const result of results) {
      fs.writeFileSync(path.join(rawDir, `${result.source_id}.json`), `${JSON.stringify(result, null, 2)}\n`);
    }
    fs.writeFileSync(path.join(processedDir, `${runName}-posts.json`), `${JSON.stringify(payload, null, 2)}\n`);
    fs.writeFileSync(path.join(notionDir, `${runName}-review.md`), renderReview(results, args.date));
  }

  console.log(JSON.stringify(payload, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exit(1);
});
