/**
 * Debug - use Playwright fill() to type query
 *
 * SAFETY: Reads credential from env vars only.
 * Refuses to run against any non-local destination.
 */
const http = require('http');

const EMAIL = process.env.TEST_EMAIL;
const PASSWORD = process.env.TEST_PASSWORD;
const PORT = parseInt(process.env.TEST_BACKEND_PORT || '0', 10);

if (!EMAIL || !PASSWORD || PASSWORD.length < 4) {
  console.error('FATAL: TEST_EMAIL and TEST_PASSWORD env vars must be set to non-empty values.');
  process.exit(1);
}

const ALLOWED_PORTS = [51999, 51998, 51997];
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
  const { chromium } = require('playwright');
  const login = await loginApi();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  for (const c of login.cookies) {
    const parts = c.split(';'); const eq = parts[0].indexOf('=');
    if (eq < 0) continue;
    try { context.addCookies([{ name: parts[0].substring(0, eq).trim(), value: parts[0].substring(eq + 1), domain: '127.0.0.1', path: '/', httpOnly: true, secure: false, sameSite: 'Lax' }]); } catch(_e) {}
  }
  const page = await context.newPage();

  const logs = [];
  page.on('console', msg => { if (msg.text().includes('Ask') || msg.text().includes('action')) logs.push(msg.text()); });

  require('./_harness-guard.cjs').assertLoopback('dom-inspect', 'http://127.0.0.1:52000', 'PAGE_URL');
  await page.goto('http://127.0.0.1:52000', { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(2000);

  await page.keyboard.press('Control+k');
  await page.waitForTimeout(1000);

  const inputs = await page.$$('input');
  let spotlightInput = null;
  for (const inp of inputs) {
    const placeholder = await inp.getAttribute('placeholder');
    if (placeholder && placeholder.includes('question')) {
      spotlightInput = inp;
      break;
    }
  }

  if (spotlightInput) {
    console.log('Found spotlight input');
    await spotlightInput.fill('What is my revenue?');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const items = document.querySelectorAll('.mantine-Spotlight-action');
      return {
        count: items.length,
        allText: Array.from(items).map(b => b.textContent?.trim().slice(0, 50)),
        hasAskAI: Array.from(items).some(b => b.textContent?.includes('Ask AI')),
      };
    });
    console.log('After fill():', JSON.stringify(result));

    await spotlightInput.fill('');
    await spotlightInput.type('market');
    await page.waitForTimeout(500);

    const result2 = await page.evaluate(() => {
      const items = document.querySelectorAll('.mantine-Spotlight-action');
      return {
        count: items.length,
        allText: Array.from(items).map(b => b.textContent?.trim().slice(0, 50)),
        hasAskAI: Array.from(items).some(b => b.textContent?.includes('Ask AI')),
      };
    });
    console.log('After type():', JSON.stringify(result2));
  } else {
    console.log('Spotlight input NOT found');
    const allPlaceholders = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('input')).map(i => i.placeholder);
    });
    console.log('All input placeholders:', allPlaceholders);
  }

  await browser.close();
}

main().catch(err => console.error('FATAL:', err));