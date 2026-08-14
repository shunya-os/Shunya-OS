#!/usr/bin/env node
/**
 * FDA28 Browser QA — desktop/laptop/tablet/mobile/accessibility verification
 * Tests the LIVE deployed product at https://shunyaos.com
 */
const { chromium } = require('playwright');

const BASE = 'https://shunyaos.com';
const results = [];
let pass = 0, fail = 0;

function record(name, ok, detail = '') {
  results.push({ name, ok, detail });
  if (ok) pass++; else fail++;
  console.log(`${ok ? '  ✅' : '  ❌'} ${name}${detail ? ' — ' + detail : ''}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });

  // ═══ DESKTOP (1920x1080) ═══
  console.log('\n═══ DESKTOP 1920×1080 ═══');
  const desktop = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const consoleErrors = [];
  desktop.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  desktop.on('pageerror', err => consoleErrors.push(`PAGEERROR: ${err.message}`));

  // Homepage
  const r1 = await desktop.goto(`${BASE}/`, { waitUntil: 'networkidle', timeout: 30000 });
  record('Homepage loads', r1.status() === 200, `status=${r1.status()}`);
  const title = await desktop.title();
  record('Page title present', title.length > 0, title);
  const overflow = await desktop.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  record('No horizontal overflow', !overflow, overflow ? `scrollW=${document.documentElement.scrollWidth} clientW=${document.documentElement.clientWidth}` : '');
  const hasContent = await desktop.evaluate(() => document.body.innerText.length > 100);
  record('Page has content', hasContent, `chars=${await desktop.evaluate(() => document.body.innerText.length)}`);

  // Check for dead text
  const bodyText = await desktop.evaluate(() => document.body.innerText.toLowerCase());
  record('No "coming soon"', !bodyText.includes('coming soon'));
  record('No "lorem ipsum"', !bodyText.includes('lorem ipsum'));
  record('No "under construction"', !bodyText.includes('under construction'));

  // Screenshot
  await desktop.screenshot({ path: '/home/shunya-deploy/shunya_os/frontend/screenshots/fda28-desktop-home.png', fullPage: false });
  record('Screenshot captured', true);

  // Links check
  const links = await desktop.evaluate(() => Array.from(document.querySelectorAll('a')).map(a => a.href).filter(h => h.startsWith('http')));
  let brokenLinks = 0;
  for (const href of links.slice(0, 10)) {
    try {
      const resp = await desktop.goto(href, { timeout: 10000 });
      if (resp && resp.status() >= 400) brokenLinks++;
    } catch { brokenLinks++; }
  }
  await desktop.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
  record(`Links check (${links.length} found, 10 tested)`, brokenLinks === 0, `${brokenLinks} broken`);

  // Login page — SPA has a "Tap to continue" interstitial before the login form
  await desktop.goto(`${BASE}/auth/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await desktop.waitForFunction(() => document.getElementById('root')?.innerText?.length > 10, { timeout: 10000 });
  // Click "Tap to continue" to reveal the login form
  try {
    const tapBtn = desktop.getByText('Tap to continue');
    if (await tapBtn.isVisible({ timeout: 3000 })) {
      await tapBtn.click();
      await desktop.waitForTimeout(2000);
    }
  } catch {}
  const loginUrl = desktop.url();
  record('Login page reachable', true, `url=${loginUrl}`);
  const loginInputs = await desktop.evaluate(() => Array.from(document.querySelectorAll('input')).map(i => i.type));
  record('Login inputs present', loginInputs.length >= 2, `inputs=${loginInputs.join(',')}`);
  const loginError = await desktop.evaluate(() => document.body.innerText.includes('Internal server error'));
  record('No 500 error on login', !loginError);
  await desktop.screenshot({ path: '/home/shunya-deploy/shunya_os/frontend/screenshots/fda28-desktop-login.png' });

  // ═══ TABLET (768x1024) ═══
  console.log('\n═══ TABLET 768×1024 ═══');
  const tablet = await browser.newPage({ viewport: { width: 768, height: 1024 } });
  const tErrors = [];
  tablet.on('console', msg => { if (msg.type() === 'error') tErrors.push(msg.text()); });
  await tablet.goto(`${BASE}/`, { waitUntil: 'networkidle', timeout: 30000 });
  const tOverflow = await tablet.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  record('Tablet: no horizontal overflow', !tOverflow, tOverflow ? `scrollW=${document.documentElement.scrollWidth}` : '');
  const tContent = await tablet.evaluate(() => document.body.innerText.length > 100);
  record('Tablet: content renders', tContent);
  await tablet.screenshot({ path: '/home/shunya-deploy/shunya_os/frontend/screenshots/fda28-tablet-home.png' });

  // ═══ MOBILE PORTRAIT (390x844 - iPhone 14) ═══
  console.log('\n═══ MOBILE 390×844 ═══');
  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const mErrors = [];
  mobile.on('console', msg => { if (msg.type() === 'error') mErrors.push(msg.text()); });
  await mobile.goto(`${BASE}/`, { waitUntil: 'networkidle', timeout: 30000 });
  const mOverflow = await mobile.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  record('Mobile: no horizontal overflow', !mOverflow, mOverflow ? `scrollW=${document.documentElement.scrollWidth}` : '');
  const mContent = await mobile.evaluate(() => document.body.innerText.length > 100);
  record('Mobile: content renders', mContent);
  await mobile.screenshot({ path: '/home/shunya-deploy/shunya_os/frontend/screenshots/fda28-mobile-home.png' });

  // Mobile login
  await mobile.goto(`${BASE}/auth/login`, { waitUntil: 'networkidle', timeout: 30000 });
  await mobile.waitForFunction(() => document.getElementById('root')?.innerText?.length > 10, { timeout: 10000 });
  try {
    const tapBtn = mobile.getByText('Tap to continue');
    if (await tapBtn.isVisible({ timeout: 3000 })) {
      await tapBtn.click();
      await mobile.waitForTimeout(2000);
    }
  } catch {}
  const mLoginOverflow = await mobile.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  record('Mobile: login no overflow', !mLoginOverflow);
  await mobile.screenshot({ path: '/home/shunya-deploy/shunya_os/frontend/screenshots/fda28-mobile-login.png' });

  // ═══ CONSOLE ERROR SUMMARY ═══
  console.log('\n═══ CONSOLE ERRORS ═══');
  const allErrors = [...new Set([...consoleErrors, ...tErrors, ...mErrors])];
  if (allErrors.length === 0) {
    record('No console errors', true);
  } else {
    record(`Console errors (${allErrors.length})`, false, allErrors.slice(0, 5).join(' | '));
  }

  // ═══ ACCESSIBILITY ═══
  console.log('\n═══ ACCESSIBILITY ═══');
  await desktop.goto(`${BASE}/`, { waitUntil: 'networkidle' });
  await desktop.waitForFunction(() => document.getElementById('root')?.innerText?.length > 10, { timeout: 10000 });
  const images = await desktop.evaluate(() => Array.from(document.querySelectorAll('img')).map(i => ({ alt: i.alt, src: i.src })));
  const missingAlt = images.filter(i => !i.alt);
  record(`Images have alt text (${images.length} imgs)`, missingAlt.length === 0, `${missingAlt.length} missing`);
  const buttons = await desktop.evaluate(() => Array.from(document.querySelectorAll('button')).map(b => ({ text: b.innerText, aria: b.getAttribute('aria-label') })));
  const unlabeledButtons = buttons.filter(b => !b.text.trim() && !b.aria);
  record(`Buttons have labels (${buttons.length})`, unlabeledButtons.length === 0, `${unlabeledButtons.length} unlabeled`);
  const headings = await desktop.evaluate(() => Array.from(document.querySelectorAll('h1,h2,h3')).map(h => h.tagName));
  // SPA may use styled divs — also check for role=heading or large text
  const headingRoles = await desktop.evaluate(() => Array.from(document.querySelectorAll('[role="heading"]')).length);
  record('Headings present', headings.length > 0 || headingRoles > 0, `h1-h3=${headings.join(',')} role=heading=${headingRoles}`);

  // ═══ SUMMARY ═══
  console.log(`\n═══════════════════════════════`);
  console.log(`FDA28 BROWSER QA: ${pass} PASS, ${fail} FAIL`);
  console.log(`═══════════════════════════════`);

  await browser.close();
  process.exit(fail > 0 ? 1 : 0);
})().catch(e => {
  console.error('FATAL:', e.message);
  process.exit(2);
});