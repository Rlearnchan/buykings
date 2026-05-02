#!/usr/bin/env node

import fs from 'node:fs';
import http from 'node:http';
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

const config = {
  pageUrl: getArg('--page-url', 'https://wepoll.kr/g2/bbs/mypage_data.php'),
  userDataDir: getArg('--user-data-dir'),
  browserPath: getArg('--browser-path'),
  host: getArg('--host', '127.0.0.1'),
  port: Number(getArg('--port', '8777')),
  headed: hasFlag('--headed'),
  allowManualLogin: hasFlag('--allow-manual-login'),
  verbose: hasFlag('--verbose'),
};

if (!config.userDataDir) {
  console.error('Missing required argument: --user-data-dir');
  process.exit(1);
}

function log(...messages) {
  if (config.verbose) {
    console.error('[wepoll-fetcher]', ...messages);
  }
}

function json(res, statusCode, payload) {
  res.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(payload, null, 2));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', (chunk) => {
      raw += chunk;
    });
    req.on('end', () => resolve(raw));
    req.on('error', reject);
  });
}

function visibleLoginWarning(page) {
  return page.getByText('로그인 하십시오.', { exact: true }).count();
}

async function ensureAuthenticated(page, { interactive = false } = {}) {
  if (!page.url().includes('login') && !(await visibleLoginWarning(page))) {
    return true;
  }
  if (!interactive) {
    return false;
  }
  if (!config.allowManualLogin) {
    return false;
  }
  log('waiting for manual login');
  await page.waitForURL((url) => {
    const href = url.toString();
    return href.includes('wepoll.kr') && !href.includes('nid.naver.com');
  }, { timeout: 600000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 });
  if (!page.url().includes('mypage_data.php')) {
    await page.goto(config.pageUrl, { waitUntil: 'networkidle', timeout: 30000 });
  }
  log('manual login completed', page.url());
  return true;
}

async function waitForDownload(page, job) {
  const periodLabel = job.periodLabel ?? '최근 3일';
  const boardLabel = job.boardLabel ?? '경제';
  const includeLabel = job.includeLabel ?? '글만';
  const formatLabel = job.formatLabel ?? 'CSV';
  const outputDir = path.resolve(job.outputDir);
  const dateFrom = job.dateFrom;
  const dateTo = job.dateTo;

  fs.mkdirSync(outputDir, { recursive: true });

  await page.goto(config.pageUrl, { waitUntil: 'networkidle', timeout: 30000 });
  const authenticated = await ensureAuthenticated(page, { interactive: false });
  if (!authenticated) {
    throw new Error(`Wepoll session is not authenticated: ${page.url()}`);
  }

  if (dateFrom && dateTo) {
    await page.evaluate(({ dateFrom, dateTo }) => {
      const setDate = (name, value) => {
        const input = document.querySelector(`input[name="${name}"]`);
        if (!input) {
          throw new Error(`missing date input: ${name}`);
        }
        input.value = value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      };
      setDate('date_from', dateFrom);
      setDate('date_to', dateTo);
    }, { dateFrom, dateTo });
    await page.getByRole('radio', { name: boardLabel }).check();
    await page.getByRole('radio', { name: includeLabel }).check();
    await page.getByRole('radio', { name: formatLabel }).check();
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 30000 }),
      page.getByRole('button', { name: /다운로드/ }).click(),
    ]);
    const downloadedFile = path.join(outputDir, download.suggestedFilename());
    await download.saveAs(downloadedFile);
    return {
      ok: true,
      page_url: page.url(),
      downloaded_file: downloadedFile,
      suggested_filename: download.suggestedFilename(),
      period_label: periodLabel,
      date_from: dateFrom,
      date_to: dateTo,
      board_label: boardLabel,
      include_label: includeLabel,
      format_label: formatLabel,
    };
  }

  await page.getByRole('button', { name: /최근|오늘|이번|지난|기간/ }).click();
  await page.getByText(periodLabel, { exact: true }).click();
  await page.getByRole('radio', { name: boardLabel }).check();
  await page.getByRole('radio', { name: includeLabel }).check();
  await page.getByRole('radio', { name: formatLabel }).check();

  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: 30000 }),
    page.getByRole('button', { name: /다운로드/ }).click(),
  ]);

  const downloadedFile = path.join(outputDir, download.suggestedFilename());
  await download.saveAs(downloadedFile);

  return {
    ok: true,
    page_url: page.url(),
    downloaded_file: downloadedFile,
    suggested_filename: download.suggestedFilename(),
    period_label: periodLabel,
    board_label: boardLabel,
    include_label: includeLabel,
    format_label: formatLabel,
  };
}

const context = await chromium.launchPersistentContext(config.userDataDir, {
  headless: !config.headed,
  executablePath: config.browserPath,
  acceptDownloads: true,
});

const page = context.pages()[0] ?? await context.newPage();
log('browser launched');
await page.goto(config.pageUrl, { waitUntil: 'networkidle', timeout: 30000 });
await ensureAuthenticated(page, { interactive: true });
log('fetcher ready', page.url());

let activeDownload = false;

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/health') {
      await page.goto(config.pageUrl, { waitUntil: 'networkidle', timeout: 30000 });
      const authenticated = !page.url().includes('login') && !(await visibleLoginWarning(page));
      return json(res, 200, {
        ok: true,
        authenticated,
        page_url: page.url(),
        active_download: activeDownload,
      });
    }

    if (req.method === 'GET' && req.url === '/debug') {
      await page.goto(config.pageUrl, { waitUntil: 'networkidle', timeout: 30000 });
      const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch((error) => String(error));
      const buttons = await page.locator('button').allTextContents().catch(() => []);
      const inputs = await page.locator('input').evaluateAll((nodes) =>
        nodes.map((node) => ({
          type: node.getAttribute('type'),
          name: node.getAttribute('name'),
          value: node.getAttribute('value'),
          checked: Boolean(node.checked),
        })),
      ).catch(() => []);
      return json(res, 200, {
        ok: true,
        page_url: page.url(),
        body_text: bodyText.slice(0, 5000),
        buttons,
        inputs,
      });
    }

    if (req.method === 'POST' && req.url === '/download') {
      if (activeDownload) {
        return json(res, 409, {
          ok: false,
          error: 'download_already_in_progress',
        });
      }

      const raw = await readBody(req);
      const job = raw ? JSON.parse(raw) : {};
      if (!job.outputDir) {
        return json(res, 400, {
          ok: false,
          error: 'missing_output_dir',
        });
      }

      activeDownload = true;
      try {
        const result = await waitForDownload(page, job);
        return json(res, 200, result);
      } finally {
        activeDownload = false;
      }
    }

    return json(res, 404, {
      ok: false,
      error: 'not_found',
    });
  } catch (error) {
    activeDownload = false;
    return json(res, 500, {
      ok: false,
      error: error instanceof Error ? error.message : String(error),
      page_url: page.url(),
    });
  }
});

server.listen(config.port, config.host, () => {
  console.log(
    JSON.stringify(
      {
        ok: true,
        message: 'wepoll fetcher daemon started',
        host: config.host,
        port: config.port,
        page_url: page.url(),
      },
      null,
      2,
    ),
  );
});

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, async () => {
    log('shutting down', signal);
    server.close();
    await context.close();
    process.exit(0);
  });
}
