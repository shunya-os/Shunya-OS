/**
 * G1.1-R19 — Isolated CommandPalette E2E browser test.
 *
 * Uses only synthetic test credentials and isolated local provider.
 * Verifies success-path AI response rendered in the CommandPalette.
 */
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

// ── Config (all from env, no defaults) ──
const EMAIL = process.env.TEST_EMAIL;
const PASSWORD = process.env.TEST_PASSWORD;
const PORT = parseInt(process.env.TEST_BACKEND_PORT || '0', 10);
const FRONTEND_URL = process.env.FRONTEND_URL;
// Portable artifact location: override with TEST_ARTIFACT_DIR, otherwise use
// the OS temp dir so the script runs on any machine without editing paths.
const SCRATCH = process.env.TEST_ARTIFACT_DIR
  || path.join(require('os').tmpdir(), 'shunya_r19_results');
const SS = path.join(SCRATCH, 'screenshots');

const ALLOWED_PORTS = [51999, 51998, 51997];
let failures = [];
function fail(msg) { failures.push(msg); console.error('FAIL:', msg); }

// ── Safety validation ──
if (!EMAIL || !PASSWORD || PASSWORD.length < 4) { fail('Credential env vars required'); process.exit(1); }
if (PORT === 0 || !ALLOWED_PORTS.includes(PORT)) { fail('Valid TEST_BACKEND_PORT required'); process.exit(1); }
if (!FRONTEND_URL || (!FRONTEND_URL.startsWith('http://127.0.0.1:') && !FRONTEND_URL.startsWith('http://localhost:'))) {
  fail('FRONTEND_URL must be localhost'); process.exit(1);
}
require('./_harness-guard.cjs').assertLoopback('r19-e2e', FRONTEND_URL, 'FRONTEND_URL');

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
    // 1. Login
    const login = await loginApi();
    record('Synthetic user login', login.status === 200, `HTTP ${login.status}`);

    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    for (const c of login.cookies) {
      const parts = c.split(';'); const eq = parts[0].indexOf('=');
      if (eq < 0) continue;
      try { context.addCookies([{ name: parts[0].substring(0, eq).trim(), value: parts[0].substring(eq + 1), domain: '127.0.0.1', path: '/', httpOnly: true, secure: false, sameSite: 'Lax' }]); } catch(_) {}
    }

    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', msg => msg.type() === 'error' && consoleErrors.push(msg.text()));
    page.on('pageerror', err => consoleErrors.push(`PAGE: ${err.message}`));

    let interceptedResponse = null;
    page.on('response', resp => {
      if (resp.url().includes('/api/v1/ai/chat')) {
        resp.json().then(j => { interceptedResponse = j; }).catch(() => {});
      }
    });

    // 2. Load page
    await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(2000);
    await ss(page, '01-loaded');
    record('Page loads', true);

    // 3. Open CommandPalette
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(1000);
    await ss(page, '02-spotlight-open');
    const open = await page.evaluate(() => !!document.querySelector('.mantine-Spotlight-root'));
    record('Spotlight opens via Ctrl+K', open);

    // 4. Find search input
    let si = null;
    for (const inp of await page.$$('input')) {
      const ph = await inp.getAttribute('placeholder');
      if (ph && ph.includes('question')) { si = inp; break; }
    }
    record('Search input found', !!si);

    if (si) {
      // 5. Type query
      await si.fill('Hello');
      await page.waitForTimeout(600);
      await ss(page, '03-typed-hello');
      const hasAskAI = await page.evaluate(() =>
        Array.from(document.querySelectorAll('.mantine-Spotlight-action'))
          .some(b => b.textContent?.includes('Ask AI'))
      );
      record('"Ask AI: Hello" action appears', hasAskAI);

      // 6. Submit query
      if (hasAskAI) {
        const firstAction = await page.$('.mantine-Spotlight-action:first-child');
        if (firstAction) await firstAction.click();
        await page.waitForTimeout(5000);  // Wait for kernel processing
        await ss(page, '04-banner');

        // 7. Check banner
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
            text: el.textContent?.trim() || '',
          };
        });
        record('AiResultBanner appears', banner.exists);
        if (banner.exists) {
          record('Banner shows loading/answer/error', banner.loading || banner.answer || banner.error,
                 `loading:${banner.loading} answer:${banner.answer} error:${banner.error}`);
          record('Banner has role/aria-live', banner.role && banner.ariaLive,
                 `role=${banner.role} live=${banner.ariaLive}`);
          record('Dismiss button visible', banner.dismiss);

          // Wait for completion
          for (let i = 0; i < 10; i++) {
            const done = await page.evaluate(() =>
              !!document.querySelector('.sh-ai-answer') ||
              !!document.querySelector('.sh-ai-error')
            );
            if (done) break;
            await page.waitForTimeout(2000);
          }
          await ss(page, '04-banner-final');

          const final = await page.evaluate(() => {
            const el = document.querySelector('.sh-ai-result');
            if (!el) return {};
            return {
              answer: !!document.querySelector('.sh-ai-answer'),
              error: !!document.querySelector('.sh-ai-error'),
              dismiss: !!document.querySelector('.sh-ai-dismiss'),
              text: el.textContent?.trim() || '',
              query: document.querySelector('.sh-ai-query')?.textContent || '',
            };
          });
          record('Banner completes', final.answer || final.error,
                 final.answer ? 'answer' : final.error ? 'error' : 'timeout');
          record('Answer shows AI content', final.answer && final.text.includes('SHUNYA'),
                 final.answer ? final.text.slice(0, 80) : '');

          // Verify intercepted response matches local provider
          if (interceptedResponse) {
            const hasContent = interceptedResponse.content && interceptedResponse.content.includes('SHUNYA');
            record('API response contains local provider content', hasContent,
                   interceptedResponse.content?.slice(0, 60) || '');
          }

          // Dismiss
          if (final.dismiss) {
            await page.click('.sh-ai-dismiss');
            await page.waitForTimeout(400);
            record('Dismiss works', await page.evaluate(() => !document.querySelector('.sh-ai-result')));
          }
        }
      }
    }

    // 8. Responsive
    for (const { w, h, name } of [{ w: 375, h: 667, name: 'mobile' }, { w: 768, h: 1024, name: 'tablet' }]) {
      await page.setViewportSize({ width: w, height: h });
      await page.waitForTimeout(300);
      await page.keyboard.press('Control+k');
      await page.waitForTimeout(600);
      await ss(page, `05-${name}`);
      record(`Spotlight at ${name} ${w}x${h}`,
             await page.evaluate(() => !!document.querySelector('.mantine-Spotlight-root')));
      await page.keyboard.press('Escape');
    }

    // 9. Console errors
    const relevant = consoleErrors.filter(e => !e.includes('503') && !e.includes('SERVICE'));
    record('No unexpected console errors', relevant.length === 0,
           relevant.length > 0 ? relevant[0].slice(0, 80) : '');

  } catch (err) {
    fail('Fatal: ' + err.message);
  } finally {
    await browser.close();
  }

  // 10. Report
  const report = { timestamp: new Date().toISOString(), passed, failed, total: passed + failed, results };
  fs.writeFileSync(path.join(SCRATCH, 'r19-report.json'), JSON.stringify(report, null, 2));
  console.log(`\n=== R19 ISOLATED E2E ===\nPassed: ${passed} / Failed: ${failed} / Total: ${passed + failed}`);
  results.forEach(r => console.log(`  ${r.ok ? 'PASS' : 'FAIL'} ${r.name}`));
  if (failures.length) {
    console.error('FATAL ERRORS:', failures);
    process.exit(1);
  }
  process.exit(failures.length > 0 ? 1 : 0);
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });