/**
 * G1.15 — Durable keyboard/focus regression for the first-object journey.
 * G1.17 — KB-01 root cause fixed in this harness (see notes below).
 * G1.18 — KB-02: the empty-state CTA source changed to the authoritative
 * predicate `GET /api/v1/objects/first-object-state`, and this harness now
 * asserts both sides of it: CTA present only when the predicate reports no
 * business data, and gone in a fresh session after a successful import.
 *
 * Keyboard-only paths: login, CTA activation, import validation + recovery,
 * relationship record opening, detail, reload persistence. Asserts visible
 * focus indicators, alert/status announcement roles, and that no mouse click is
 * required for the critical path.
 *
 * KB-01 evidence (G1.17): the recovery step used to select the import target by
 * pressing "c" on the native select. Because the select keeps the previous
 * choice across a reset, the second "c" cycled the already-selected
 * "Customers" to "Campaigns", so the valid customer CSV was submitted as a
 * campaign import and the backend truthfully rejected it ("Missing required
 * field: name"). The product was correct; the harness was not deterministic.
 * Selection is now Home + ArrowDown until the expected value is reached, and
 * the value is asserted before every submission.
 *
 * The malformed row is also typed into a cleared textarea (Ctrl+A, Backspace):
 * the paste box opens pre-filled with sample rows, so typing appended to the
 * sample instead of entering the intended malformed CSV.
 *
 * Run against the app served SAME-ORIGIN (the relationship workspace calls
 * `/relationships/api/v1/...`, which a dev proxy limited to `/api` does not
 * forward, and production nginx proxies everything to Gunicorn):
 *
 *   VIEWPORT=1280x800 node tests/keyboard-first-object.cjs
 *
 * Env: VIEWPORT (default 1280x800), FRONTEND_URL (default http://127.0.0.1:51999),
 *      BACKEND_URL (default = FRONTEND_URL) for account provisioning via API.
 */
const path = require('path');
const http = require('http');
const REPO = process.env.SHUNYA_REPO || '/home/shunya-deploy/shunya_os';
const { chromium } = require(path.join(REPO, 'frontend', 'node_modules', 'playwright'));
const BACKEND = process.env.BACKEND_URL || 'http://127.0.0.1:51999';
const BASE = process.env.FRONTEND_URL || BACKEND;
// G1.26-B: both origins are guarded — production gunicorn is also loopback:5001.
require('./_harness-guard.cjs').assertLoopback('keyboard-first-object', BASE, 'FRONTEND_URL');
require('./_harness-guard.cjs').assertLoopback('keyboard-first-object', BACKEND, 'BACKEND_URL');
const RUN = Date.now().toString(36).slice(-6);
const EMAIL = `g115kb-${RUN}@cert.local`;
// Per-run synthetic password: the account is created by this run only.
// (The repository guard forbids hard-coded password literals in tracked files.)
const PASSWORD = `G1.15-keyboard-${RUN}-pw`;
const RECORD_NAME = `KB Customer ${RUN}`;
const results = [];
const serverErrors = [];
const record = (group, n, ok, d) => {
  results.push({ group, n, ok: !!ok, detail: d === undefined ? null : d });
  console.log(`${ok ? 'PASS' : 'FAIL'} [${group}] ${n}${d !== undefined ? ': ' + d : ''}`);
};

function api(method, p, body, cookie) {
  return new Promise((resolve) => {
    const data = body ? JSON.stringify(body) : null;
    const headers = { 'Content-Type': 'application/json', Accept: 'application/json' };
    if (cookie) headers.Cookie = cookie;
    if (data) headers['Content-Length'] = Buffer.byteLength(data);
    const req = http.request(BACKEND + p, { method, headers }, (res) => {
      let t = '';
      res.on('data', (c) => { t += c; });
      res.on('end', () => resolve({ status: res.statusCode, text: t, setCookie: res.headers['set-cookie'] || [] }));
    });
    req.on('error', (e) => resolve({ status: 0, text: e.message, setCookie: [] }));
    if (data) req.write(data);
    req.end();
  });
}

async function provision() {
  await api('POST', '/api/v1/auth/signup', { name: 'G1.15 Keyboard', email: EMAIL, password: PASSWORD });
  const t = await api('GET', `/__test__/get-verify-token/${encodeURIComponent(EMAIL)}`);
  await api('POST', '/api/v1/auth/verify-email', { token: JSON.parse(t.text || '{}').verify_token || '' });
  const login = await api('POST', '/login/password', { email: EMAIL, password: PASSWORD });
  const cookie = (login.setCookie.find((c) => c.startsWith('session=')) || '').split(';')[0];
  const org = await api('POST', '/orgs', { company_name: `G1.15 KB Org ${RUN}` }, cookie);
  return login.status === 200 && org.status === 201;
}

async function focusedInfo(page) {
  return page.evaluate(() => {
    const el = document.activeElement;
    const cs = el ? getComputedStyle(el) : null;
    return {
      tag: el ? el.tagName : null,
      text: el ? (el.textContent || '').trim().slice(0, 60) : '',
      placeholder: el && el.getAttribute ? (el.getAttribute('placeholder') || '') : '',
      className: el && el.className ? String(el.className) : '',
      outlineStyle: cs ? cs.outlineStyle : null,
      outlineWidth: cs ? cs.outlineWidth : null,
      boxShadow: cs ? cs.boxShadow : null,
    };
  });
}

async function tabTo(page, predicate, max = 45) {
  for (let i = 0; i < max; i += 1) {
    await page.keyboard.press('Tab');
    const info = await focusedInfo(page);
    if (predicate(info)) return { found: true, info, tabs: i + 1 };
  }
  return { found: false, info: await focusedInfo(page), tabs: max };
}

/** Keyboard-only sign-in. Returns the URL reached. */
async function keyboardLogin(page, email, password) {
  await page.goto(BASE + '/auth/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('input[placeholder="you@company.com"]', { timeout: 30000 });
  await page.evaluate(() => document.body.focus());
  const field = await tabTo(page, (i) => i.placeholder === 'you@company.com', 15);
  if (!field.found) throw new Error('email field not reachable by Tab');
  await page.keyboard.type(email);
  await page.keyboard.press('Tab');
  await page.keyboard.type(password);
  const submit = await tabTo(page, (i) => i.tag === 'BUTTON' && /sign in/i.test(i.text), 8);
  if (!submit.found) throw new Error('sign-in button not reachable by Tab');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(3500);
  return page.url();
}

/**
 * Deterministic keyboard selection for the native target select.
 * Home → first option, then ArrowDown until the requested value is selected.
 * Typeahead ("c") is cycle-sensitive when the value is already selected and is
 * exactly what caused the KB-01 target drift.
 */
async function chooseTarget(page, wantValue) {
  const sel = page.locator('.wksp-import-form select, .wksp-import-target-row select').first();
  if (!(await sel.count())) return { ok: false, reason: 'no target select' };
  await page.keyboard.press('Home');
  for (let i = 0; i < 8; i += 1) {
    const value = await sel.inputValue();
    if (value === wantValue) {
      const label = (await sel.locator('option:checked').textContent()) || '';
      return { ok: true, value, label: label.trim() };
    }
    await page.keyboard.press('ArrowDown');
  }
  return { ok: false, value: await sel.inputValue() };
}

/**
 * Replace the textarea content using the keyboard only (no mouse).
 * The caller has already focused the textarea with Tab; the paste box opens
 * pre-filled with sample rows, so select-all + delete is required before typing.
 */
async function setCsv(page, text) {
  await page.keyboard.press('Control+a');
  await page.keyboard.press('Backspace');
  await page.keyboard.type(text);
  return page.locator('.wksp-textarea').inputValue();
}

(async () => {
  const [VW, VH] = (process.env.VIEWPORT || '1280x800').split('x').map(Number);
  const ok = await provision();
  record('setup', 'Synthetic account + org provisioned', ok);

  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: VW, height: VH } });
  const page = await ctx.newPage();
  // The empty-state CTA must only appear when the authoritative emptiness
  // predicate was fetched successfully AND reports no business data
  // (unknown ≠ empty). Capture that response so the assertion is based on the
  // server's answer, not on the CTA's presence alone.
  let firstObjectState = null;
  page.on('response', async (r) => {
    if (!r.url().endsWith('/api/v1/objects/first-object-state')) return;
    let hasBusinessData = null;
    try { const j = await r.json(); if (typeof j.has_business_data === 'boolean') hasBusinessData = j.has_business_data; } catch { /* malformed */ }
    firstObjectState = { status: r.status(), has_business_data: hasBusinessData };
  });
  // 5xx from the APPLICATION are journey failures; a blocked external host
  // (fonts, CDNs) is an environment limitation, recorded but not attributed to
  // the product. The assertion is scoped to the app origin for that reason.
  page.on('response', (r) => {
    if (r.status() < 500) return;
    if (r.url().startsWith(BASE)) serverErrors.push(`${r.status()} ${r.url()}`);
    else console.log(`NOTE external resource unavailable: ${r.status()} ${r.url().split('?')[0]}`);
  });
  try {
    // ── Keyboard-only login ────────────────────────────────────────────
    await page.goto(BASE + '/auth/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('input[placeholder="you@company.com"]', { timeout: 30000 });
    await page.evaluate(() => document.body.focus());
    const emailField = await tabTo(page, (i) => i.placeholder === 'you@company.com', 15);
    record('keyboard', 'Email field reachable by Tab', emailField.found, `${emailField.tabs} tabs`);
    await page.keyboard.type(EMAIL);
    await page.keyboard.press('Tab');
    await page.keyboard.type(PASSWORD);
    const submit = await tabTo(page, (i) => i.tag === 'BUTTON' && /sign in/i.test(i.text), 8);
    if (!submit.found) throw new Error('sign-in button not reachable by Tab');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(3500);
    record('keyboard', 'Login completed via keyboard', !page.url().includes('/auth/'), page.url());

    // ── CTA via Tab + Enter ────────────────────────────────────────────
    const cta = await tabTo(page, (i) => /Create your first business object/i.test(i.text), 60);
    // Journey step 3: the CTA is only truthful when the authoritative
    // emptiness predicate returned successfully and reported no business data.
    record('journey', 'Empty-state CTA backed by a successful, empty predicate',
      !!firstObjectState && firstObjectState.status === 200 && firstObjectState.has_business_data === false,
      JSON.stringify(firstObjectState));
    record('keyboard', 'First-object CTA reachable by Tab', cta.found, `${cta.tabs} tabs`);
    const visible = cta.info.outlineStyle !== 'none' || (cta.info.outlineWidth && cta.info.outlineWidth !== '0px') || (cta.info.boxShadow && cta.info.boxShadow !== 'none');
    record('keyboard', 'Focused CTA shows a visible focus indicator', visible,
      `outline=${cta.info.outlineStyle}/${cta.info.outlineWidth}`);
    if (!cta.found) throw new Error('first-object CTA not reachable');
    await page.keyboard.press('Enter');
    await page.waitForSelector('text=Bring Data Into SHUNYA', { timeout: 20000 });
    record('keyboard', 'Import panel opens via keyboard activation', true);

    // ── Invalid input path ─────────────────────────────────────────────
    const pasteTab = await tabTo(page, (i) => i.tag === 'BUTTON' && /Paste CSV/i.test(i.text), 25);
    record('keyboard', 'Paste CSV tab reachable by Tab', pasteTab.found);
    if (pasteTab.found) await page.keyboard.press('Enter');

    const targetTab1 = await tabTo(page, (i) => i.tag === 'SELECT', 10);
    record('keyboard', 'Target select reachable by Tab', targetTab1.found, `${targetTab1.tabs} tabs`);
    const tgt1 = await chooseTarget(page, 'customer');
    record('keyboard', 'Target select holds Customers (invalid attempt)', tgt1.ok && tgt1.value === 'customer', JSON.stringify(tgt1));

    const ta = await tabTo(page, (i) => i.tag === 'TEXTAREA', 20);
    record('keyboard', 'CSV textarea reachable by Tab', ta.found, `${ta.tabs} tabs`);
    const malformed = 'email\nonly-an-email@example.com\n';
    const typedMalformed = await setCsv(page, malformed);
    record('keyboard', 'Malformed CSV entered exactly as typed', typedMalformed === malformed, JSON.stringify(typedMalformed));

    const previewBtn = await tabTo(page, (i) => i.tag === 'BUTTON' && /Preview & Validate/i.test(i.text), 6);
    record('keyboard', 'Preview button reachable by Tab', previewBtn.found);
    if (previewBtn.found) await page.keyboard.press('Enter');
    await page.waitForTimeout(1800);
    const previewStats = await page.locator('.wksp-import-stats').textContent().catch(() => '');
    record('journey', 'Preview reports the malformed rows as invalid',
      /0 valid/.test(previewStats) && /[1-9]\d* invalid/.test(previewStats),
      (previewStats || '').replace(/\s+/g, ' ').trim().slice(0, 60));

    let importBtn = await tabTo(page, (i) => i.tag === 'BUTTON' && /^Import \d+ records?$/i.test(i.text), 8);
    if (importBtn.found) await page.keyboard.press('Enter');
    await page.waitForTimeout(2200);
    const alert = await page.locator('[role="alert"], [role="status"]').allTextContents().catch(() => []);
    const alertText = alert.join(' ').replace(/\s+/g, ' ');
    record('journey', 'Invalid import announced via alert/status region', /Import Failed|rejected|invalid|error/i.test(alertText), alertText.slice(0, 100));
    record('journey', 'Invalid import never claims success', !/Import Complete/.test(alertText));

    // ── Keyboard recovery, then a genuinely valid import ───────────────
    const more = await tabTo(page, (i) => i.tag === 'BUTTON' && /Import More Data/i.test(i.text), 60);
    record('keyboard', 'Import More Data reachable by Tab after failure', more.found, `${more.tabs} tabs`);
    if (!more.found) throw new Error('recovery control not reachable by Tab');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(700);
    const focusAfterReset = await focusedInfo(page);
    record('keyboard', 'Focus returns to the import panel after reset',
      String(focusAfterReset.className).includes('wksp-import'), focusAfterReset.className || focusAfterReset.tag);

    const targetTab2 = await tabTo(page, (i) => i.tag === 'SELECT', 12);
    record('keyboard', 'Target select reachable by Tab after reset', targetTab2.found);
    const tgt2 = await chooseTarget(page, 'customer');
    record('keyboard', 'Target select still holds Customers before valid submission',
      tgt2.ok && tgt2.value === 'customer', JSON.stringify(tgt2));

    const ta2 = await tabTo(page, (i) => i.tag === 'TEXTAREA', 20);
    record('keyboard', 'Recovery textarea reachable by Tab', ta2.found, `${ta2.tabs} tabs`);
    const validCsv = `display_name,email\n${RECORD_NAME},kb-${RUN}@cert.local\n`;
    const typedValid = await setCsv(page, validCsv);
    record('keyboard', 'Valid CSV entered exactly as typed', typedValid === validCsv, JSON.stringify(typedValid));

    const prev2 = await tabTo(page, (i) => i.tag === 'BUTTON' && /Preview & Validate/i.test(i.text), 8);
    if (prev2.found) await page.keyboard.press('Enter');
    await page.waitForTimeout(1600);
    const validStats = await page.locator('.wksp-import-stats').textContent().catch(() => '');
    record('journey', 'Valid preview accepts the record', /1 valid/.test(validStats), (validStats || '').replace(/\s+/g, ' ').trim().slice(0, 60));

    const imp2 = await tabTo(page, (i) => i.tag === 'BUTTON' && /^Import \d+ records?$/i.test(i.text), 10);
    if (imp2.found) await page.keyboard.press('Enter');
    await page.waitForTimeout(2500);
    const okText = (await page.locator('[role="status"]').allTextContents().catch(() => [])).join(' ');
    record('journey', 'Valid import completes and is announced', /Import Complete/.test(okText), okText.replace(/\s+/g, ' ').trim().slice(0, 80));

    // Backend truth, read through the product API from this browser session.
    const persisted = await page.evaluate(async (name) => {
      const r = await fetch('/relationships/api/v1/relationships?limit=100', { credentials: 'include' });
      const j = await r.json().catch(() => ({}));
      const rels = j.relationships || [];
      const hit = rels.find((x) => x.display_name === name);
      return { status: r.status, count: rels.length, id: hit ? hit.id : null };
    }, RECORD_NAME);
    record('journey', 'Created record is persisted (product API returns it)',
      persisted.status === 200 && !!persisted.id, JSON.stringify(persisted));
    if (!persisted.id) throw new Error('record not persisted; cannot continue');

    // ── Relationships via keyboard from the import result ──────────────
    const relBtn = await tabTo(page, (i) => i.tag === 'BUTTON' && /Open Relationships/i.test(i.text), 25);
    record('keyboard', 'Open Relationships reachable by Tab', relBtn.found, `${relBtn.tabs} tabs`);
    if (!relBtn.found) throw new Error('Open Relationships not reachable');
    await page.keyboard.press('Enter');
    const itemAppeared = await page.waitForSelector('.pw-commercial-item', { timeout: 15000 }).then(() => true).catch(() => false);
    record('journey', 'Relationship panel lists the imported record', itemAppeared);

    if (await page.evaluate(() => String(document.activeElement && document.activeElement.className || '').includes('pw-commercial-item'))) {
      // focus already moved into the panel — no extra Tab needed
    } else {
      await page.evaluate(() => document.body.focus());
    }
    let item = { found: false, info: { text: '', className: '' }, tabs: 0 };
    for (let i = 0; i < 80; i += 1) {
      const info = await focusedInfo(page);
      if (info.className.includes('pw-commercial-item')) { item = { found: true, info, tabs: i }; break; }
      await page.keyboard.press('Tab');
    }
    record('keyboard', 'Relationship record reachable by Tab with the imported name',
      item.found && item.info.text.includes(RECORD_NAME), item.found ? item.info.text.slice(0, 50) : 'not reached');

    if (item.found) await page.keyboard.press('Enter');
    await page.waitForTimeout(1500);
    const detail = await page.textContent('.pw-rel-detail').catch(() => '');
    record('keyboard', 'Relationship detail opens via keyboard', (detail || '').length > 0, (detail || '').replace(/\s+/g, ' ').trim().slice(0, 60));
    record('journey', 'Detail belongs to the imported record (timeline/memory shown)',
      /Timeline|AI Memory|Health:/.test(detail || ''), (detail || '').replace(/\s+/g, ' ').trim().slice(0, 80));

    // ── Reload: state persists ─────────────────────────────────────────
    const urlBeforeReload = page.url();
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(4000);
    const bodyAfter = (await page.textContent('body')) || '';
    record('journey', 'Record persists after reload', bodyAfter.includes(RECORD_NAME), page.url());

    const itemAfterReload = await page.waitForSelector('.pw-commercial-item', { timeout: 8000 }).then(() => true).catch(() => false);
    if (itemAfterReload) {
      await page.evaluate(() => document.body.focus());
      let reached = false;
      for (let i = 0; i < 80; i += 1) {
        const info = await focusedInfo(page);
        if (info.className.includes('pw-commercial-item') && info.text.includes(RECORD_NAME)) { reached = true; break; }
        await page.keyboard.press('Tab');
      }
      record('keyboard', 'Record reachable by Tab after reload', reached, urlBeforeReload);
    } else {
      record('keyboard', 'Record reachable by Tab after reload', false, 'relationship panel did not re-render');
    }

    // ── KB-02: the empty-state CTA must be gone once data exists ───────
    const stateAfter = await page.evaluate(async () => {
      const r = await fetch('/api/v1/objects/first-object-state', { credentials: 'include' });
      const j = await r.json().catch(() => ({}));
      return { status: r.status, has_business_data: j.has_business_data, counts: j.counts };
    });
    record('journey', 'Predicate reports business data after the import',
      stateAfter.status === 200 && stateAfter.has_business_data === true,
      JSON.stringify(stateAfter));

    // Fresh session (no local state), same account: the home screen must no
    // longer advertise an empty workspace.
    const freshCtx = await browser.newContext({ viewport: { width: VW, height: VH } });
    const fresh = await freshCtx.newPage();
    try {
      await keyboardLogin(fresh, EMAIL, PASSWORD);
      await fresh.waitForTimeout(2500);
      const home = await fresh.evaluate(() => ({
        path: location.pathname,
        ctaVisible: !![...document.querySelectorAll('button, [role="button"]')]
          .some((b) => /Create your first business object/i.test(b.textContent || '')),
      }));
      record('journey', 'Empty-state CTA is gone after import (fresh session)',
        !home.ctaVisible, JSON.stringify(home));
    } finally {
      await freshCtx.close();
    }

    // ── Non-functional journey assertions ──────────────────────────────
    record('journey', 'No unexpected HTTP 5xx during the journey', serverErrors.length === 0, serverErrors.slice(0, 3).join(' | '));
    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    record('journey', 'No horizontal overflow at this viewport',
      overflow.scrollWidth <= overflow.clientWidth + 1, `${overflow.scrollWidth}/${overflow.clientWidth}`);
  } catch (e) {
    record('journey', 'Journey completed without exception', false, e.message);
  } finally {
    await browser.close();
    const passed = results.filter((r) => r.ok).length;
    console.log(`\n=== G1.18 KEYBOARD + FIRST-OBJECT JOURNEY (${VW}x${VH}) ===`);
    for (const g of ['keyboard', 'journey', 'setup']) {
      const rows = results.filter((r) => r.group === g);
      if (rows.length) console.log(`${g}: ${rows.filter((r) => r.ok).length}/${rows.length}`);
    }
    console.log(`TOTAL: ${passed}/${results.length}`);
    if (process.env.RESULTS_OUT) {
      require('fs').writeFileSync(process.env.RESULTS_OUT, JSON.stringify({ viewport: `${VW}x${VH}`, email: EMAIL, results }, null, 2));
    }
    process.exit(passed === results.length ? 0 : 1);
  }
})();
