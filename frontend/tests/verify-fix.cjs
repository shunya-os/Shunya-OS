/**
 * Quick test: verify duplicate-key warning is gone after fix
 *
 * SAFETY: Reads credential from env vars only.
 * Refuses to run against any non-local destination.
 */
const http = require('http');
const { chromium } = require('playwright');

const EMAIL = process.env.TEST_EMAIL;
const PASSWORD = process.env.TEST_PASSWORD;
const PORT = parseInt(process.env.TEST_BACKEND_PORT || '0', 10);

// ── Credential safety ──
if (!EMAIL || !PASSWORD || PASSWORD.length < 4) {
  console.error('FATAL: TEST_EMAIL and TEST_PASSWORD env vars must be set to non-empty values.');
  console.error('Test refuses to run with hardcoded or empty credentials.');
  process.exit(1);
}

// ── Destination safety: only localhost:PORT is allowed ──
const ALLOWED_PORTS = [51999, 51998, 51997];  // isolated test ports only
if (PORT === 0) {
  console.error('FATAL: TEST_BACKEND_PORT env var is required (one of ' + ALLOWED_PORTS.join(',') + ').');
  process.exit(1);
}
if (PORT >= 5000 && PORT <= 5010) {
  console.error('FATAL: Port ' + PORT + ' is in the reserved/production range (5000-5010). Refusing.');
  process.exit(1);
}
if (!ALLOWED_PORTS.includes(PORT)) {
  console.error('FATAL: Port ' + PORT + ' is not in the allowed test port list: ' + ALLOWED_PORTS.join(','));
  process.exit(1);
}
// loginApi only connects to 127.0.0.1 — no hostname from env. This is intentional
// to prevent credential-bearing requests from leaving the local machine.

// ── Frontend destination safety ──
const FRONTEND_URL = process.env.FRONTEND_URL;
if (!FRONTEND_URL) {
  console.error('FATAL: FRONTEND_URL env var is required (must start with http://127.0.0.1: or http://localhost:).');
  process.exit(1);
}
if (!FRONTEND_URL.startsWith('http://127.0.0.1:') && !FRONTEND_URL.startsWith('http://localhost:')) {
  console.error('FATAL: FRONTEND_URL must point to localhost (127.0.0.1 or localhost). Got: ' + FRONTEND_URL);
  process.exit(1);
}
require('./_harness-guard.cjs').assertLoopback('verify-fix', FRONTEND_URL, 'FRONTEND_URL');

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
  const browser = await chromium.launch({ headless: true });
  let exitCode = 0;
  try {
    const login = await loginApi();

    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    for (const c of login.cookies) {
      const parts = c.split(';'); const eq = parts[0].indexOf('=');
      if (eq < 0) continue;
      try { context.addCookies([{ name: parts[0].substring(0, eq).trim(), value: parts[0].substring(eq + 1), domain: '127.0.0.1', path: '/', httpOnly: true, secure: false, sameSite: 'Lax' }]); } catch(_e) {}
    }

    const page = await context.newPage();
    const warnings = [];
    page.on('console', msg => {
      if (msg.text().includes('same key')) warnings.push(msg.text());
    });
    page.on('pageerror', err => warnings.push(`PAGE: ${err.message}`));

    await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(2000);

    for (let i = 0; i < 3; i++) {
      await page.keyboard.press('Control+k');
      await page.waitForTimeout(500);
      const si = await page.$('input[placeholder*="question"]');
      if (si) {
        await si.fill('What is revenue?');
        await page.waitForTimeout(300);
        await si.fill('Show sales');
        await page.waitForTimeout(300);
        await si.fill('');
        await page.waitForTimeout(200);
      }
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    }

    const duplicateKeyWarnings = warnings.filter(w => w.includes('same key'));
    console.log('Duplicate key warnings after fix:', duplicateKeyWarnings.length);
    if (duplicateKeyWarnings.length > 0) {
      console.log('ISSUE: ' + duplicateKeyWarnings.length + ' duplicate-key warnings detected');
      exitCode = 1;
    } else {
      console.log('OK: No duplicate-key warnings');
    }
    console.log('Total console messages:', warnings.length);
  } catch (err) {
    console.error('FATAL:', err.message);
    exitCode = 1;
  } finally {
    await browser.close();
    process.exit(exitCode);
  }
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });