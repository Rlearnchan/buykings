#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');

function parseArgs(argv) {
  const args = {
    date: new Date().toISOString().slice(0, 10),
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--date') args.date = argv[++i];
    else if (arg === '--help') {
      console.log('Usage: build_morning_inputs.mjs [--date YYYY-MM-DD]');
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function loadMetadata(date) {
  const rawDir = path.join(projectRoot, 'data', 'raw', date);
  if (!fs.existsSync(rawDir)) return [];
  return fs
    .readdirSync(rawDir)
    .filter((name) => name.endsWith('.json'))
    .sort()
    .map((name) => JSON.parse(fs.readFileSync(path.join(rawDir, name), 'utf8')));
}

function formatKoreanDate(date) {
  const [year, month, day] = date.split('-');
  return `${year.slice(2)}.${month}.${day}`;
}

function summarizeItem(item) {
  if (item.source_id === 'cnbc-us10y' && item.extracted?.quote) {
    const q = item.extracted.quote;
    const change = q.change == null ? '' : ` (${q.change >= 0 ? '+' : ''}${q.change})`;
    return {
      label: '10년물 국채금리',
      summary: `${q.yield_pct}%${change}`,
      detail: `시각 ${q.quote_time || 'n/a'}, 전일 종가 ${q.yield_prev_close_pct ?? 'n/a'}%`,
    };
  }
  if (item.source_id === 'cnn-fear-greed' && item.extracted?.fear_greed) {
    const fg = item.extracted.fear_greed;
    return {
      label: 'CNN 공포탐욕지수',
      summary: `${fg.score} (${fg.status})`,
      detail: `업데이트 ${fg.updated_at_text || 'n/a'}`,
    };
  }
  return {
    label: item.name || item.source_id,
    summary: item.status,
    detail: item.error || item.capture_notes || '',
  };
}

function buildPayload(date, items) {
  const okItems = items.filter((item) => item.status === 'ok');
  const blockedItems = items.filter((item) => item.status === 'blocked');
  const errorItems = items.filter((item) => item.status === 'error');
  return {
    date,
    title: formatKoreanDate(date),
    generated_at: new Date().toISOString(),
    status_counts: {
      total: items.length,
      ok: okItems.length,
      blocked: blockedItems.length,
      error: errorItems.length,
    },
    market_now: okItems.map((item) => ({
      source_id: item.source_id,
      name: item.name,
      url: item.final_url || item.configured_url,
      screenshot_path: item.screenshot_path,
      captured_at: item.captured_at,
      extracted: item.extracted || {},
      ...summarizeItem(item),
    })),
    capture_issues: [...blockedItems, ...errorItems].map((item) => ({
      source_id: item.source_id,
      name: item.name,
      status: item.status,
      url: item.final_url || item.configured_url,
      screenshot_path: item.screenshot_path,
      issue: item.error || item.capture_notes || item.title || '',
    })),
  };
}

function markdownForPayload(payload) {
  const lines = [];
  lines.push(`# ${payload.title}`);
  lines.push('');
  lines.push(`최종 수정 일시: ${payload.generated_at}`);
  lines.push('');
  lines.push('## 주요 뉴스 요약');
  lines.push('');
  if (payload.market_now.length === 0) {
    lines.push('- 아직 정상 수집된 market_now 항목이 없습니다.');
  } else {
    for (const item of payload.market_now) {
      lines.push(`- ${item.label}: ${item.summary}`);
    }
  }
  lines.push('');
  lines.push('## 자료 수집');
  lines.push('');
  lines.push('### 시장은 지금');
  lines.push('');
  for (const item of payload.market_now) {
    lines.push(`#### ${item.label}`);
    lines.push('');
    lines.push(`- 요약: ${item.summary}`);
    if (item.detail) lines.push(`- 세부: ${item.detail}`);
    lines.push(`- 출처: ${item.url}`);
    lines.push(`- 캡처: ${item.screenshot_path}`);
    lines.push('');
  }
  lines.push('## 파이프라인 점검 메모');
  lines.push('');
  lines.push(`- 정상 수집: ${payload.status_counts.ok}`);
  lines.push(`- 차단: ${payload.status_counts.blocked}`);
  lines.push(`- 오류: ${payload.status_counts.error}`);
  for (const issue of payload.capture_issues) {
    lines.push(`- ${issue.name}: ${issue.status} (${issue.source_id})`);
  }
  lines.push('');
  return `${lines.join('\n')}\n`;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const items = loadMetadata(args.date);
  const payload = buildPayload(args.date, items);

  const processedDir = path.join(projectRoot, 'data', 'processed', args.date);
  const notionDir = path.join(projectRoot, 'runtime', 'notion', args.date);
  ensureDir(processedDir);
  ensureDir(notionDir);

  const jsonPath = path.join(processedDir, 'morning_inputs.json');
  const markdownPath = path.join(notionDir, `${payload.title}.md`);
  fs.writeFileSync(jsonPath, `${JSON.stringify(payload, null, 2)}\n`);
  fs.writeFileSync(markdownPath, markdownForPayload(payload));

  console.log(
    JSON.stringify(
      {
        ok: true,
        date: args.date,
        json_path: path.relative(projectRoot, jsonPath),
        markdown_path: path.relative(projectRoot, markdownPath),
        status_counts: payload.status_counts,
      },
      null,
      2,
    ),
  );
}

main();
