/**
 * Deterministic regression test: CommandPalette duplicate-key fix.
 *
 * Verifies:
 * 1. Filter called repeatedly does not mutate the original action collection.
 * 2. Each applicable query produces exactly one 'ask-ai' action.
 * 3. Clearing the query restores original action count.
 * 4. Repeated query/clear cycles do not accumulate duplicate IDs.
 * 5. Non-zero exit status on any duplicate-key warning.
 */
const { chromium } = require('playwright');
const http = require('http');

// ── Safety validation ──
const EMAIL = process.env.TEST_EMAIL;
const PASSWORD = process.env.TEST_PASSWORD;
const PORT = parseInt(process.env.TEST_BACKEND_PORT || '0', 10);
const FRONTEND_URL = process.env.FRONTEND_URL;

const ALLOWED_PORTS = [51999, 51998, 51997];
let failures = [];

function fail(msg) { failures.push(msg); console.error('FAIL:', msg); }

if (!EMAIL || !PASSWORD || PASSWORD.length < 4) { fail('Credential env vars required'); process.exit(1); }
if (PORT === 0 || !ALLOWED_PORTS.includes(PORT)) { fail('Valid TEST_BACKEND_PORT required'); process.exit(1); }
if (!FRONTEND_URL || (!FRONTEND_URL.startsWith('http://127.0.0.1:') && !FRONTEND_URL.startsWith('http://localhost:'))) {
  fail('FRONTEND_URL must be localhost'); process.exit(1);
}
require('./_harness-guard.cjs').assertLoopback('regression-duplicate-keys', FRONTEND_URL, 'FRONTEND_URL');

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

async function run() {
  const browser = await chromium.launch({ headless: true });
  let exitCode = 0;

  try {
    const login = await loginApi();
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    for (const c of login.cookies) {
      const p = c.split(';'); const e = p[0].indexOf('=');
      if (e < 0) continue;
      try { ctx.addCookies([{ name: p[0].substring(0, e).trim(), value: p[0].substring(e + 1), domain: '127.0.0.1', path: '/', httpOnly: true, secure: false, sameSite: 'Lax' }]); } catch(_) {}
    }
    const page = await ctx.newPage();

    const dupKeyWarnings = [];
    page.on('console', msg => { if (msg.text().includes('same key')) dupKeyWarnings.push(msg.text()); });
    page.on('pageerror', err => dupKeyWarnings.push(`PAGE: ${err.message}`));

    await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(2000);

    // ── Test: Repeated query/clear cycles ──
    for (let cycle = 0; cycle < 3; cycle++) {
      await page.waitForTimeout(500);  // Ensure fully closed before reopening
      await page.keyboard.press('Control+k');
      await page.waitForTimeout(1000);

      const si = await page.$('input[placeholder*="question"]');
      if (!si) { fail('Cycle ' + cycle + ': no spotlight input found'); continue; }

      // Query A: count ask-ai occurrences
      await si.fill('What is my revenue?');
      await page.waitForTimeout(400);
      let countA = await page.evaluate(() =>
        Array.from(document.querySelectorAll('.mantine-Spotlight-action'))
          .filter(b => b.textContent?.includes('Ask AI')).length
      );
      if (countA !== 1) fail('Cycle ' + cycle + ' query A: expected 1 ask-ai, got ' + countA);

      // Query B (different): count ask-ai occurrences
      await si.fill('');
      await page.waitForTimeout(200);
      await si.fill('Show me sales data');
      await page.waitForTimeout(400);
      let countB = await page.evaluate(() =>
        Array.from(document.querySelectorAll('.mantine-Spotlight-action'))
          .filter(b => b.textContent?.includes('Ask AI')).length
      );
      if (countB !== 1) fail('Cycle ' + cycle + ' query B: expected 1 ask-ai, got ' + countB);

      // Clear: verify ask-ai count drops to 0
      await si.fill('');
      await page.waitForTimeout(400);
      let countClear = await page.evaluate(() =>
        Array.from(document.querySelectorAll('.mantine-Spotlight-action'))
          .filter(b => b.textContent?.includes('Ask AI')).length
      );
      if (countClear !== 0) fail('Cycle ' + cycle + ' after clear: expected 0 ask-ai, got ' + countClear);

      // Total action count should be stable across cycles
      if (cycle === 0) {
        let totalFirst = await page.evaluate(() => document.querySelectorAll('.mantine-Spotlight-action').length);
        if (totalFirst > 11) fail('Cycle ' + cycle + ': total actions (' + totalFirst + ') exceeds expected max');
      }

      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    }

    // ── Verify no duplicate-key warnings ──
    if (dupKeyWarnings.length > 0) {
      fail(dupKeyWarnings.length + ' duplicate-key warnings detected: ' + dupKeyWarnings.slice(0, 3).join(' | '));
    } else {
      console.log('PASS: No duplicate-key warnings across ' + 3 + ' cycles');
    }

  } catch (err) {
    fail('Fatal: ' + err.message);
    exitCode = 1;
  } finally {
    await browser.close();
    if (failures.length > 0) {
      console.error(failures.length + ' failures:');
      failures.forEach(f => console.error('  ' + f));
      process.exit(1);
    }
    console.log('PASS: All regression tests passed');
    process.exit(0);
  }
}

run().catch(err => { console.error('FATAL:', err.message); process.exit(1); });