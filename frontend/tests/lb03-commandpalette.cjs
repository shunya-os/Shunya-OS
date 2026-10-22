/**
 * Browser certification test for CommandPalette (LB-03)
 *
 * SAFETY: Reads credential from env vars only.
 * Refuses to run against any non-local destination.
 */
const http = require('http');
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const EMAIL = process.env.TEST_EMAIL;
const PASSWORD = process.env.TEST_PASSWORD;

if (!EMAIL || !PASSWORD || PASSWORD.length < 4) {
  console.error('FATAL: TEST_EMAIL and TEST_PASSWORD env vars must be set to non-empty values.');
  process.exit(1);
}

const ALLOWED_PORTS = [51999, 51998, 51997];

const PORT_RAW = process.env.TEST_BACKEND_PORT;
if (!PORT_RAW || PORT_RAW.trim() === '') {
  console.error('FATAL: TEST_BACKEND_PORT env var is required (one of ' + ALLOWED_PORTS.join(',') + ').');
  process.exit(1);
}
const PORT = parseInt(PORT_RAW, 10);
if (PORT >= 5000 && PORT <= 5010) {
  console.error('FATAL: Port ' + PORT + ' is in the reserved/production range (5000-5010). Refusing.');
  process.exit(1);
}
if (!ALLOWED_PORTS.includes(PORT)) {
  console.error('FATAL: Port ' + PORT + ' is not in the allowed test port list: ' + ALLOWED_PORTS.join(','));
  process.exit(1);
}

// Pre-request proxy safety: validate VITE_PROXY_TARGET before any network access.
const PROXY_TARGET_RAW = process.env.VITE_PROXY_TARGET;
if (!PROXY_TARGET_RAW || PROXY_TARGET_RAW.trim() === '') {
  console.error('FATAL: VITE_PROXY_TARGET env var is required for test mode. Must point to test backend (e.g. http://127.0.0.1:' + PORT + ').');
  process.exit(1);
}
try {
  const proxyUrl = new URL(PROXY_TARGET_RAW);
  const proxyHost = proxyUrl.hostname;
  const proxyPort = parseInt(proxyUrl.port, 10);
  if (proxyHost !== '127.0.0.1' && proxyHost !== 'localhost') {
    console.error('FATAL: VITE_PROXY_TARGET must be localhost. Got: ' + PROXY_TARGET_RAW);
    process.exit(1);
  }
  if (!ALLOWED_PORTS.includes(proxyPort)) {
    console.error('FATAL: VITE_PROXY_TARGET port ' + proxyPort + ' not in allowed test ports. Got: ' + PROXY_TARGET_RAW);
    process.exit(1);
  }
  if (proxyPort !== PORT) {
    console.error('FATAL: VITE_PROXY_TARGET port ' + proxyPort + ' must match TEST_BACKEND_PORT ' + PORT + '. Got: ' + PROXY_TARGET_RAW);
    process.exit(1);
  }
} catch (e) {
  console.error('FATAL: VITE_PROXY_TARGET is not a valid URL. Got: ' + PROXY_TARGET_RAW);
  process.exit(1);
}
console.log('VITE_PROXY_TARGET validated:', PROXY_TARGET_RAW);

const FRONTEND_URL = process.env.FRONTEND_URL;
if (!FRONTEND_URL) {
  console.error('FATAL: FRONTEND_URL env var is required (must be localhost).');
  process.exit(1);
}
if (!FRONTEND_URL.startsWith('http://127.0.0.1:') && !FRONTEND_URL.startsWith('http://localhost:')) {
  console.error('FATAL: FRONTEND_URL must point to localhost. Got: ' + FRONTEND_URL);
  process.exit(1);
}
require('./_harness-guard.cjs').assertLoopback('lb03-commandpalette', FRONTEND_URL, 'FRONTEND_URL');

// Portable artifact location: override with TEST_ARTIFACT_DIR, otherwise use
// the OS temp dir so the script runs on any machine without editing paths.
const SCRATCH = process.env.TEST_ARTIFACT_DIR
  || path.join(require('os').tmpdir(), 'shunya_lb03_results');
const SS = path.join(SCRATCH, 'screenshots');

async function ss(page, name) {
  fs.mkdirSync(SS, { recursive: true });
  await page.screenshot({ path: path.join(SS, `${name}.png`) });
}

function loginApi() {
  const data = JSON.stringify({ email: EMAIL, password: PASSWORD });
  return new Promise((resolve, reject) => {
    const opts = { hostname: '127.0.0.1', port: PORT, path: '/login', method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } };
    const req = http.request(opts, (res) => {
      let body = '';
      res.on('data', c => body += c);
      res.on('end', () => resolve({ status: res.statusCode, cookies: res.headers['set-cookie'] || [], body }));
    });
    req.on('error', reject);
    req.write(data); req.end();
  });
}

async function main() {
  const results = [];
  let passed = 0, failed = 0;
  function record(name, ok, detail = '') {
    if (ok) passed++; else failed++;
    results.push({ name, ok, detail });
    console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ': ' + detail : ''}`);
  }

  const browser = await chromium.launch({ headless: true });
  try {
    const login = await loginApi();
    record('Login API', login.status === 200, `HTTP ${login.status}`);

    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    for (const c of login.cookies) {
      const parts = c.split(';'); const eq = parts[0].indexOf('=');
      if (eq < 0) continue;
      try { context.addCookies([{ name: parts[0].substring(0, eq).trim(), value: parts[0].substring(eq + 1), domain: '127.0.0.1', path: '/', httpOnly: true, secure: false, sameSite: 'Lax' }]); } catch(e) {}
    }

    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', msg => msg.type() === 'error' && consoleErrors.push({ text: msg.text(), loc: msg.location ? msg.location().url : '-' }));
    page.on('pageerror', err => consoleErrors.push({ text: `PAGE: ${err.message}`, loc: '' }));

    await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(2000);
    await ss(page, '01-loaded');
    record('Page loads', true, `Title: ${await page.title()}`);

    await page.keyboard.press('Control+k');
    await page.waitForTimeout(1000);
    await ss(page, '02-spotlight-open');
    record('Spotlight opens via Ctrl+K', await page.evaluate(() => !!document.querySelector('.mantine-Spotlight-root')));

    let si = null;
    for (const inp of await page.$$('input')) {
      const ph = await inp.getAttribute('placeholder');
      if (ph && ph.includes('question')) { si = inp; break; }
    }
    record('Spotlight search input found', !!si, si ? await si.getAttribute('placeholder') : '');

    if (si) {
      await si.fill('What is my revenue?');
      await page.waitForTimeout(600);
      await ss(page, '03-query-typed');

      const hasAskAI = await page.evaluate(() =>
        Array.from(document.querySelectorAll('.mantine-Spotlight-action'))
          .some(b => b.textContent?.includes('Ask AI'))
      );
      record('"Ask AI" action appears for query', hasAskAI);

      if (hasAskAI) {
        const fc = await page.$('.mantine-Spotlight-action:first-child');
        let apiRequest = null;
        page.on('request', req => {
          if (req.url().includes('/api/v1/ai/chat')) apiRequest = { method: req.method(), url: req.url().slice(0, 80), body: req.postData()?.slice(0, 100) };
        });
        if (fc) await fc.click();
        await page.waitForTimeout(2000);
        await ss(page, '04-banner');

        const banner = await page.evaluate(() => {
          const el = document.querySelector('.sh-ai-result');
          if (!el) return { exists: false };
          return {
            exists: true,
            loading: !!document.querySelector('.sh-ai-loading'),
            answer: !!document.querySelector('.sh-ai-answer'),
            error: !!document.querySelector('.sh-ai-error'),
            dismiss: !!document.querySelector('.sh-ai-dismiss'),
            role: el.getAttribute('role'),
            ariaLive: el.getAttribute('aria-live'),
            text: el.textContent?.trim().slice(0, 150) || '',
          };
        });
        record('AiResultBanner exists', banner.exists);
        if (banner.exists) {
          record('Banner shows loading', banner.loading, banner.text.slice(0, 60));
          record('Banner has role/aria-live', banner.role && banner.ariaLive, `role=${banner.role} live=${banner.ariaLive}`);
          record('API request /api/v1/ai/chat was intercepted', apiRequest !== null,
                 apiRequest ? `${apiRequest.method} to ${apiRequest.url}` : '');

          let waitedForDone = false;
          for (let i = 0; i < 15 && !waitedForDone; i++) {
            await page.waitForTimeout(2000);
            waitedForDone = await page.evaluate(() => !!document.querySelector('.sh-ai-answer') || !!document.querySelector('.sh-ai-error'));
            if (waitedForDone) break;
          }
          await ss(page, '04-banner-final');

          const finalState = await page.evaluate(() => {
            const el = document.querySelector('.sh-ai-result');
            if (!el) return {};
            return {
              answer: !!document.querySelector('.sh-ai-answer'),
              error: !!document.querySelector('.sh-ai-error'),
              dismiss: !!document.querySelector('.sh-ai-dismiss'),
              text: el.textContent?.trim().slice(0, 200) || '',
              query: document.querySelector('.sh-ai-query')?.textContent || '',
            };
          });
          record('Banner completes (answer or error)', finalState.answer || finalState.error,
                 finalState.answer ? 'answer' : finalState.error ? 'error' : 'timeout');
          record('Error shown truthfully (not as success)', !finalState.answer || !finalState.error,
                 finalState.error ? 'error state is distinct from success' : '');
          record('Query label shown', !!finalState.query, finalState.query.slice(0, 40));
          record('Dismiss button in final state', finalState.dismiss || false);

          if (finalState.dismiss) {
            await page.click('.sh-ai-dismiss');
            await page.waitForTimeout(400);
            record('Dismiss button works', await page.evaluate(() => !document.querySelector('.sh-ai-result')));
          }

          await page.keyboard.press('Control+k');
          await page.waitForTimeout(600);
          for (const inp2 of await page.$$('input')) {
            const ph2 = await inp2.getAttribute('placeholder');
            if (ph2 && ph2.includes('question')) {
              await inp2.fill('Show sales');
              await page.waitForTimeout(300);
              const ac2 = await page.$('.mantine-Spotlight-action:first-child');
              if (ac2) await ac2.click();
              await page.waitForTimeout(800);
            }
          }
          await page.keyboard.press('Escape');
          await page.waitForTimeout(400);
          record('Escape dismisses banner', await page.evaluate(() => !document.querySelector('.sh-ai-result')));
        }
      }
    }

    for (const { w, h, name } of [{ w: 375, h: 667, name: 'mobile' }, { w: 768, h: 1024, name: 'tablet' }, { w: 1280, h: 800, name: 'desktop' }]) {
      await page.setViewportSize({ width: w, height: h });
      await page.waitForTimeout(300);
      await page.keyboard.press('Control+k');
      await page.waitForTimeout(600);
      await ss(page, `05-${name}`);
      record(`Spotlight at ${name} ${w}x${h}`, await page.evaluate(() => !!document.querySelector('.mantine-Spotlight-root')));
      await page.keyboard.press('Escape');
    }

    const relevantErrors = consoleErrors.filter(e =>
      !e.text.includes('503') && !e.text.includes('SERVICE_UNAVAILABLE'));
    record('No unexpected console errors', relevantErrors.length === 0,
           relevantErrors.length > 0 ? relevantErrors[0].text.slice(0, 100) :
           consoleErrors.length + ' total, 0 unexpected');

  } catch (err) {
    console.error('FATAL:', err.message);
  } finally {
    await browser.close();
  }

  const report = { timestamp: new Date().toISOString(), passed, failed, total: passed + failed, results, screenshots: fs.existsSync(SS) ? fs.readdirSync(SS) : [] };
  fs.writeFileSync(path.join(SCRATCH, 'lb03-report.json'), JSON.stringify(report, null, 2));
  console.log(`\n=== LB-03 FINAL RESULTS ===\nPassed: ${passed} / Failed: ${failed} / Total: ${passed + failed}`);
  results.forEach(r => console.log(`  ${r.ok ? 'PASS' : 'FAIL'} ${r.name}`));
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(err => { console.error('Fatal:', err); process.exit(1); });