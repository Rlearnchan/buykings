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

const defaultSources = [
  {
    id: 'yahoo-finance-news-scroll',
    label: 'Yahoo Finance News',
    url: 'https://finance.yahoo.com/news/',
    method: 'browser_scroll',
    authority: 'medium',
    ease: 'high',
    notes: 'Finance news landing page. Good headline river, but page navigation noise must be filtered.',
  },
  {
    id: 'yahoo-finance-ticker-rss',
    label: 'Yahoo Finance Ticker RSS',
    url: 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC,%5EIXIC,%5EDJI,CL%3DF,%5ETNX,NVDA,MSFT,AMZN,GOOGL',
    method: 'rss',
    authority: 'medium',
    ease: 'high',
    notes: 'Stable RSS seeded by index, oil, rate, and big-tech tickers.',
  },
  {
    id: 'finviz-news',
    label: 'Finviz News',
    url: 'https://finviz.com/news.ashx?v=3',
    method: 'html',
    authority: 'medium',
    ease: 'high',
    notes: 'Headline-only market river. Often links out to original publishers.',
  },
  {
    id: 'biztoc-home',
    label: 'BizToc Home',
    url: 'https://biztoc.com/',
    method: 'browser_scroll',
    authority: 'medium',
    ease: 'medium',
    notes: 'Large volume aggregator. Needs category and source-quality filters.',
  },
  {
    id: 'biztoc-feed',
    label: 'BizToc RSS',
    url: 'https://biztoc.com/feed',
    method: 'rss',
    authority: 'medium',
    ease: 'high',
    notes: 'Stable high-volume feed with mixed business and low-signal headlines.',
  },
  {
    id: 'cnbc-world',
    label: 'CNBC World',
    url: 'https://www.cnbc.com/world/?region=world',
    method: 'browser_scroll',
    authority: 'medium_high',
    ease: 'medium',
    notes: 'Fast market-news context. Public pages are usually accessible but dynamic.',
  },
  {
    id: 'tradingview-news',
    label: 'TradingView News',
    url: 'https://www.tradingview.com/news/',
    method: 'browser_scroll',
    authority: 'medium',
    ease: 'medium',
    notes: 'Ticker-oriented headlines and syndicated market items.',
  },
  {
    id: 'factset-insight-rss',
    label: 'FactSet Insight RSS',
    url: 'https://insight.factset.com/rss.xml',
    method: 'rss',
    authority: 'high',
    ease: 'high',
    notes: 'Lower cadence but strong earnings and market-context authority.',
  },
];

function parseArgs(argv) {
  const args = {
    date: new Date().toISOString().slice(0, 10),
    outputDir: path.join(projectRoot, 'docs', 'source_audits'),
    maxItemsPerSource: 80,
    maxScrolls: 10,
    headed: false,
    timeoutMs: 45000,
    browserChannel: 'chrome',
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--date') args.date = argv[++i];
    else if (arg === '--output-dir') args.outputDir = path.resolve(argv[++i]);
    else if (arg === '--max-items-per-source') args.maxItemsPerSource = Number.parseInt(argv[++i], 10);
    else if (arg === '--max-scrolls') args.maxScrolls = Number.parseInt(argv[++i], 10);
    else if (arg === '--headed') args.headed = true;
    else if (arg === '--timeout-ms') args.timeoutMs = Number.parseInt(argv[++i], 10);
    else if (arg === '--browser-channel') args.browserChannel = argv[++i];
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
    throw new Error('Playwright is unavailable.');
  }
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function clean(value, limit = null) {
  const text = String(value || '')
    .replace(/[\u200b-\u200f\ufeff]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  if (limit && text.length > limit) return `${text.slice(0, limit - 1).trim()}…`;
  return text;
}

function hostOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
}

function csvEscape(value) {
  const text = String(value ?? '');
  if (/[",\r\n]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
  return text;
}

function writeCsv(filePath, rows) {
  const headers = [
    'item_id',
    'source_id',
    'source_label',
    'publisher',
    'title',
    'url',
    'host',
    'published_at',
    'snippet',
    'content_level',
    'collection_method',
    'captured_at',
  ];
  const lines = [headers.join(',')];
  for (const row of rows) {
    lines.push(headers.map((header) => csvEscape(row[header] || '')).join(','));
  }
  fs.writeFileSync(filePath, `${lines.join('\n')}\n`, 'utf8');
}

function htmlDecode(value) {
  return String(value || '')
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function stripTags(value) {
  return String(value || '').replace(/<[^>]+>/g, ' ');
}

function tagText(xml, tag) {
  const match = xml.match(new RegExp(`<${tag}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tag}>`, 'i'));
  return match ? htmlDecode(match[1]) : '';
}

function sourceText(itemXml) {
  const match = itemXml.match(/<source(?:\s[^>]*)?>([\s\S]*?)<\/source>/i);
  return match ? htmlDecode(match[1]) : '';
}

async function fetchText(url, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 AutoparkSourceAudit/0.1',
        Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      },
    });
    return { ok: response.ok, status: response.status, text: await response.text() };
  } finally {
    clearTimeout(timer);
  }
}

async function collectRss(source, args, capturedAt) {
  const fetched = await fetchText(source.url, args.timeoutMs);
  if (!fetched.ok) throw new Error(`HTTP ${fetched.status}`);
  const items = [...fetched.text.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi)]
    .slice(0, args.maxItemsPerSource)
    .map((match, index) => {
      const itemXml = match[1];
      const title = clean(tagText(itemXml, 'title'), 180);
      const url = clean(tagText(itemXml, 'link'));
      const snippet = clean(stripTags(tagText(itemXml, 'description')), 300);
      return {
        item_id: `${source.id}-${String(index + 1).padStart(3, '0')}`,
        source_id: source.id,
        source_label: source.label,
        publisher: clean(sourceText(itemXml), 80),
        title,
        url,
        host: hostOf(url),
        published_at: clean(tagText(itemXml, 'pubDate'), 80),
        snippet,
        content_level: snippet ? 'headline+summary' : 'headline',
        collection_method: source.method,
        captured_at: capturedAt,
      };
    })
    .filter((item) => item.title && item.url);
  return { items, stopReason: 'rss_items_exhausted', status: 'ok' };
}

async function collectHtml(source, args, capturedAt) {
  const fetched = await fetchText(source.url, args.timeoutMs);
  if (!fetched.ok) throw new Error(`HTTP ${fetched.status}`);
  const rows = [];
  const seen = new Set();
  for (const match of fetched.text.matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a>/gi)) {
    const attrs = match[1] || '';
    const hrefMatch = attrs.match(/\bhref=["']([^"']+)["']/i);
    if (!hrefMatch) continue;
    let url = '';
    try {
      url = new URL(htmlDecode(hrefMatch[1]), source.url).toString();
    } catch {
      continue;
    }
    const title = clean(stripTags(htmlDecode(match[2])), 180);
    const item = {
      item_id: `${source.id}-${String(rows.length + 1).padStart(3, '0')}`,
      source_id: source.id,
      source_label: source.label,
      publisher: '',
      title,
      url,
      host: hostOf(url),
      published_at: '',
      snippet: '',
      content_level: 'headline',
      collection_method: source.method,
      captured_at: capturedAt,
    };
    const key = `${item.title} ${item.url}`;
    if (seen.has(key) || !item.title || !sourceSpecificKeep(source.id, item)) continue;
    seen.add(key);
    rows.push(item);
    if (rows.length >= args.maxItemsPerSource) break;
  }
  return { items: rows, stopReason: rows.length >= args.maxItemsPerSource ? 'item_limit' : 'html_links_exhausted', status: 'ok' };
}

function sourceSpecificKeep(sourceId, item) {
  const loweredTitle = item.title.toLowerCase();
  const url = item.url.toLowerCase();
  const parsed = (() => {
    try {
      return new URL(item.url);
    } catch {
      return null;
    }
  })();
  const pathName = parsed?.pathname || '';
  const navTitles = new Set([
    'home',
    'screener',
    'charts',
    'maps',
    'groups',
    'portfolio',
    'insider',
    'futures',
    'forex',
    'crypto',
    'calendar',
    'pricing',
    'theme',
    'help',
    'login',
    'register',
    'market news',
    'market pulse',
    'stocks news',
    'etf news',
    'crypto news',
    'financial news',
    'trending tickers',
  ]);
  if (loweredTitle.startsWith('skip to ')) return false;
  if (navTitles.has(loweredTitle) || ['subscribe', 'sign in', 'watchlist', 'markets', 'news'].includes(loweredTitle)) return false;
  if (/^(finance:|tradingview main page)/i.test(item.title)) return false;
  if (sourceId.startsWith('yahoo')) {
    if (!/(finance\.yahoo\.com|fool\.com|investors\.com|barrons\.com|marketwatch\.com|thestreet\.com|beincrypto\.com)/.test(url)) return false;
    if (/health\.yahoo\.com|\/personal-finance\/|\/credit-cards\/|\/mortgages\//.test(url)) return false;
    if (hostOf(item.url) === 'finance.yahoo.com' && !/(^\/news\/|^\/m\/|^\/markets\/|^\/sectors\/|^\/video\/)/.test(pathName)) return false;
  }
  if (sourceId === 'finviz-news') {
    if (/\/quote|\/screener|\/login|\/register|\/elite|\/calendar|\/map|\/groups|\/portfolio|\/futures|\/forex|\/crypto/.test(url)) return false;
    if (hostOf(item.url) === 'finviz.com' && !pathName.startsWith('/news/')) return false;
  }
  if (sourceId.startsWith('biztoc') && /\/account|\/login|\/upgrade|\/about|\/privacy/.test(url)) return false;
  return true;
}

async function collectBrowser(source, args, capturedAt, context) {
  const page = await context.newPage();
  const seen = new Map();
  let stopReason = 'max_scrolls';
  try {
    await page.goto(source.url, { waitUntil: 'domcontentloaded', timeout: args.timeoutMs });
    await page.waitForTimeout(2500);
    let previousHeight = 0;
    let stableCount = 0;
    for (let scroll = 0; scroll <= args.maxScrolls; scroll += 1) {
      const batch = await page.evaluate((limit) => {
        const cleanLocal = (value) => String(value || '').replace(/\s+/g, ' ').trim();
        const rows = [];
        for (const anchor of Array.from(document.querySelectorAll('a[href]'))) {
          const title = cleanLocal(anchor.innerText || anchor.getAttribute('aria-label') || anchor.getAttribute('title') || '');
          if (title.length < 14 || title.length > 220) continue;
          let url = '';
          try {
            url = new URL(anchor.getAttribute('href'), location.href).toString();
          } catch {
            continue;
          }
          const parent = anchor.closest('article, li, tr, div') || anchor.parentElement;
          const parentText = cleanLocal(parent?.innerText || '');
          const timeText = cleanLocal(parent?.querySelector?.('time')?.getAttribute('datetime') || parent?.querySelector?.('time')?.innerText || '');
          const publisher = cleanLocal(
            parent?.querySelector?.('[data-test-locator="publisher"], [class*="source"], [class*="provider"], .news-link-left, .nn-tab-link')?.innerText || '',
          );
          rows.push({
            title,
            url,
            publisher,
            published_at: timeText,
            snippet: parentText && parentText !== title ? parentText.slice(0, 320) : '',
          });
          if (rows.length >= limit) break;
        }
        return { rows, height: document.documentElement.scrollHeight, y: window.scrollY };
      }, args.maxItemsPerSource * 4);
      for (const raw of batch.rows) {
        const item = {
          item_id: `${source.id}-${String(seen.size + 1).padStart(3, '0')}`,
          source_id: source.id,
          source_label: source.label,
          publisher: clean(raw.publisher, 80),
          title: clean(raw.title, 180),
          url: clean(raw.url),
          host: hostOf(raw.url),
          published_at: clean(raw.published_at, 80),
          snippet: clean(raw.snippet, 300),
          content_level: raw.snippet ? 'headline+snippet' : 'headline',
          collection_method: source.method,
          captured_at: capturedAt,
        };
        const key = `${item.title} ${item.url}`;
        if (seen.has(key) || !sourceSpecificKeep(source.id, item)) continue;
        item.item_id = `${source.id}-${String(seen.size + 1).padStart(3, '0')}`;
        seen.set(key, item);
        if (seen.size >= args.maxItemsPerSource) {
          stopReason = 'item_limit';
          break;
        }
      }
      if (seen.size >= args.maxItemsPerSource) break;
      if (batch.height <= previousHeight + 20) stableCount += 1;
      else stableCount = 0;
      previousHeight = batch.height;
      if (stableCount >= 2) {
        stopReason = 'scroll_exhausted';
        break;
      }
      await page.mouse.wheel(0, 1200);
      await page.waitForTimeout(1200);
    }
    const items = [...seen.values()].slice(0, args.maxItemsPerSource);
    return { items, stopReason, status: 'ok', finalUrl: page.url() };
  } finally {
    await page.close().catch(() => {});
  }
}

function scoreSource(source, result) {
  const items = result.items || [];
  const headlineCount = items.length;
  const summaryCount = items.filter((item) => item.snippet).length;
  const originalHosts = new Set(items.map((item) => item.host).filter(Boolean)).size;
  const amountScore = headlineCount >= 60 ? 5 : headlineCount >= 35 ? 4 : headlineCount >= 15 ? 3 : headlineCount >= 5 ? 2 : headlineCount > 0 ? 1 : 0;
  const summaryScore = summaryCount >= 30 ? 5 : summaryCount >= 15 ? 4 : summaryCount >= 5 ? 3 : summaryCount > 0 ? 2 : 0;
  const authorityScore = source.authority === 'high' ? 5 : source.authority === 'medium_high' ? 4 : source.authority === 'medium' ? 3 : 2;
  const easeScore = result.status === 'ok' ? (source.ease === 'high' ? 5 : source.ease === 'medium' ? 3 : 2) : 0;
  return {
    headlineCount,
    summaryCount,
    originalHosts,
    amountScore,
    summaryScore,
    authorityScore,
    easeScore,
    overallScore: amountScore + summaryScore + authorityScore + easeScore,
  };
}

function sourceMemo(source, score, sampleTitles) {
  if (source.id.includes('yahoo-finance-ticker-rss')) {
    return '접근성이 가장 좋고 시장/유가/금리/빅테크 티커 기반으로 당일 헤드라인이 잘 잡힌다. 다만 Motley Fool 등 외부 저신호 매체가 섞여 원출처별 가중치가 필요하다.';
  }
  if (source.id.includes('yahoo-finance-news-scroll')) {
    return '페이지 기반으로 더 넓은 헤드라인 강을 만들 수 있지만 네비게이션/생활 뉴스 잡음 필터가 중요하다.';
  }
  if (source.id.includes('finviz')) {
    return '시장 친화적 헤드라인이 많고 원문 링크로 보내므로 headline radar로 좋다. 원문 전문보다는 제목/출처/시간 메타 중심이 적합하다.';
  }
  if (source.id.includes('biztoc')) {
    return '정보량은 많지만 잡음도 많다. 출처 라벨, 카테고리, 시장 키워드로 강하게 걸러야 한다.';
  }
  if (source.id.includes('factset')) {
    return '양은 적지만 실적/시장 맥락 권위가 높다. 리드 후보보다는 해석 보강에 강하다.';
  }
  if (source.id.includes('cnbc')) {
    return '방송 친화적인 빠른 뉴스가 많다. 공개 페이지 접근성과 동적 렌더링 품질을 계속 봐야 한다.';
  }
  if (source.id.includes('tradingview')) {
    return '티커/섹터성 헤드라인이 많아 종목 연결에 유리하지만 중복/신디케이션 필터가 필요하다.';
  }
  return `샘플: ${sampleTitles.slice(0, 2).join(' / ')}`;
}

function renderReport(args, capturedAt, sourceResults, rows, sourceSummaries) {
  const lines = [
    `# Autopark Source Collection Audit ${args.date}`,
    '',
    `- 생성 시각: \`${capturedAt}\``,
    `- 수집 행: \`${rows.length}\``,
    `- CSV: \`${path.basename(args.csvPath)}\``,
    `- 원문 전문/원시 HTML은 저장하지 않음`,
    '',
    '## Source Summary',
    '',
    '| Source | Status | Headlines | Summary/Snippet | Hosts | Ease | Authority | Overall | Stop/Note |',
    '|---|---:|---:|---:|---:|---:|---:|---:|---|',
  ];
  for (const summary of sourceSummaries) {
    lines.push(
      `| ${summary.label} | ${summary.status} | ${summary.headlineCount} | ${summary.summaryCount} | ${summary.originalHosts} | ${summary.easeScore} | ${summary.authorityScore} | ${summary.overallScore} | ${summary.stopReason || summary.error || ''} |`,
    );
  }
  lines.push('', '## 평가 메모', '');
  for (const summary of sourceSummaries) {
    lines.push(`### ${summary.label}`, '');
    lines.push(`- 정보량: 헤드라인 ${summary.headlineCount}개, 요약/스니펫 ${summary.summaryCount}개, 원출처 host ${summary.originalHosts}개`);
    lines.push(`- 신뢰도: 수집 용이성 ${summary.easeScore}/5, 매체 권위 ${summary.authorityScore}/5`);
    lines.push(`- 추가 자료: 그래프/이미지는 이번 audit에서 저장하지 않았고, 링크/스니펫 중심으로 평가`);
    lines.push(`- 메모: ${summary.memo}`);
    if (summary.samples.length) {
      lines.push(`- 샘플: ${summary.samples.slice(0, 3).map((title) => `\`${title}\``).join(' / ')}`);
    }
    lines.push('');
  }
  lines.push('## Next Actions', '');
  lines.push('- Yahoo Finance는 ticker RSS를 기본 안정 소스로 두고, news scroll은 확장 수집으로 보강한다.');
  lines.push('- Finviz News는 headline-only radar로 추가 가치가 크므로 별도 수집 단계에 넣을 만하다.');
  lines.push('- BizToc은 양이 많아 source/category/keyword 필터를 강화한 뒤 보조 풀로 둔다.');
  lines.push('- Reuters/Bloomberg/WSJ는 브라우저 자동화 차단으로 수동 확인 또는 Yahoo/Finviz/BizToc 경유 헤드라인 참조가 현실적이다.');
  return `${lines.join('\n')}\n`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const capturedAt = new Date().toISOString();
  ensureDir(args.outputDir);
  args.csvPath = path.join(args.outputDir, `${args.date}-source-collection-audit.csv`);
  args.reportPath = path.join(args.outputDir, `${args.date}-source-collection-audit.md`);
  args.jsonPath = path.join(args.outputDir, `${args.date}-source-collection-audit.json`);

  const { chromium } = await loadPlaywright();
  const context = await chromium.launchPersistentContext(path.join(projectRoot, 'runtime', 'profiles', 'source-audit'), {
    headless: !args.headed,
    channel: args.browserChannel || undefined,
    viewport: { width: 1440, height: 1100 },
    locale: 'en-US',
    colorScheme: 'light',
  });

  const sourceResults = [];
  try {
    for (const source of defaultSources) {
      const started = Date.now();
      try {
        const result = source.method === 'rss'
          ? await collectRss(source, args, capturedAt)
          : source.method === 'html'
            ? await collectHtml(source, args, capturedAt)
            : await collectBrowser(source, args, capturedAt, context);
        sourceResults.push({
          ...source,
          ...result,
          elapsedSeconds: Number(((Date.now() - started) / 1000).toFixed(2)),
        });
      } catch (error) {
        sourceResults.push({
          ...source,
          status: 'error',
          error: error.message,
          items: [],
          stopReason: 'error',
          elapsedSeconds: Number(((Date.now() - started) / 1000).toFixed(2)),
        });
      }
    }
  } finally {
    await context.close().catch(() => {});
  }

  const rows = sourceResults.flatMap((result) => result.items || []);
  const sourceSummaries = sourceResults.map((result) => {
    const score = scoreSource(result, result);
    const samples = (result.items || []).slice(0, 5).map((item) => item.title);
    return {
      id: result.id,
      label: result.label,
      status: result.status,
      stopReason: result.stopReason,
      error: result.error,
      elapsedSeconds: result.elapsedSeconds,
      samples,
      memo: sourceMemo(result, score, samples),
      ...score,
    };
  }).sort((a, b) => b.overallScore - a.overallScore || b.headlineCount - a.headlineCount);

  writeCsv(args.csvPath, rows);
  fs.writeFileSync(args.jsonPath, `${JSON.stringify({ ok: true, date: args.date, capturedAt, sourceResults, sourceSummaries }, null, 2)}\n`, 'utf8');
  fs.writeFileSync(args.reportPath, renderReport(args, capturedAt, sourceResults, rows, sourceSummaries), 'utf8');

  console.log(JSON.stringify({
    ok: true,
    date: args.date,
    row_count: rows.length,
    csv: args.csvPath,
    report: args.reportPath,
    json: args.jsonPath,
    source_summaries: sourceSummaries.map((summary) => ({
      id: summary.id,
      status: summary.status,
      headline_count: summary.headlineCount,
      summary_count: summary.summaryCount,
      overall_score: summary.overallScore,
      stop_reason: summary.stopReason,
      error: summary.error,
    })),
  }, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exit(1);
});
