#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { chromium } from 'playwright';

const args = process.argv.slice(2);

function getArg(name, fallback = undefined) {
  const exact = args.find((arg) => arg.startsWith(`${name}=`));
  if (exact) return exact.slice(name.length + 1);
  const index = args.indexOf(name);
  if (index >= 0 && index + 1 < args.length) return args[index + 1];
  return fallback;
}

function hasFlag(name) {
  return args.includes(name);
}

const pageUrl = getArg('--page-url', 'https://wepoll.kr/g2/bbs/mypage_data.php');
const periodLabel = getArg('--period-label', '최근 3일');
const boardLabel = getArg('--board-label', '경제');
const includeLabel = getArg('--include-label', '글만');
const formatLabel = getArg('--format-label', 'CSV');
const outputDir = getArg('--output-dir');
const userDataDir = getArg('--user-data-dir');
const profileDir = getArg('--profile-dir', 'Default');
const browserPath = getArg('--browser-path');
const screenshot = getArg('--screenshot');
const headed = hasFlag('--headed');
const verbose = hasFlag('--verbose');
const allowManualLogin = hasFlag('--allow-manual-login');

function log(...messages) {
  if (verbose) {
    console.error('[wepoll-playwright]', ...messages);
  }
}

if (!outputDir) {
  console.error('Missing required argument: --output-dir');
  process.exit(1);
}

if (!userDataDir) {
  console.error('Missing required argument: --user-data-dir');
  process.exit(1);
}

fs.mkdirSync(outputDir, { recursive: true });
if (screenshot) fs.mkdirSync(path.dirname(screenshot), { recursive: true });

const context = await chromium.launchPersistentContext(userDataDir, {
  headless: !headed,
  executablePath: browserPath,
  acceptDownloads: true,
  args: [`--profile-directory=${profileDir}`],
});

try {
  log('browser launched');
  const page = context.pages()[0] ?? await context.newPage();
  log('page ready');
  await page.goto(pageUrl, { waitUntil: 'networkidle', timeout: 30000 });
  log('page loaded', page.url());

  if (page.url().includes('login')) {
    if (!allowManualLogin) {
      throw new Error(`Wepoll session is not authenticated: ${page.url()}`);
    }
    log('waiting for manual login');
    await page.waitForURL(/mypage_data\.php/, { timeout: 300000 });
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    log('manual login completed', page.url());
  }
  if (await page.getByText('로그인 하십시오.', { exact: true }).count()) {
    if (!allowManualLogin) {
      throw new Error('Wepoll session is not authenticated: login warning is visible');
    }
    log('login warning visible; waiting for manual login');
    await page.waitForURL(/mypage_data\.php/, { timeout: 300000 });
    await page.waitForLoadState('networkidle', { timeout: 30000 });
  }

  await page.getByRole('button', { name: /최근|오늘|이번|지난|기간/ }).click();
  await page.getByText(periodLabel, { exact: true }).click();
  log('period selected', periodLabel);
  await page.getByRole('radio', { name: boardLabel }).check();
  await page.getByRole('radio', { name: includeLabel }).check();
  await page.getByRole('radio', { name: formatLabel }).check();
  log('options checked');

  if (screenshot) {
    await page.screenshot({ path: screenshot, fullPage: true });
  }

  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: 30000 }),
    page.getByRole('button', { name: /다운로드/ }).click(),
  ]);
  log('download event received');

  const target = path.resolve(outputDir, download.suggestedFilename());
  await download.saveAs(target);

  console.log(
    JSON.stringify(
      {
        ok: true,
        pageUrl: page.url(),
        downloadedFile: target,
        suggestedFilename: download.suggestedFilename(),
        periodLabel,
        boardLabel,
        includeLabel,
        formatLabel,
      },
      null,
      2,
    ),
  );
} finally {
  await context.close();
}
