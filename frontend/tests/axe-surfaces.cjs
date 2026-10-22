/**
 * G1.24 — automated accessibility scan of the changed surfaces.
 *
 * Surfaces: sign-in, invitation acceptance (valid token), first-use home
 * (examples-only workspace), and the knowledge browser (example badges +
 * "These are examples" banner).
 *
 * Automated axe results are a floor, not a conformance claim: manual
 * assistive-technology testing is still outstanding and is reported as such.
 *
 * Env: BASE (default http://127.0.0.1:51997), OUT (JSON path), TOKEN optional.
 */
const fs = require('fs');
const http = require('http');
const path = require('path');

const REPO = process.env.SHUNYA_REPO || '/home/shunya-deploy/shunya_os';
const { chromium } = require(path.join(REPO, 'frontend', 'node_modules', 'playwright'));
const AXE = path.join(REPO, 'frontend', 'node_modules', 'axe-core', 'axe.min.js');

const BASE = process.env.BASE || 'http://127.0.0.1:51997';
// G1.26-B: refuse any target that is not an isolated loopback test server.
require('./_harness-guard.cjs').assertLoopback('axe-surfaces', BASE, 'BASE');
const EMAIL = process.env.OWNER_EMAIL || 'test@shunyaos.com';
const PASSWORD = process.env.OWNER_PASSWORD || 'test-password-for-certification';
const RUN = Date.now().toString(36).slice(-6);

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
  const login = await api('POST', '/login/password', { email: EMAIL, password: PASSWORD });
  const cookie = (login.setCookie.find((c) => c.startsWith('session=')) || '').split(';')[0];
  const invitee = `g124-axe-${RUN}@cert.local`;
  const created = await api('POST', '/api/v1/team/invite', { email: invitee, role: 'viewer' }, cookie);
  const inviteUrl = (JSON.parse(created.text || '{}').data || {}).invite_url || '';
  if (!inviteUrl) {
    console.error('could not create an invitation for the scan');
    process.exit(2);
  }

  const browser = await chromium.launch({ headless: true });
  const report = {};
  // Evidence artifacts must never carry a capability token.
  const safeUrl = (u) => u.replace(BASE, '').replace(/([?&]token=)[^&]+/i, '$1<redacted>');

  async function scan(name, url, { authenticated = false, after, expectText } = {}) {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 800 },
      ignoreHTTPSErrors: true,
    });
    if (authenticated) {
      const cookies = cookie.split(';').map((c) => c.trim());
      const [cname, cvalue] = cookies[0].split('=');
      await context.addCookies([{ name: cname, value: cvalue, url: BASE }]);
    }
    const page = await context.newPage();
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2500);
    if (after) await after(page);
    // Precondition: an empty shell also scans clean, so a surface that failed to
    // render would look like a pass. Require the expected content first.
    if (expectText) {
      const text = (await page.textContent('body')) || '';
      if (!expectText.test(text)) {
        report[name] = { url: safeUrl(url), violation: 0, surfaceMissing: true, saw: text.replace(/\s+/g, ' ').slice(0, 120) };
        console.log(`FAIL [axe] ${name}: expected surface content not rendered (scan would be vacuous) — saw: ${text.replace(/\s+/g, ' ').slice(0, 100)}`);
        await context.close();
        return;
      }
    }
    await page.addScriptTag({ path: AXE });
    const results = await page.evaluate(async () => {
      // eslint-disable-next-line no-undef
      return await axe.run(document, {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
      });
    });
    report[name] = {
      url: safeUrl(url),
      violations: results.violations.length,
      ids: results.violations.map((v) => `${v.id}(${v.nodes.length})`),
      incomplete: results.incomplete.length,
    };
    console.log(`${results.violations.length === 0 ? 'PASS' : 'FAIL'} [axe] ${name}: ${results.violations.length} violation(s)`
      + (results.violations.length ? ' — ' + report[name].ids.join(', ') : ''));
    await context.close();
  }

  try {
    await scan('sign-in', BASE + '/auth/login', {
      expectText: /sign in/i,
      after: async (page) => {
        await page.waitForSelector('input[placeholder="you@company.com"]', { timeout: 20000 }).catch(() => {});
        await page.waitForTimeout(600);
      },
    });
    await scan('invitation', inviteUrl, { expectText: /invited to join/i });
    await scan('home-first-use', BASE + '/', {
      authenticated: true,
      expectText: /Create your first business object/i,
    });
    await scan('knowledge-examples', BASE + '/workspace/knowledge/knowledge', {
      authenticated: true,
      expectText: /These are examples/i,
    });
  } catch (e) {
    report.error = e.message;
    console.error('axe run failed:', e.message);
  } finally {
    await browser.close();
    if (process.env.OUT) fs.writeFileSync(process.env.OUT, JSON.stringify(report, null, 2));
    const failures = Object.values(report).filter(
      (r) => r && (r.surfaceMissing || r.violations > 0)).length;
    process.exit(failures === 0 && !report.error ? 0 : 1);
  }
})();
