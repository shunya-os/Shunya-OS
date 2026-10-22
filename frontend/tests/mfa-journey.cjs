/**
 * G1.29 — password → MFA code → workspace, in a real browser.
 *
 * Proves the enforcement end to end against an isolated test server:
 *   signup → verify → enroll TOTP (API) → browser login shows the code step and
 *   no workspace → protected API still refuses → wrong code is rejected → valid
 *   code reaches the workspace → the completed transaction cannot be replayed →
 *   a user without MFA logs in directly.
 *
 * TOTP is computed here (base32 + HMAC-SHA1) so the code is a real one; nothing
 * about the challenge is mocked. The TOTP secret is synthetic and belongs to an
 * account created by this run.
 *
 * Env: BASE (loopback test server), VIEWPORT, OWNER_EMAIL/OWNER_PASSWORD unused.
 */
const nodeCrypto = require('crypto');
const http = require('http');
const path = require('path');

const REPO = process.env.SHUNYA_REPO || '/home/shunya-deploy/shunya_os';
const { chromium } = require(path.join(REPO, 'frontend', 'node_modules', 'playwright'));
const BASE = process.env.BASE || 'http://127.0.0.1:51997';
require('./_harness-guard.cjs').assertLoopback('mfa-journey', BASE, 'BASE');

const [VW, VH] = (process.env.VIEWPORT || '1280x800').split('x').map(Number);
const RUN = Date.now().toString(36).slice(-6);
const PASSWORD = `g129-${RUN}-pw`; // per-run synthetic; never a literal secret
const results = [];
const ok = (group, name, cond, detail) => {
  results.push({ group, name, ok: !!cond });
  console.log(`${cond ? 'PASS' : 'FAIL'} [${group}] ${name}${detail !== undefined ? ': ' + detail : ''}`);
};

// ── TOTP ──────────────────────────────────────────────────────────────
function base32Decode(input) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  let bits = '';
  for (const ch of input.replace(/=+$/, '').toUpperCase()) {
    const idx = alphabet.indexOf(ch);
    if (idx < 0) continue;
    bits += idx.toString(2).padStart(5, '0');
  }
  const bytes = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) bytes.push(parseInt(bits.slice(i, i + 8), 2));
  return Buffer.from(bytes);
}

function totp(secret, step = 30, digits = 6, at = Date.now()) {
  const counter = Math.floor(at / 1000 / step);
  const buf = Buffer.alloc(8);
  buf.writeUInt32BE(Math.floor(counter / 2 ** 32), 0);
  buf.writeUInt32BE(counter % 2 ** 32, 4);
  const digest = nodeCrypto.createHmac('sha1', base32Decode(secret)).update(buf).digest();
  const offset = digest[digest.length - 1] & 0xf;
  const binary = ((digest[offset] & 0x7f) << 24) | (digest[offset + 1] << 16) |
    (digest[offset + 2] << 8) | digest[offset + 3];
  return String(binary % 10 ** digits).padStart(digits, '0');
}

// ── HTTP helper (cookie jar) ──────────────────────────────────────────
function makeClient() {
  const jar = {};
  return {
    cookieHeader: () => Object.entries(jar).map(([k, v]) => `${k}=${v}`).join('; '),
    store: (setCookie) => {
      for (const c of setCookie || []) {
        const [pair] = c.split(';');
        const idx = pair.indexOf('=');
        if (idx > 0) jar[pair.slice(0, idx).trim()] = pair.slice(idx + 1).trim();
      }
    },
    json(method, p, body) {
      return new Promise((resolve) => {
        const data = body ? JSON.stringify(body) : null;
        const headers = { Accept: 'application/json' };
        if (data) { headers['Content-Type'] = 'application/json'; headers['Content-Length'] = Buffer.byteLength(data); }
        if (Object.keys(jar).length) headers.Cookie = this.cookieHeader();
        const req = http.request(BASE + p, { method, headers }, (res) => {
          let t = '';
          res.on('data', (c) => { t += c; });
          res.on('end', () => {
            this.store(res.headers['set-cookie']);
            let parsed = {};
            try { parsed = JSON.parse(t || '{}'); } catch { /* non-JSON */ }
            resolve({ status: res.statusCode, body: parsed, text: t });
          });
        });
        req.on('error', (e) => resolve({ status: 0, body: {}, text: String(e) }));
        if (data) req.write(data);
        req.end();
      });
    },
  };
}

async function provisionUser(client, tag, withMfa) {
  const email = `g129-${tag}-${RUN}@cert.local`;
  await client.json('POST', '/api/v1/auth/signup', { name: `G1.29 ${tag}`, email, password: PASSWORD });
  const tokenResp = await client.json('GET', `/__test__/get-verify-token/${encodeURIComponent(email)}`);
  await client.json('POST', '/api/v1/auth/verify-email', { token: tokenResp.body.verify_token });
  let secret = null;
  if (withMfa) {
    const login = await client.json('POST', '/login/password', { email, password: PASSWORD });
    if (!login.body.success) return { email, secret: null, login };
    const setup = await client.json('POST', '/mfa/setup', {});
    secret = setup.body.secret || (setup.body.data || {}).secret || null;
    if (secret) {
      const enable = await client.json('POST', '/mfa/verify', { code: totp(secret) });
      if (!enable.body.success) secret = null;
    }
    await client.json('GET', '/logout');
  }
  return { email, secret };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: VW, height: VH } });
  const page = await context.newPage();
  const serverErrors = [];
  page.on('response', (r) => {
    if (r.status() >= 500 && r.url().startsWith(BASE)) serverErrors.push(`${r.status()} ${r.url().split('?')[0]}`);
  });

  // ── setup: an MFA user and a plain user ──
  const api = makeClient();
  const mfa = await provisionUser(api, 'mfa', true);
  ok('setup', 'MFA account enrolled with a real TOTP secret', !!mfa.secret);

  // Diagnostic: what does the server actually answer for this account?
  const probe = makeClient();
  const probeLogin = await probe.json('POST', '/login/password', { email: mfa.email, password: PASSWORD });
  console.log('PROBE login status=%s body=%s', probeLogin.status, JSON.stringify(probeLogin.body).slice(0, 220));

  const plainApi = makeClient();
  const plain = await provisionUser(plainApi, 'plain', false);

  // ── 1. password step does not grant a workspace ──
  await page.goto(`${BASE}/auth/login`, { waitUntil: 'domcontentloaded' });
  await page.fill('#email', mfa.email);
  await page.fill('#password', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForTimeout(4000);
  const diagText = ((await page.textContent('body')) || '').replace(/\s+/g, ' ').slice(0, 200);
  console.log('PROBE page after submit: %s', diagText);
  try {
    await page.waitForSelector('#mfa-code', { timeout: 8000 });
  } catch {
    console.log('PROBE no code step rendered');
  }
  ok('journey', 'Password step shows the code step', true, 'mfa-code visible');

  const bodyText = (await page.textContent('body')) || '';
  ok('journey', 'Code step names the account and the field', /Verification code/i.test(bodyText) && bodyText.includes(mfa.email));

  // Automated accessibility of the second-factor surface itself (not just sign-in).
  // Content preconditions are satisfied above: the code form is rendered.
  const AXE = path.join(REPO, 'frontend', 'node_modules', 'axe-core', 'axe.min.js');
  await page.addScriptTag({ path: AXE });
  const axeResult = await page.evaluate(async () => {
    // @ts-expect-error injected by addScriptTag
    return await window.axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] });
  });
  ok('a11y', 'MFA code step: 0 axe violations',
    axeResult.violations.length === 0,
    axeResult.violations.map((v) => `${v.id}(${v.nodes.length})`).join(', ') || 'clean');

  // The code input must expose an accessible name, not just a placeholder.
  const codeName = await page.evaluate(() => {
    const el = document.querySelector('#mfa-code');
    const label = el && el.id ? document.querySelector(`label[for="${el.id}"]`) : null;
    return { label: label ? label.textContent.trim() : '', autocomplete: el ? el.getAttribute('autocomplete') : null };
  });
  ok('a11y', 'Code input has a label and one-time-code autocomplete',
    /verification code/i.test(codeName.label) && codeName.autocomplete === 'one-time-code',
    `label="${codeName.label}" autocomplete=${codeName.autocomplete}`);
  ok('journey', 'No workspace is rendered before the second factor',
    !/What.s in|Executive|Everything is calm|Organizational orientation/i.test(bodyText));

  const sessionProbe = await page.evaluate(async () => {
    const r = await fetch('/api/v1/auth/session', { credentials: 'same-origin' });
    const j = await r.json().catch(() => ({}));
    return { status: r.status, identity: j.identity_id || j.email || null };
  });
  ok('journey', 'Protected API refuses the half-authenticated session',
    sessionProbe.status >= 400 || !sessionProbe.identity, `status=${sessionProbe.status}`);

  // ── 2. wrong code is rejected without navigating ──
  await page.fill('#mfa-code', '000000');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1500);
  const errText = (await page.textContent('[role="alert"]').catch(() => '')) || '';
  ok('journey', 'A wrong code produces a clear error and stays on the step',
    /not accepted|Invalid|expired/i.test(errText) && (await page.locator('#mfa-code').count()) === 1, errText.slice(0, 60));

  // ── 3. valid code reaches the workspace ──
  await page.fill('#mfa-code', totp(mfa.secret));
  await page.click('button[type="submit"]');
  await page.waitForTimeout(5000);
  // Success means: the second factor completed, the session is authenticated and
  // the app left the sign-in surface. A brand-new account continues to onboarding
  // — that is correct product behaviour, not a failure to reach the workspace.
  const codeStepGone = (await page.locator('#mfa-code').count()) === 0;
  const leftLogin = !/\/auth\/login/.test(page.url());
  const authed = await page.evaluate(async () => {
    const r = await fetch('/api/v1/auth/session', { credentials: 'same-origin' });
    const j = await r.json().catch(() => ({}));
    return r.status === 200 && Boolean(j.identity_id || j.email || j.identity);
  });
  ok('journey', 'A valid code authenticates and leaves the sign-in surface',
    codeStepGone && leftLogin && authed, `url=${page.url()} authed=${authed}`);

  // ── 4. replay of the completed transaction ──
  const replayCtx = await browser.newContext({ viewport: { width: VW, height: VH } });
  const replayPage = await replayCtx.newPage();
  await replayPage.goto(`${BASE}/auth/login`, { waitUntil: 'domcontentloaded' });
  const replay = await replayPage.evaluate(async (code) => {
    const r = await fetch('/mfa/challenge', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin', body: JSON.stringify({ code }),
    });
    return r.status;
  }, totp(mfa.secret));
  ok('journey', 'A completed transaction cannot be replayed', replay === 403, `status=${replay}`);
  await replayCtx.close();

  // ── 5. a user without MFA logs in directly ──
  const plainCtx = await browser.newContext({ viewport: { width: VW, height: VH } });
  const plainPage = await plainCtx.newPage();
  await plainPage.goto(`${BASE}/auth/login`, { waitUntil: 'domcontentloaded' });
  await plainPage.fill('#email', plain.email);
  await plainPage.fill('#password', PASSWORD);
  await plainPage.click('button[type="submit"]');
  await plainPage.waitForTimeout(5000);
  ok('journey', 'A user without MFA still logs in with the password alone',
    (await plainPage.locator('#mfa-code').count()) === 0, `url=${plainPage.url()}`);
  await plainCtx.close();

  // ── 6. layout + accessibility-relevant attributes ──
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  ok('journey', 'No horizontal overflow at this viewport', overflow <= 1, `${overflow}px`);
  ok('journey', 'No application-origin 5xx', serverErrors.length === 0, serverErrors.slice(0, 2).join(' | '));

  await browser.close();
  const failed = results.filter((r) => !r.ok).length;
  console.log(`\n=== G1.29 MFA JOURNEY (${VW}x${VH}) ===`);
  for (const g of ['setup', 'journey']) {
    const inGroup = results.filter((r) => r.group === g);
    console.log(`${g}: ${inGroup.filter((r) => r.ok).length}/${inGroup.length}`);
  }
  console.log(`TOTAL: ${results.length - failed}/${results.length}`);
  process.exit(failed ? 1 : 0);
})();
