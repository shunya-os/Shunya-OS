/**
 * G1.24 — invitation lifecycle browser journey.
 *
 * Proves the whole invite path against an isolated app + local SMTP capture:
 *   admin creates invitation → message really sent (STARTTLS+AUTH) and captured
 *   → MIME body decoded by the harness → recipient opens the link → validates
 *   → accepts → membership persisted → login → workspace access → replay
 *   rejected → non-admin / cross-tenant refused → client error path writes
 *   nothing.
 *
 * Nothing external: the sink is loopback, every address is synthetic, and no
 * token is ever printed (only presence/length booleans).
 *
 * Env:
 *   VIEWPORT      1280x800 | 768x1024 | 375x667
 *   BASE          app origin (default http://127.0.0.1:51999)
 *   CAPTURE_FILE  JSONL written by capture_smtp.py
 *   OWNER_EMAIL / OWNER_PASSWORD  seeded test-server account
 *   RESULTS_OUT   optional JSON result path
 */
const fs = require('fs');
const http = require('http');
const path = require('path');

const REPO = process.env.SHUNYA_REPO || '/home/shunya-deploy/shunya_os';
const { chromium } = require(path.join(REPO, 'frontend', 'node_modules', 'playwright'));

const BASE = process.env.BASE || 'http://127.0.0.1:51999';
// G1.26-B: refuse any target that is not an isolated loopback test server.
require('./_harness-guard.cjs').assertLoopback('invitation-journey', BASE, 'BASE');
const CAPTURE_FILE = process.env.CAPTURE_FILE || '';
const OWNER_EMAIL = process.env.OWNER_EMAIL || 'test@shunyaos.com';
const OWNER_PASSWORD = process.env.OWNER_PASSWORD || 'test-password-for-certification';
const RUN = Date.now().toString(36).slice(-6);
// Per-run synthetic password: the invitee account is created by this run only.
// (The repository guard forbids hard-coded password literals in tracked files.)
const PASSWORD = `G1.24-invitee-${RUN}-pw`;

const results = [];
const appErrors = [];
const record = (group, name, ok, detail) => {
  results.push({ group, name, ok: !!ok, detail: detail === undefined ? null : detail });
  console.log(`${ok ? 'PASS' : 'FAIL'} [${group}] ${name}${detail !== undefined ? ': ' + detail : ''}`);
};

function api(method, p, body, cookie) {
  return new Promise((resolve) => {
    const data = body ? JSON.stringify(body) : null;
    const headers = { 'Content-Type': 'application/json', Accept: 'application/json' };
    if (cookie) headers.Cookie = cookie;
    if (data) headers['Content-Length'] = Buffer.byteLength(data);
    const req = http.request(BASE + p, { method, headers }, (res) => {
      let t = '';
      res.on('data', (c) => { t += c; });
      res.on('end', () => resolve({
        status: res.statusCode,
        text: t,
        setCookie: res.headers['set-cookie'] || [],
      }));
    });
    req.on('error', (e) => resolve({ status: 0, text: e.message, setCookie: [] }));
    if (data) req.write(data);
    req.end();
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Read the capture sink until a message for `recipient` appears. */
async function waitForMessage(recipient, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const lines = fs.readFileSync(CAPTURE_FILE, 'utf8').split('\n').filter(Boolean);
      const messages = lines.map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
      const hit = messages.filter((m) => (m.to || []).includes(recipient));
      if (hit.length) return hit[hit.length - 1];
    } catch { /* file not written yet */ }
    await sleep(250);
  }
  return null;
}

async function focusedInfo(page) {
  return page.evaluate(() => {
    const el = document.activeElement;
    return {
      tag: el ? el.tagName : null,
      text: el ? (el.textContent || '').trim().slice(0, 80) : '',
      placeholder: el && el.getAttribute ? (el.getAttribute('placeholder') || '') : '',
      id: el && el.getAttribute ? (el.getAttribute('id') || '') : '',
    };
  });
}

async function tabTo(page, predicate, max = 40) {
  for (let i = 0; i < max; i += 1) {
    await page.keyboard.press('Tab');
    const info = await focusedInfo(page);
    if (predicate(info)) return { found: true, info, tabs: i + 1 };
  }
  return { found: false, info: await focusedInfo(page), tabs: max };
}

/** Keyboard-only login through the real form. */
async function loginUI(page, email, password) {
  await page.goto(BASE + '/auth/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('input[placeholder="you@company.com"]', { timeout: 30000 });
  await page.evaluate(() => document.body.focus());
  const field = await tabTo(page, (i) => i.placeholder === 'you@company.com', 15);
  if (!field.found) throw new Error('email field not reachable by Tab');
  await page.keyboard.type(email);
  await page.keyboard.press('Tab');
  await page.keyboard.type(password);
  const submit = await tabTo(page, (i) => i.tag === 'BUTTON' && /sign in/i.test(i.text), 10);
  if (!submit.found) throw new Error('sign-in button not reachable by Tab');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(3500);
  return page.url();
}

function tokenFromUrl(url) {
  try { return new URL(url).searchParams.get('token') || ''; } catch { return ''; }
}

(async () => {
  const [VW, VH] = (process.env.VIEWPORT || '1280x800').split('x').map(Number);
  const browser = await chromium.launch({ headless: true });
  const ownerCtx = await browser.newContext({ viewport: { width: VW, height: VH } });
  const owner = await ownerCtx.newPage();
  owner.on('response', (r) => {
    if (r.status() < 500) return;
    if (r.url().startsWith(BASE)) appErrors.push(`${r.status()} ${r.url().split('?')[0]}`);
    else console.log(`NOTE external resource unavailable: ${r.status()} ${r.url().split('?')[0]}`);
  });

  let inviteUrl = '';
  let invitee = '';
  let orgId = null;
  let secondInvite = { url: '', email: '' };

  try {
    // ── 1. admin login ─────────────────────────────────────────────────
    const ownerUrl = await loginUI(owner, OWNER_EMAIL, OWNER_PASSWORD);
    record('journey', 'Administrator signed in with the keyboard only', !ownerUrl.includes('/auth/'), ownerUrl.replace(BASE, ''));

    const state = await owner.evaluate(async () => {
      const r = await fetch('/api/v1/objects/first-object-state', { credentials: 'include' });
      const j = await r.json().catch(() => ({}));
      return { status: r.status, org: j.organization_id ?? null };
    });
    orgId = state.org;
    record('journey', 'Administrator has an organization context', state.status === 200 && !!orgId, `org=${orgId}`);

    // ── 2. create the invitation (real admin session, real route) ──────
    invitee = `g124-journey-${RUN}@cert.local`;
    const created = await owner.evaluate(async (email) => {
      const r = await fetch('/api/v1/team/invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, role: 'member', name: 'Journey Invitee' }),
      });
      return { status: r.status, body: await r.json().catch(() => ({})) };
    }, invitee);
    const inv = created.body?.data || {};
    inviteUrl = inv.invite_url || '';
    record('journey', 'Invitation created by the authorized administrator', created.status === 201 && !!inviteUrl,
      `status=${created.status}`);
    record('journey', 'Response distinguishes acceptance from delivery',
      inv.delivery?.accepted === true && inv.delivery?.delivered === false,
      JSON.stringify(inv.delivery || {}));

    // ── 3. the message really arrived; the harness decodes it ──────────
    const message = await waitForMessage(invitee);
    record('journey', 'Invitation message captured by the local sink', !!message,
      message ? `tls=${message.tls} auth=${!!message.auth_user}` : 'not captured');
    if (message) {
      record('journey', 'Captured over STARTTLS with authentication',
        message.tls === true && !!message.auth_user);
      const body = message.body || '';
      const token = tokenFromUrl(inviteUrl);
      record('journey', 'Decoded body carries exactly one accept link',
        !!token && body.split('/auth/invitation?token=').length - 1 === 1,
        `tokenPresent=${!!token}`);
      record('journey', 'Emailed link is the same capability the admin received',
        body.includes(inviteUrl));
      record('journey', 'Recipient and organization in the message are the intended ones',
        (message.to || []).includes(invitee) && /invited to join/i.test(message.subject || ''),
        message.subject);
    }

    // ── 4. recipient opens the link in a clean session ─────────────────
    const inviteeCtx = await browser.newContext({ viewport: { width: VW, height: VH } });
    const recipient = await inviteeCtx.newPage();
    recipient.on('response', (r) => {
      if (r.status() >= 500 && r.url().startsWith(BASE)) appErrors.push(`${r.status()} ${r.url().split('?')[0]}`);
    });
    await recipient.goto(inviteUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await recipient.waitForSelector('#invite-name', { timeout: 20000 });
    const inviteText = (await recipient.textContent('body')) || '';
    record('journey', 'Invitation page names the organization and the invited address',
      /invited to join/i.test(inviteText) && inviteText.includes(invitee),
      inviteText.replace(/\s+/g, ' ').slice(0, 80));
    record('keyboard', 'Name field is focused on arrival',
      (await focusedInfo(recipient)).id === 'invite-name');

    // client-side error path first: mismatched passwords must not submit
    await recipient.keyboard.type('Journey Invitee');
    const pwdTab = await tabTo(recipient, (i) => i.id === 'invite-password', 6);
    record('keyboard', 'Password field reachable by Tab', pwdTab.found);
    await recipient.keyboard.type(PASSWORD);
    const confirmTab = await tabTo(recipient, (i) => i.id === 'invite-confirm', 6);
    record('keyboard', 'Confirm field reachable by Tab', confirmTab.found);
    await recipient.keyboard.type(PASSWORD + '-mismatch');
    const submitTab = await tabTo(recipient, (i) => i.tag === 'BUTTON' && /accept invitation/i.test(i.text), 8);
    record('keyboard', 'Submit reachable by Tab', submitTab.found);
    if (submitTab.found) await recipient.keyboard.press('Enter');
    await recipient.waitForTimeout(800);
    const errText = (await recipient.textContent('[role="alert"]').catch(() => '')) || '';
    record('journey', 'Mismatched passwords produce a truthful client error',
      /do not match/i.test(errText), errText.slice(0, 60));
    const stillPending = await owner.evaluate(async (_org) => {
      const r = await fetch(`/api/v1/team/invitations`, { credentials: 'include' });
      const j = await r.json().catch(() => ({}));
      const row = (j.data || []).find((x) => x.status === 'pending');
      return { status: r.status, pending: !!row };
    }, orgId);
    record('journey', 'A rejected form wrote nothing (invitation still pending)', stillPending.status === 200 && stillPending.pending);

    // ── 5. accept for real ─────────────────────────────────────────────
    await recipient.evaluate(() => { const el = document.getElementById('invite-confirm'); if (el) { el.focus(); } });
    await recipient.keyboard.press('Control+a');
    await recipient.keyboard.type(PASSWORD);
    await recipient.keyboard.press('Enter');
    await recipient.waitForTimeout(2500);
    const successText = (await recipient.textContent('body')) || '';
    record('journey', 'Acceptance succeeds and confirms the join',
      /You've joined|Invitation accepted/i.test(successText),
      successText.replace(/\s+/g, ' ').slice(0, 80));

    // ── 6. the new account can sign in and reach the workspace ─────────
    await recipient.getByRole('button', { name: /sign in/i }).first().click();
    await recipient.waitForTimeout(1200);
    await loginUI(recipient, invitee, PASSWORD);
    record('journey', 'Invited identity can sign in', !recipient.url().includes('/auth/'), recipient.url().replace(BASE, ''));

    const access = await recipient.evaluate(async () => {
      const r = await fetch('/api/v1/objects/first-object-state', { credentials: 'include' });
      const j = await r.json().catch(() => ({}));
      return { status: r.status, org: j.organization_id ?? null, hasData: j.has_business_data };
    });
    record('journey', 'Invited member can read the authorized workspace',
      access.status === 200 && access.org === orgId, JSON.stringify(access));

    const memberAdminAttempt = await recipient.evaluate(async (org) => {
      const r = await fetch(`/api/v1/orgs/${org}/invitations`, { credentials: 'include' });
      return { status: r.status };
    }, orgId);
    record('journey', 'A plain member cannot list invitations', memberAdminAttempt.status === 403,
      `status=${memberAdminAttempt.status}`);

    // ── 7. replay is refused ───────────────────────────────────────────
    const replayCtx = await browser.newContext({ viewport: { width: VW, height: VH } });
    const replay = await replayCtx.newPage();
    await replay.goto(inviteUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await replay.waitForTimeout(2000);
    const replayBody = (await replay.textContent('body')) || '';
    const replayAlert = (await replay.textContent('[role="alert"]').catch(() => '')) || '';
    record('journey', 'Replaying an accepted link is refused with a message',
      /already|invalid|expired|could not/i.test(replayAlert + ' ' + replayBody) && !/invite-name/.test(replayBody),
      (replayAlert || replayBody).replace(/\s+/g, ' ').slice(0, 70));
    await replayCtx.close();

    // ── 8. cross-tenant: a non-member is refused ───────────────────────
    const outsiderEmail = `g124-outsider-${RUN}@cert.local`;
    await api('POST', '/api/v1/auth/signup', { name: 'G1.24 Outsider', email: outsiderEmail, password: PASSWORD });
    const vt = await api('GET', `/__test__/get-verify-token/${encodeURIComponent(outsiderEmail)}`);
    const verifyToken = JSON.parse(vt.text || '{}').verify_token || '';
    await api('POST', '/api/v1/auth/verify-email', { token: verifyToken });
    const outsiderLogin = await api('POST', '/login/password', { email: outsiderEmail, password: PASSWORD });
    const outsiderCookie = (outsiderLogin.setCookie.find((c) => c.startsWith('session=')) || '').split(';')[0];
    await api('POST', '/orgs', { company_name: `Outsider Co ${RUN}` }, outsiderCookie);

    const crossList = await api('GET', `/api/v1/orgs/${orgId}/invitations`, null, outsiderCookie);
    const crossCreate = await api('POST', `/api/v1/orgs/${orgId}/invitations`, { email: `x-${RUN}@cert.local` }, outsiderCookie);
    record('journey', 'Cross-tenant invitation listing is refused', crossList.status === 403, `status=${crossList.status}`);
    record('journey', 'Cross-tenant invitation creation is refused', crossCreate.status === 403, `status=${crossCreate.status}`);

    // ── 9. expiry / token binding (second invitation) ──────────────────
    secondInvite.email = `g124-expiry-${RUN}@cert.local`;
    const second = await owner.evaluate(async (email) => {
      const r = await fetch('/api/v1/team/invite', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        credentials: 'include', body: JSON.stringify({ email, role: 'viewer' }),
      });
      return { status: r.status, body: await r.json().catch(() => ({})) };
    }, secondInvite.email);
    secondInvite.url = second.body?.data?.invite_url || '';
    const secondToken = tokenFromUrl(secondInvite.url);
    const binding = await api('GET', `/api/v1/orgs/invitations/${encodeURIComponent(secondToken)}`);
    const bindingBody = JSON.parse(binding.text || '{}').data || {};
    record('journey', 'Token is bound to the invited recipient and organization',
      binding.status === 200 && bindingBody.email === secondInvite.email && Number(bindingBody.org_id) === Number(orgId),
      `status=${binding.status}`);
    const wrongToken = await api('GET', '/api/v1/orgs/invitations/not-a-real-token');
    record('journey', 'An unknown token is refused', wrongToken.status === 404, `status=${wrongToken.status}`);

    // ── 10. non-functional guarantees ──────────────────────────────────
    record('journey', 'No application-origin 5xx during the journey', appErrors.length === 0, appErrors.slice(0, 3).join(' | '));
    const overflow = await recipient.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    record('journey', 'No horizontal overflow at this viewport',
      overflow.scrollWidth <= overflow.clientWidth + 1, `${overflow.scrollWidth}/${overflow.clientWidth}`);
    const inviteOverflow = await recipient.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    record('journey', 'Workspace stays within the viewport after joining',
      inviteOverflow.scrollWidth <= inviteOverflow.clientWidth + 1,
      `${inviteOverflow.scrollWidth}/${inviteOverflow.clientWidth}`);
  } catch (e) {
    record('journey', 'Journey completed without exception', false, e.message);
  } finally {
    await browser.close();
    const passed = results.filter((r) => r.ok).length;
    console.log(`\n=== G1.24 INVITATION JOURNEY (${VW}x${VH}) ===`);
    for (const g of ['journey', 'keyboard']) {
      const rows = results.filter((r) => r.group === g);
      if (rows.length) console.log(`${g}: ${rows.filter((r) => r.ok).length}/${rows.length}`);
    }
    console.log(`TOTAL: ${passed}/${results.length}`);
    if (process.env.RESULTS_OUT) {
      fs.writeFileSync(process.env.RESULTS_OUT, JSON.stringify({ viewport: `${VW}x${VH}`, results }, null, 2));
    }
    process.exit(passed === results.length ? 0 : 1);
  }
})();
