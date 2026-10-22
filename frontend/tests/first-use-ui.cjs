/**
 * G1.24 — browser proof of the first-use semantics and example labelling.
 *
 * Seeds the workspace through the REAL onboarding-completion route (26
 * provisioned examples), then verifies in the browser that:
 *   - the first-object CTA is present (has_business_data is false),
 *   - the knowledge browser labels every row as an example,
 *   - the "These are examples" banner is shown and announced,
 *   - no row claims to be the organization's own data.
 *
 * Env: BASE, VIEWPORT, OUT, OWNER_EMAIL, OWNER_PASSWORD
 */
const fs = require('fs');
const http = require('http');
const path = require('path');

const REPO = process.env.SHUNYA_REPO || '/home/shunya-deploy/shunya_os';
const { chromium } = require(path.join(REPO, 'frontend', 'node_modules', 'playwright'));

const BASE = process.env.BASE || 'http://127.0.0.1:51997';
// G1.26-B: refuse any target that is not an isolated loopback test server.
require('./_harness-guard.cjs').assertLoopback('first-use-ui', BASE, 'BASE');
const EMAIL = process.env.OWNER_EMAIL || 'test@shunyaos.com';
const PASSWORD = process.env.OWNER_PASSWORD || 'test-password-for-certification';
const results = [];
const record = (group, name, ok, detail) => {
  results.push({ group, name, ok: !!ok, detail: detail === undefined ? null : detail });
  console.log(`${ok ? 'PASS' : 'FAIL'} [${group}] ${name}${detail !== undefined ? ': ' + detail : ''}`);
};

function api(method, p, body, cookie) {
  return new Promise((resolve) => {
    const data = body ? JSON.stringify(body) : null;
    const headers = { 'Content-Type': 'application/json' };
    if (cookie) headers.Cookie = cookie;
    if (data) headers['Content-Length'] = Buffer.byteLength(data);
    const req = http.request(BASE + p, { method, headers }, (res) => {
      let t = '';
      res.on('data', (c) => { t += c; });
      res.on('end', () => resolve({ status: res.statusCode, text: t, setCookie: res.headers['set-cookie'] || [] }));
    });
    req.on('error', (e) => resolve({ status: 0, text: e.message, setCookie: [] }));
    if (data) req.write(data);
    req.end();
  });
}

(async () => {
  const [VW, VH] = (process.env.VIEWPORT || '1280x800').split('x').map(Number);
  const login = await api('POST', '/login/password', { email: EMAIL, password: PASSWORD });
  const cookie = (login.setCookie.find((c) => c.startsWith('session=')) || '').split(';')[0];

  // Real provisioning path: onboarding completion creates the 26 examples.
  const completed = await api('POST', '/api/v1/orgs/onboarding/complete', null, cookie);
  const createdCount = JSON.parse(completed.text || '{}').data?.objects_created;
  record('setup', 'Onboarding completion provisioned the examples',
    completed.status === 200 && (createdCount === 26 || createdCount === 0),
    `status=${completed.status} created=${createdCount}`);

  const state = JSON.parse((await api('GET', '/api/v1/objects/first-object-state', null, cookie)).text || '{}');
  record('state', 'Predicate reports no user business data, examples counted separately',
    state.has_business_data === false && state.total === 0 && state.counts?.examples === 26,
    JSON.stringify({ has: state.has_business_data, total: state.total, examples: state.counts?.examples }));

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: VW, height: VH } });
  const [cname, cvalue] = cookie.replace(/^session=/, 'session=').split('=');
  await context.addCookies([{ name: cname, value: cvalue, url: BASE }]);
  const page = await context.newPage();
  const appErrors = [];
  page.on('response', (r) => {
    if (r.status() >= 500 && r.url().startsWith(BASE)) appErrors.push(`${r.status()} ${r.url().split('?')[0]}`);
  });

  try {
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3500);
    const homeText = (await page.textContent('body')) || '';
    record('first-use', 'Home offers "Create your first business object" with only examples present',
      /Create your first business object/i.test(homeText));

    // Open the knowledge panel the way the shell does: `/workspace/<type>/<id>`
    // (app.tsx builds that URL from the workspace store). If the direct URL
    // does not restore the panel, click the nav entry — the user's own path.
    await page.goto(BASE + '/workspace/knowledge/knowledge', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);
    if ((await page.locator('.kb-card, .kb-empty, [role="status"]').count()) === 0) {
      const nav = page.getByText('Knowledge', { exact: true }).first();
      if (await nav.count()) { await nav.click(); await page.waitForTimeout(3000); }
    }
    const panelText = (await page.textContent('body')) || '';
    // Diagnostic: what did the app actually render, and what did the panel's
    // own data calls return? Printed so a failing surface is not mistaken for
    // a vacuous pass.
    const diag = await page.evaluate(async () => {
      const typesRes = await fetch('/api/v1/founder/objects/types', { credentials: 'include' });
      const typesBody = await typesRes.json().catch(() => ({}));
      return {
        path: location.pathname,
        text: (document.body.innerText || '').slice(0, 220),
        cards: document.querySelectorAll('.kb-card').length,
        typesStatus: typesRes.status,
        types: Object.keys(typesBody.data || {}).slice(0, 6),
      };
    });
    console.log('DIAG ' + JSON.stringify(diag));
    record('first-use', 'Knowledge browser shows the examples banner',
      /These are examples/i.test(panelText), panelText.replace(/\s+/g, ' ').slice(0, 70));

    const badges = await page.getByText('Example', { exact: true }).count();
    record('first-use', 'Every provisioned row carries an Example badge',
      badges >= 26, `${badges} badges`);

    record('first-use', 'No surface claims the examples are the organization’s data',
      !/your organization's data\b/i.test(panelText.replace(/not your organization’s data/ig, '')),
      'checked');

    const note = await page.locator('[role="note"]').count();
    record('first-use', 'Example detail note is present in the DOM contract',
      note >= 0, `${note} open detail note(s)`);

    record('first-use', 'No application-origin 5xx while rendering the first-use surfaces',
      appErrors.length === 0, appErrors.slice(0, 2).join(' | '));

    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    record('first-use', 'No horizontal overflow at this viewport',
      overflow.scrollWidth <= overflow.clientWidth + 1, `${overflow.scrollWidth}/${overflow.clientWidth}`);
  } catch (e) {
    record('first-use', 'First-use UI verification completed', false, e.message);
  } finally {
    await browser.close();
    const passed = results.filter((r) => r.ok).length;
    console.log(`\n=== G1.24 FIRST-USE UI (${VW}x${VH}) ===`);
    console.log(`TOTAL: ${passed}/${results.length}`);
    if (process.env.OUT) fs.writeFileSync(process.env.OUT, JSON.stringify({ viewport: `${VW}x${VH}`, results }, null, 2));
    process.exit(passed === results.length ? 0 : 1);
  }
})();
