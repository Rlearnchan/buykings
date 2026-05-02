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

function parseArgs(argv) {
  const args = {
    config: path.join(projectRoot, 'config', 'autopark.json'),
    date: new Date().toISOString().slice(0, 10),
    source: null,
    headed: false,
    useAuthProfiles: false,
    authProfile: null,
    browserChannel: null,
    cdpEndpoint: null,
    bootstrap: false,
    bootstrapWaitMs: 120000,
    fullPage: true,
    timeoutMs: 45000,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--config') args.config = argv[++i];
    else if (arg === '--date') args.date = argv[++i];
    else if (arg === '--source') args.source = argv[++i];
    else if (arg === '--headed') args.headed = true;
    else if (arg === '--use-auth-profiles') args.useAuthProfiles = true;
    else if (arg === '--auth-profile') args.authProfile = argv[++i];
    else if (arg === '--browser-channel') args.browserChannel = argv[++i];
    else if (arg === '--cdp-endpoint') args.cdpEndpoint = argv[++i];
    else if (arg === '--bootstrap') {
      args.bootstrap = true;
      args.headed = true;
      args.useAuthProfiles = true;
    } else if (arg === '--bootstrap-wait-ms') args.bootstrapWaitMs = Number.parseInt(argv[++i], 10);
    else if (arg === '--viewport') {
      const [width, height] = argv[++i].split('x').map((value) => Number.parseInt(value, 10));
      args.viewport = { width, height };
    } else if (arg === '--timeout-ms') args.timeoutMs = Number.parseInt(argv[++i], 10);
    else if (arg === '--no-full-page') args.fullPage = false;
    else if (arg === '--help') {
      console.log('Usage: capture_source.mjs --source <source-id> [--date YYYY-MM-DD] [--headed] [--use-auth-profiles] [--bootstrap]');
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (!args.source) throw new Error('Missing required --source <source-id>');
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

function loadSource(configPath, sourceId) {
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const source = (config.sources || []).find((candidate) => candidate.id === sourceId);
  if (!source) throw new Error(`Unknown source id: ${sourceId}`);
  if (!source.enabled) throw new Error(`Source is disabled: ${sourceId}`);
  return source;
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function resolveAuthProfile(args, source) {
  const configured = args.authProfile || (args.useAuthProfiles ? source.auth_profile : null);
  if (!configured) return null;
  const profilePath = path.isAbsolute(configured)
    ? configured
    : path.join(projectRoot, 'runtime', 'profiles', configured);
  ensureDir(profilePath);
  return profilePath;
}

async function createBrowserSession(chromium, args, source) {
  const viewport = args.viewport || { width: 1440, height: 1100 };
  const baseContextOptions = {
    viewport,
    deviceScaleFactor: 1,
    locale: 'en-US',
    colorScheme: 'light',
  };
  if (args.cdpEndpoint) {
    const browser = await chromium.connectOverCDP(args.cdpEndpoint);
    const context = browser.contexts()[0] || await browser.newContext(baseContextOptions);
    return {
      browser,
      context,
      authProfilePath: null,
      browserMode: 'cdp',
      shouldCloseContext: false,
      shouldCloseBrowser: true,
    };
  }
  const authProfilePath = resolveAuthProfile(args, source);

  if (authProfilePath) {
    const persistentOptions = {
      ...baseContextOptions,
      headless: !args.headed,
    };
    if (args.browserChannel) {
      persistentOptions.channel = args.browserChannel;
    } else {
      const executablePath = fallbackChromiumPath();
      if (executablePath) persistentOptions.executablePath = executablePath;
    }
    const context = await chromium.launchPersistentContext(authProfilePath, persistentOptions);
    return {
      browser: context.browser(),
      context,
      authProfilePath,
      browserMode: 'persistent',
      shouldCloseContext: true,
      shouldCloseBrowser: true,
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
  const context = await browser.newContext(baseContextOptions);
  return {
    browser,
    context,
    authProfilePath: null,
    browserMode: 'ephemeral',
    shouldCloseContext: true,
    shouldCloseBrowser: true,
  };
}

async function dismissCommonOverlays(page) {
  const labels = [
    'Accept',
    'Accept All',
    'I Accept',
    'Agree',
    'Got it',
    'Continue',
    '동의',
    '모두 동의',
    '확인',
  ];
  for (const label of labels) {
    const button = page.getByRole('button', { name: label, exact: false }).first();
    try {
      if (await button.isVisible({ timeout: 800 })) {
        await button.click({ timeout: 1500 });
        await page.waitForTimeout(500);
      }
    } catch {
      // Best-effort cleanup; overlays vary by region and site.
    }

    const text = page.getByText(label, { exact: false }).first();
    try {
      if (await text.isVisible({ timeout: 400 })) {
        await text.click({ timeout: 1500 });
        await page.waitForTimeout(500);
      }
    } catch {
      // Best-effort cleanup; overlays vary by region and site.
    }
  }
  await page.keyboard.press('Escape').catch(() => {});
  const closeTargets = [
    '[aria-label="Close"]',
    'button:has-text("×")',
    'button:has-text("Close")',
    '.modal button',
  ];
  for (const selector of closeTargets) {
    const target = page.locator(selector).first();
    try {
      if (await target.isVisible({ timeout: 500 })) {
        await target.click({ timeout: 1500 });
        await page.waitForTimeout(500);
      }
    } catch {
      // Best-effort cleanup; overlays vary by region and site.
    }
  }
}

function isFinvizSource(source) {
  return source.id?.startsWith('finviz-') || /finviz\.com/i.test(source.url || '');
}

async function forceFinvizLightMode(page) {
  await page.emulateMedia({ colorScheme: 'light' }).catch(() => {});
  await page
    .evaluate(() => {
      const lightValues = ['light', 'false', '0'];
      for (const key of ['theme', 'finviz_theme', 'fv_theme', 'darkMode', 'color-theme']) {
        try {
          localStorage.setItem(key, lightValues[0]);
          sessionStorage.setItem(key, lightValues[0]);
        } catch {
          // Storage may be blocked in hardened profiles.
        }
      }
      try {
        document.cookie = 'theme=light; path=/; max-age=31536000';
        document.cookie = 'chartsTheme=light; path=/; max-age=31536000';
        document.cookie = 'darkMode=false; path=/; max-age=31536000';
      } catch {
        // Cookie writes can be rejected by the browser profile.
      }
      document.documentElement.classList.remove('dark', 'theme-dark');
      document.body?.classList.remove('dark', 'theme-dark');
    })
    .catch(() => {});
}

function numberFromText(text) {
  if (!text) return null;
  const normalized = text.replace(/,/g, '');
  const match = normalized.match(/[+-]?\d+(?:\.\d+)?/);
  return match ? Number.parseFloat(match[0]) : null;
}

function parsePercent(value) {
  const parsed = numberFromText(value);
  return Number.isFinite(parsed) ? parsed : null;
}

async function extractCnbcUs10y(page, title, bodyText) {
  const titleMatch = title.match(/US10Y:\s*([0-9.]+)%\s*([+-][0-9.]+)?\s*(?:\(([+-]?[0-9.]+)%\))?/i);
  const bodyMatch = bodyText.match(/Yield\s*\|\s*([0-9:]+\s*[AP]M\s*EDT)\s+([0-9.]+)%\s*([▲▼]?)\s*([+-]?[0-9.]+)/i);
  const keyStats = {};
  const labels = [
    ['yield_open_pct', /Yield Open\s+([0-9.]+)%/i],
    ['yield_day_high_pct', /Yield Day High\s+([0-9.]+)%/i],
    ['yield_day_low_pct', /Yield Day Low\s+([0-9.]+)%/i],
    ['yield_prev_close_pct', /Yield Prev Close\s+([0-9.]+)%/i],
  ];
  for (const [key, regex] of labels) {
    const match = bodyText.match(regex);
    if (match) keyStats[key] = parsePercent(match[1]);
  }

  return {
    quote: {
      symbol: 'US10Y',
      yield_pct: titleMatch ? parsePercent(titleMatch[1]) : bodyMatch ? parsePercent(bodyMatch[2]) : null,
      change: titleMatch ? numberFromText(titleMatch[2]) : bodyMatch ? numberFromText(bodyMatch[4]) : null,
      change_pct: titleMatch ? parsePercent(titleMatch[3]) : null,
      quote_time: bodyMatch ? bodyMatch[1] : null,
      direction: bodyMatch?.[3] === '▼' ? 'down' : bodyMatch?.[3] === '▲' ? 'up' : null,
      ...keyStats,
    },
  };
}

async function extractCnnFearGreed(page, title, bodyText) {
  const topCard = bodyText.match(/Fear\s*&\s*Greed Index\s*→\s*([0-9]+)\s+([A-Za-z ]+?)\s+is driving the US market/i);
  const mainGauge = bodyText.match(/Fear\s*&\s*Greed Index[\s\S]{0,800}?\b([0-9]{1,3})\b[\s\S]{0,160}?(Extreme Fear|Fear|Neutral|Greed|Extreme Greed)/i);
  const previousClose = bodyText.match(/Previous close\s+(Extreme Fear|Fear|Neutral|Greed|Extreme Greed)\s+([0-9]{1,3})/i);
  const oneWeekAgo = bodyText.match(/1 week ago\s+(Extreme Fear|Fear|Neutral|Greed|Extreme Greed)\s+([0-9]{1,3})/i);
  const oneMonthAgo = bodyText.match(/1 month ago\s+(Extreme Fear|Fear|Neutral|Greed|Extreme Greed)\s+([0-9]{1,3})/i);
  const oneYearAgo = bodyText.match(/1 year ago\s+(Extreme Fear|Fear|Neutral|Greed|Extreme Greed)\s+([0-9]{1,3})/i);
  const updatedAt = bodyText.match(/Last updated\s+([^\n]+)/i);

  const score = topCard ? Number.parseInt(topCard[1], 10) : mainGauge ? Number.parseInt(mainGauge[1], 10) : null;
  const status = topCard ? topCard[2].trim() : mainGauge ? mainGauge[2].trim() : null;
  return {
    fear_greed: {
      score,
      status,
      previous_close: previousClose
        ? { status: previousClose[1], score: Number.parseInt(previousClose[2], 10) }
        : null,
      one_week_ago: oneWeekAgo
        ? { status: oneWeekAgo[1], score: Number.parseInt(oneWeekAgo[2], 10) }
        : null,
      one_month_ago: oneMonthAgo
        ? { status: oneMonthAgo[1], score: Number.parseInt(oneMonthAgo[2], 10) }
        : null,
      one_year_ago: oneYearAgo
        ? { status: oneYearAgo[1], score: Number.parseInt(oneYearAgo[2], 10) }
        : null,
      updated_at_text: updatedAt ? updatedAt[1].trim() : null,
    },
  };
}

function parseFedWatchRows(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.replace(/\s+/g, ' ').trim())
    .filter(Boolean)
    .map((line) => line.split(/\s{2,}|\t+/).map((cell) => cell.trim()).filter(Boolean))
    .filter((cells) => cells.length > 1 || /%|bp|target|probab|rate/i.test(cells[0] || ''))
    .slice(0, 80);
}

async function extractTableCells(table) {
  return table
    .locator('tr')
    .evaluateAll((rows) =>
      rows
        .map((row) =>
          [...row.querySelectorAll('th,td')]
            .map((cell) => cell.textContent.replace(/\s+/g, ' ').trim())
            .filter(Boolean),
        )
        .filter((cells) => cells.length),
    )
    .catch(() => []);
}

function classifyFedWatchTable(rows) {
  const joinedRows = rows.map((row) => row.join(' ')).join('\n');
  const header = rows.find((row) => /meeting date/i.test(row.join(' '))) || [];
  const rateColumnCount = header.filter((cell) => /^\d{3,4}-\d{3,4}$/.test(cell)).length;
  const meetingDataRows = rows.filter((row) => /^\d{4}-\d{2}-\d{2}$/.test(row[0] || '') && row.some((cell) => /%$/.test(cell)));
  if (/conditional meeting probabilities/i.test(joinedRows) || (rateColumnCount >= 3 && meetingDataRows.length >= 2)) {
    return 'conditional_meeting_probabilities';
  }
  if (/target rate|probability/i.test(joinedRows) && rows.some((row) => row.some((cell) => /^\d{3,4}-\d{3,4}/.test(cell)))) {
    return 'target_rate_probabilities';
  }
  return 'probability_summary';
}

function parseMeetingToken(line) {
  const match = String(line || '').trim().match(/^(\d{1,2})\s+(\d{1,2})(\d{2})$/);
  if (!match) return null;
  const day = Number.parseInt(match[1], 10);
  const month = Number.parseInt(match[2], 10);
  const year = 2000 + Number.parseInt(match[3], 10);
  if (!day || !month || month > 12) return null;
  return {
    label: `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
    text: match[0],
  };
}

function parseMeetingTokens(text) {
  const lines = String(text || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const tokens = [];
  const seen = new Set();
  for (const line of lines) {
    const token = parseMeetingToken(line);
    if (!token || seen.has(token.label)) continue;
    seen.add(token.label);
    tokens.push(token);
  }
  return tokens.slice(0, 16);
}

function parseTargetRateNowProbabilities(text) {
  const lines = String(text || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const rows = [];
  let inTargetTable = false;
  for (const line of lines) {
    if (/TARGET RATE \(BPS\)/i.test(line)) {
      inTargetTable = true;
      continue;
    }
    if (inTargetTable && /^\*/.test(line)) break;
    if (!inTargetTable) continue;
    const cells = line.split(/\t+/).map((cell) => cell.replace(/\s+/g, ' ').trim()).filter(Boolean);
    if (!cells.length || !/^\d{3,4}-\d{3,4}/.test(cells[0])) continue;
    const probability = cells.find((cell, index) => index > 0 && /^\d+(?:\.\d+)?%$/.test(cell));
    if (!probability) continue;
    rows.push({
      rate: cells[0].replace(/\s*\(Current\)\s*/i, '').trim(),
      probability,
    });
  }
  return rows;
}

async function extractConditionalMeetingProbabilities(scopes) {
  const frame = scopes.find((scope) => /QuikStrikeView/i.test(scope.url?.() || ''));
  if (!frame) return null;
  const initialText = await frame.locator('body').innerText({ timeout: 2500 }).catch(() => '');
  const tokens = parseMeetingTokens(initialText);
  if (tokens.length < 2) return null;
  const meetings = [];
  const rates = new Set();
  for (const token of tokens) {
    const option = frame.getByText(token.text, { exact: true }).first();
    if (!(await option.isVisible({ timeout: 800 }).catch(() => false))) continue;
    await option.click({ timeout: 2500 }).catch(() => {});
    await frame.page().waitForTimeout(650);
    const text = await frame.locator('body').innerText({ timeout: 2500 }).catch(() => '');
    const probabilities = parseTargetRateNowProbabilities(text);
    if (!probabilities.length) continue;
    probabilities.forEach((row) => rates.add(row.rate));
    meetings.push({ meeting_date: token.label, probabilities });
  }
  if (meetings.length < 2 || rates.size < 2) return null;
  const sortedRates = [...rates].sort((a, b) => Number.parseInt(a.split('-')[0], 10) - Number.parseInt(b.split('-')[0], 10));
  const rows = [
    ['MEETING DATE', ...sortedRates],
    ...meetings.map((meeting) => {
      const byRate = new Map(meeting.probabilities.map((row) => [row.rate, row.probability]));
      return [meeting.meeting_date, ...sortedRates.map((rate) => byRate.get(rate) || '0.0%')];
    }),
  ];
  return {
    index: 'reconstructed',
    row_count: rows.length,
    rows,
    kind: 'conditional_meeting_probabilities',
    reconstruction: 'clicked_meeting_dates',
  };
}

async function extractCmeFedWatch(page, title, bodyText) {
  await clickFirstVisibleText(page, ['Probabilities', '확률', '금리 확률']);
  await page.waitForTimeout(1500);
  const scopes = [page, ...page.frames()];
  const tables = [];
  const conditional = await extractConditionalMeetingProbabilities(scopes);
  if (conditional) tables.push(conditional);
  for (const scope of scopes) {
    const locator = scope.locator('table, [role="table"], .table, .cmeTable');
    const count = await locator.count().catch(() => 0);
    for (let index = 0; index < count; index += 1) {
      const table = locator.nth(index);
      const text = await table.innerText({ timeout: 1200 }).catch(() => '');
      if (!/%|probab|target|rate|bp/i.test(text)) continue;
      const cellRows = await extractTableCells(table);
      const rows = cellRows.length ? cellRows : parseFedWatchRows(text);
      if (!rows.length) continue;
      tables.push({
        index,
        row_count: rows.length,
        rows,
        kind: classifyFedWatchTable(rows),
      });
    }
  }
  const bodyRows = parseFedWatchRows(bodyText)
    .filter((cells) => /%|probab|target|rate|bp/i.test(cells.join(' ')))
    .slice(0, 40);
  return {
    fedwatch: {
      capture_mode: 'table_text',
      table_count: tables.length,
      selected_table:
        tables.find((table) => table.kind === 'conditional_meeting_probabilities') ||
        tables.find((table) => table.kind === 'target_rate_probabilities') ||
        (tables.length ? tables[tables.length - 1] : null),
      tables,
      fallback_rows: tables.length ? [] : bodyRows,
      title,
    },
  };
}

async function extractStructuredData(source, page, title, bodyText) {
  if (source.id === 'cnbc-us10y') {
    return extractCnbcUs10y(page, title, bodyText);
  }
  if (source.id === 'cnn-fear-greed') {
    return extractCnnFearGreed(page, title, bodyText);
  }
  if (source.id === 'cme-fedwatch') {
    return extractCmeFedWatch(page, title, bodyText);
  }
  return {};
}

async function detectPartialCapture(source, page, bodyText) {
  if (!source.id.startsWith('investing-')) return null;
  const canvasCount = await page.locator('canvas').count().catch(() => 0);
  const iframeCount = await page.locator('iframe').count().catch(() => 0);
  const hasTradingViewFooter = /Powered by TradingView/i.test(bodyText);
  const chartUnavailable =
    /refused to connect/i.test(bodyText) ||
    /연결을 거부/i.test(bodyText) ||
    (hasTradingViewFooter && canvasCount === 0);

  if (!chartUnavailable) return null;
  return {
    status: 'partial',
    issue: 'investing_chart_frame_unavailable',
    detail: 'Investing page loaded, but the embedded TradingView chart frame did not render.',
    canvas_count: canvasCount,
    iframe_count: iframeCount,
  };
}

function clampClip(clip, viewport) {
  return {
    x: Math.max(0, Math.round(clip.x)),
    y: Math.max(0, Math.round(clip.y)),
    width: Math.max(1, Math.min(Math.round(clip.width), viewport.width - Math.max(0, Math.round(clip.x)))),
    height: Math.max(1, Math.min(Math.round(clip.height), viewport.height - Math.max(0, Math.round(clip.y)))),
  };
}

async function captureFinvizIndexFutures(page, screenshotDir, safeId, viewport) {
  const canvases = await page.locator('canvas').evaluateAll((items) =>
    items
      .map((el) => {
        const rect = el.getBoundingClientRect();
        return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
      })
      .filter((rect) => rect.width >= 250 && rect.height >= 150 && rect.y < 420)
      .slice(0, 3),
  );
  if (canvases.length < 3) return null;

  const top = Math.min(...canvases.map((rect) => rect.y));
  const bottom = Math.max(...canvases.map((rect) => rect.y + rect.height));
  const first = canvases[0];
  const second = canvases[1];
  const third = canvases[2];
  const variants = [
    {
      suffix: '1',
      label: 'DOW / NASDAQ',
      clip: {
        x: first.x - 12,
        y: top - 10,
        width: second.x + second.width - first.x + 24,
        height: bottom - top + 18,
      },
    },
    {
      suffix: '2',
      label: 'NASDAQ / S&P 500',
      clip: {
        x: second.x - 12,
        y: top - 10,
        width: third.x + third.width - second.x + 24,
        height: bottom - top + 18,
      },
    },
  ];

  const paths = [];
  for (const variant of variants) {
    const filePath = path.join(screenshotDir, `${safeId}-${variant.suffix}.png`);
    await page.screenshot({ path: filePath, clip: clampClip(variant.clip, viewport) });
    paths.push({
      label: variant.label,
      path: filePath,
      relative_path: path.relative(repoRoot, filePath),
    });
  }
  return paths;
}

async function captureFinvizHeatmap(page, screenshotDir, safeId, label = 'Finviz Map') {
  const target = page.locator('#map').first();
  if (!(await target.isVisible({ timeout: 3000 }).catch(() => false))) return null;
  const filePath = path.join(screenshotDir, `${safeId}-map.png`);
  await target.screenshot({ path: filePath });
  return [
    {
      label,
      path: filePath,
      relative_path: path.relative(repoRoot, filePath),
    },
  ];
}

async function captureCnbcUs10y(page, screenshotDir, safeId, viewport) {
  const quote = await page.locator('#quote-page-strip').first().boundingBox().catch(() => null);
  const chart = await page.locator('.PhoenixChartWrapper-rendererWeb').first().boundingBox().catch(() => null);
  if (!quote || !chart) return null;

  const filePath = path.join(screenshotDir, `${safeId}-quote-chart.png`);
  const x = Math.min(quote.x, chart.x) - 24;
  const y = Math.min(quote.y, chart.y) - 18;
  const right = Math.max(quote.x + quote.width, chart.x + chart.width);
  const bottom = Math.max(quote.y + quote.height, chart.y + chart.height);
  await page.screenshot({
    path: filePath,
    clip: clampClip({ x, y, width: right - x + 12, height: bottom - y + 16 }, viewport),
  });
  return [
    {
      label: 'US10Y quote and chart',
      path: filePath,
      relative_path: path.relative(repoRoot, filePath),
    },
  ];
}

async function captureCnnFearGreed(page, screenshotDir, safeId) {
  const target = page.locator('.market-tabbed-container').first();
  if (!(await target.isVisible({ timeout: 3000 }).catch(() => false))) return null;
  const filePath = path.join(screenshotDir, `${safeId}-gauge.png`);
  await target.screenshot({ path: filePath });
  return [
    {
      label: 'Fear & Greed gauge',
      path: filePath,
      relative_path: path.relative(repoRoot, filePath),
    },
  ];
}

async function clickFirstVisibleText(page, patterns) {
  const scopes = [page, ...page.frames()];
  for (const scope of scopes) {
    for (const pattern of patterns) {
      const target = scope.getByText(pattern, { exact: false }).first();
      if (await target.isVisible({ timeout: 1000 }).catch(() => false)) {
        await target.click({ timeout: 2000 }).catch(() => {});
        await page.waitForTimeout(1200);
        return true;
      }
    }
  }
  return false;
}

async function captureCmeFedWatch(page, screenshotDir, safeId, viewport) {
  await clickFirstVisibleText(page, ['Probabilities', '확률', '概率']);
  const scopes = [page, ...page.frames()];
  const patterns = [
    /Target Rate Probabilities/i,
    /Meeting Probabilities/i,
    /대상.*금리.*확률/i,
    /목표.*금리.*확률/i,
  ];
  for (const scope of scopes) {
    for (const pattern of patterns) {
      const locator = scope.getByText(pattern).last();
      await locator.waitFor({ state: 'visible', timeout: 2500 }).catch(() => {});
      const box = await locator.boundingBox().catch(() => null);
      if (!box) continue;
      const filePath = path.join(screenshotDir, `${safeId}-probabilities.png`);
      await page.screenshot({
        path: filePath,
        timeout: 10000,
        clip: clampClip({
          x: box.x - 40,
          y: box.y - 18,
          width: Math.max(760, Math.min(1120, viewport.width - Math.max(0, box.x - 40))),
          height: 360,
        }, viewport),
      });
      return [
        {
          label: 'FedWatch target rate probabilities',
          path: filePath,
          relative_path: path.relative(repoRoot, filePath),
        },
      ];
    }
  }
  return null;
}

async function captureCmeFedWatchStable(page, screenshotDir, safeId, viewport) {
  await clickFirstVisibleText(page, ['Probabilities', '확률', '금리 확률']);
  await page.waitForTimeout(1800);
  const scopes = [page, ...page.frames()];
  const tableCandidates = [];
  for (const scope of scopes) {
    const tables = scope.locator('table, [role="table"], .table, .cmeTable');
    const count = await tables.count().catch(() => 0);
    for (let index = 0; index < count; index += 1) {
      const table = tables.nth(index);
      const box = await table.boundingBox().catch(() => null);
      if (!box || box.width < 520 || box.height < 120) continue;
      const text = await table.innerText({ timeout: 800 }).catch(() => '');
      if (!/probab|target|rate|bp|%/i.test(text)) continue;
      tableCandidates.push({ table, box });
    }
  }
  if (tableCandidates.length) {
    tableCandidates.sort((a, b) => a.box.y - b.box.y);
    const box = tableCandidates[tableCandidates.length - 1].box;
    const filePath = path.join(screenshotDir, `${safeId}-probabilities-table.png`);
    try {
      await page.screenshot({
        path: filePath,
        clip: clampClip({
          x: box.x - 24,
          y: box.y - 18,
          width: box.width + 48,
          height: box.height + 36,
        }, viewport),
      });
      return [
        {
          label: 'FedWatch lower probabilities table',
          path: filePath,
          relative_path: path.relative(repoRoot, filePath),
        },
      ];
    } catch {
      // Some CME tables live in frames with coordinates that are not safe to use as page clips.
    }
  }

  const tableBoxes = [];
  for (const scope of scopes) {
    const rows = await scope.locator('table, [role="table"], .table, .cmeTable').evaluateAll((nodes) =>
      nodes
        .map((el) => {
          const rect = el.getBoundingClientRect();
          const text = el.innerText || el.textContent || '';
          return { x: rect.x, y: rect.y, width: rect.width, height: rect.height, text };
        })
        .filter((rect) => rect.width >= 520 && rect.height >= 120 && /probab|target|rate|bp|%/i.test(rect.text)),
    ).catch(() => []);
    tableBoxes.push(...rows);
  }
  if (false && tableBoxes.length) {
    tableBoxes.sort((a, b) => a.y - b.y);
    const box = tableBoxes[tableBoxes.length - 1];
    const filePath = path.join(screenshotDir, `${safeId}-probabilities-table.png`);
    await page.screenshot({
      path: filePath,
      clip: clampClip({
        x: box.x - 24,
        y: box.y - 18,
        width: box.width + 48,
        height: box.height + 36,
      }, viewport),
    });
    return [
      {
        label: 'FedWatch lower probabilities table',
        path: filePath,
        relative_path: path.relative(repoRoot, filePath),
      },
    ];
  }

  const patterns = [
    /Target Rate Probabilities/i,
    /Meeting Probabilities/i,
    /Probability Distribution/i,
    /목표.*금리.*확률/i,
    /미팅.*확률/i,
  ];
  for (const scope of scopes) {
    for (const pattern of patterns) {
      const locator = scope.getByText(pattern).last();
      await locator.waitFor({ state: 'visible', timeout: 2500 }).catch(() => {});
      const box = await locator.boundingBox().catch(() => null);
      if (!box) continue;
      const filePath = path.join(screenshotDir, `${safeId}-probabilities-heading.png`);
      try {
        await page.screenshot({
          path: filePath,
          timeout: 10000,
          clip: clampClip({
            x: box.x - 40,
            y: box.y - 18,
            width: Math.max(760, Math.min(1120, viewport.width - Math.max(0, box.x - 40))),
            height: 420,
          }, viewport),
        });
        return [
          {
            label: 'FedWatch probabilities near heading',
            path: filePath,
            relative_path: path.relative(repoRoot, filePath),
          },
        ];
      } catch {
        // Fall back to the viewport below.
      }
    }
  }

  const fallbackPath = path.join(screenshotDir, `${safeId}-probabilities-fallback.png`);
  await page.screenshot({ path: fallbackPath, fullPage: false, timeout: 10000 });
  return [
    {
      label: 'FedWatch probabilities fallback viewport',
      path: fallbackPath,
      relative_path: path.relative(repoRoot, fallbackPath),
    },
  ];
}

async function captureSourceScreenshots(source, page, screenshotDir, safeId, defaultScreenshotPath, fullPage, viewport) {
  if (source.id === 'finviz-index-futures') {
    const paths = await captureFinvizIndexFutures(page, screenshotDir, safeId, viewport);
    if (paths) return paths;
  }
  if (source.id === 'finviz-sp500-heatmap' || source.id === 'finviz-russell-heatmap') {
    const paths = await captureFinvizHeatmap(page, screenshotDir, safeId, source.name || source.id);
    if (paths) return paths;
  }
  if (source.id === 'cnbc-us10y') {
    const paths = await captureCnbcUs10y(page, screenshotDir, safeId, viewport);
    if (paths) return paths;
  }
  if (source.id === 'cnn-fear-greed') {
    const paths = await captureCnnFearGreed(page, screenshotDir, safeId);
    if (paths) return paths;
  }
  if (source.id === 'cme-fedwatch') {
    return [];
  }

  await page.screenshot({ path: defaultScreenshotPath, fullPage });
  return [
    {
      label: source.name || source.id,
      path: defaultScreenshotPath,
      relative_path: path.relative(repoRoot, defaultScreenshotPath),
    },
  ];
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const source = loadSource(path.resolve(repoRoot, args.config), args.source);
  const { chromium } = await loadPlaywright();
  const session = await createBrowserSession(chromium, args, source);
  const { browser, context } = session;
  const page = await context.newPage();
  const viewport = args.viewport || { width: 1440, height: 1100 };
  await page.setViewportSize(viewport).catch(() => {});
  const startedAt = new Date().toISOString();
  const safeId = source.id.replace(/[^a-zA-Z0-9_-]+/g, '-');
  const screenshotDir = path.join(projectRoot, 'runtime', 'screenshots', args.date);
  const rawDir = path.join(projectRoot, 'data', 'raw', args.date);
  ensureDir(screenshotDir);
  ensureDir(rawDir);

  const screenshotPath = path.join(screenshotDir, `${safeId}.png`);
  const metadataPath = path.join(rawDir, `${safeId}.json`);

  try {
    if (isFinvizSource(source)) {
      await page.emulateMedia({ colorScheme: 'light' }).catch(() => {});
    }
    await page.goto(source.url, { waitUntil: 'domcontentloaded', timeout: args.timeoutMs });
    if (isFinvizSource(source)) {
      await forceFinvizLightMode(page);
      await page.reload({ waitUntil: 'domcontentloaded', timeout: args.timeoutMs }).catch(() => {});
    }
    await dismissCommonOverlays(page);
    if (args.bootstrap) {
      console.error(
        JSON.stringify(
          {
            ok: true,
            mode: 'bootstrap',
            source_id: source.id,
            auth_profile_path: session.authProfilePath,
            message: 'Complete login/security checks in the browser window. Capture will continue after the wait.',
            wait_ms: args.bootstrapWaitMs,
          },
          null,
          2,
        ),
      );
      await page.waitForTimeout(args.bootstrapWaitMs);
      await dismissCommonOverlays(page);
    }
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(2500);
    await dismissCommonOverlays(page);

    const fullPage = source.capture_full_page === false ? false : args.fullPage;
    const capturedImages = await captureSourceScreenshots(source, page, screenshotDir, safeId, screenshotPath, fullPage, viewport);
    const title = await page.title();
    const bodyText = await page.locator('body').innerText({ timeout: 3000 }).catch(() => '');
    const blocked =
      /just a moment/i.test(title) ||
      /security verification/i.test(bodyText) ||
      /not a bot/i.test(bodyText);
    const partial = blocked ? null : await detectPartialCapture(source, page, bodyText);
    const extracted = blocked ? {} : await extractStructuredData(source, page, title, bodyText);

    const metadata = {
      source_id: source.id,
      name: source.name || source.id,
      section: source.section || null,
      kind: source.kind,
      configured_url: source.url,
      final_url: page.url(),
      title,
      captured_at: new Date().toISOString(),
      started_at: startedAt,
      target_date: args.date,
      screenshot_path: capturedImages[0]?.relative_path || null,
      screenshot_paths: capturedImages.map(({ label, relative_path }) => ({ label, path: relative_path })),
      capture_notes: source.capture_notes || '',
      full_page: fullPage,
      browser_mode: session.browserMode,
      auth_profile_path: session.authProfilePath ? path.relative(repoRoot, session.authProfilePath) : null,
      browser_channel: args.browserChannel || null,
      headed: args.headed,
      bootstrap: args.bootstrap,
      partial_issue: partial,
      extracted,
      status: blocked ? 'blocked' : partial ? 'partial' : 'ok',
    };
    fs.writeFileSync(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`);
    console.log(JSON.stringify({ ok: !blocked && !partial, metadata }, null, 2));
    if (blocked || partial) {
      process.exitCode = 2;
    }
  } catch (error) {
    const metadata = {
      source_id: source.id,
      name: source.name || source.id,
      section: source.section || null,
      kind: source.kind,
      configured_url: source.url,
      final_url: page.url(),
      title: await page.title().catch(() => ''),
      captured_at: new Date().toISOString(),
      started_at: startedAt,
      target_date: args.date,
      screenshot_path: fs.existsSync(screenshotPath) ? path.relative(repoRoot, screenshotPath) : null,
      capture_notes: source.capture_notes || '',
      browser_mode: session.browserMode,
      auth_profile_path: session.authProfilePath ? path.relative(repoRoot, session.authProfilePath) : null,
      browser_channel: args.browserChannel || null,
      headed: args.headed,
      bootstrap: args.bootstrap,
      status: 'error',
      error: error.message,
    };
    fs.writeFileSync(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`);
    console.error(JSON.stringify({ ok: false, metadata }, null, 2));
    process.exitCode = 1;
  } finally {
    await page.close().catch(() => {});
    if (session.shouldCloseContext) await context.close().catch(() => {});
    if (session.shouldCloseBrowser && browser) await browser.close().catch(() => {});
  }
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exit(1);
});
