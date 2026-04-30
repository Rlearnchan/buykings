#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(projectRoot, '..');
const defaultConfig = path.join(projectRoot, 'config', 'autopark.json');
const captureScript = path.join(projectRoot, 'scripts', 'capture_source.mjs');

function parseArgs(argv) {
  const args = {
    config: defaultConfig,
    date: new Date().toISOString().slice(0, 10),
    section: null,
    includeKnownIssues: false,
    useAuthProfiles: false,
    headed: false,
    browserChannel: null,
    bootstrap: false,
    bootstrapWaitMs: null,
    dryRun: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--config') args.config = argv[++i];
    else if (arg === '--date') args.date = argv[++i];
    else if (arg === '--section') args.section = argv[++i];
    else if (arg === '--include-known-issues') args.includeKnownIssues = true;
    else if (arg === '--use-auth-profiles') args.useAuthProfiles = true;
    else if (arg === '--headed') args.headed = true;
    else if (arg === '--browser-channel') args.browserChannel = argv[++i];
    else if (arg === '--bootstrap') {
      args.bootstrap = true;
      args.headed = true;
      args.useAuthProfiles = true;
    } else if (arg === '--bootstrap-wait-ms') args.bootstrapWaitMs = argv[++i];
    else if (arg === '--dry-run') args.dryRun = true;
    else if (arg === '--help') {
      console.log('Usage: capture_batch.mjs [--section market_now] [--date YYYY-MM-DD] [--include-known-issues] [--use-auth-profiles] [--bootstrap] [--dry-run]');
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function loadSources(configPath, args) {
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  return (config.sources || []).filter((source) => {
    if (!source.enabled) return false;
    if (args.section && source.section !== args.section) return false;
    if (!args.includeKnownIssues && source.known_capture_issue) return false;
    return true;
  });
}

function readMetadata(sourceId, date) {
  const safeId = sourceId.replace(/[^a-zA-Z0-9_-]+/g, '-');
  const metadataPath = path.join(projectRoot, 'data', 'raw', date, `${safeId}.json`);
  if (!fs.existsSync(metadataPath)) return null;
  return JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const configPath = path.resolve(repoRoot, args.config);
  const sources = loadSources(configPath, args);
  const plan = sources.map((source) => ({
    id: source.id,
    name: source.name || source.id,
    section: source.section || null,
    kind: source.kind,
    url: source.url,
  }));

  if (args.dryRun) {
    console.log(JSON.stringify({ ok: true, mode: 'dry-run', date: args.date, sources: plan }, null, 2));
    return;
  }

  const results = [];
  for (const source of sources) {
    const captureArgs = [captureScript, '--config', configPath, '--date', args.date, '--source', source.id];
    if (args.useAuthProfiles) captureArgs.push('--use-auth-profiles');
    if (args.headed) captureArgs.push('--headed');
    if (args.browserChannel) captureArgs.push('--browser-channel', args.browserChannel);
    if (args.bootstrap) captureArgs.push('--bootstrap');
    if (args.bootstrapWaitMs) captureArgs.push('--bootstrap-wait-ms', args.bootstrapWaitMs);
    const completed = spawnSync(
      process.execPath,
      captureArgs,
      { cwd: repoRoot, encoding: 'utf8' },
    );
    const metadata = readMetadata(source.id, args.date);
    results.push({
      source_id: source.id,
      exit_code: completed.status,
      status: metadata?.status || 'missing-metadata',
      screenshot_path: metadata?.screenshot_path || null,
      error: metadata?.error || null,
    });
  }

  const ok = results.every((result) => result.status === 'ok');
  console.log(JSON.stringify({ ok, date: args.date, results }, null, 2));
  if (!ok) process.exitCode = 1;
}

main();
