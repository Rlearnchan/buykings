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
      console.log('Usage: summarize_capture.mjs [--date YYYY-MM-DD]');
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
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

function summarizeItem(item) {
  if (item.source_id === 'cnbc-us10y' && item.extracted?.quote) {
    const q = item.extracted.quote;
    const change = q.change == null ? '' : ` (${q.change >= 0 ? '+' : ''}${q.change})`;
    return `10년물 국채금리: ${q.yield_pct}%${change}, ${q.quote_time || 'time n/a'}`;
  }
  if (item.source_id === 'cnn-fear-greed' && item.extracted?.fear_greed) {
    const fg = item.extracted.fear_greed;
    return `CNN 공포탐욕지수: ${fg.score} (${fg.status}), 업데이트 ${fg.updated_at_text || 'n/a'}`;
  }
  return `${item.name || item.source_id}: ${item.status}`;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const items = loadMetadata(args.date);
  const okItems = items.filter((item) => item.status === 'ok');
  const blockedItems = items.filter((item) => item.status === 'blocked');
  const errorItems = items.filter((item) => item.status === 'error');
  const payload = {
    ok: true,
    date: args.date,
    counts: {
      total: items.length,
      ok: okItems.length,
      blocked: blockedItems.length,
      error: errorItems.length,
    },
    market_now_summary: okItems.map(summarizeItem),
    blocked_sources: blockedItems.map((item) => item.source_id),
    error_sources: errorItems.map((item) => ({ source_id: item.source_id, error: item.error })),
  };
  console.log(JSON.stringify(payload, null, 2));
}

main();
