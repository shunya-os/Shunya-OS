/**
 * SHUNYA OS — C-07 Accessibility Audit
 * Comprehensive axe-core scan via Playwright
 *
 * Scans: unauthenticated pages (/, /login, /pricing)
 *        authenticated pages (if credentials available)
 *        keyboard-only navigation
 *        focus order, landmarks, headings, contrast, zoom, reduced-motion
 *
 * Usage: node axe-audit.mjs [--auth]
 */

import { chromium } from 'playwright';
import { AxeBuilder } from '@axe-core/playwright';
import { createWriteStream, writeFileSync, existsSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const RESULTS_DIR = resolve(__dirname, 'axe-results');
const BASE_URL = 'https://shunyaos.com';
const APP_URL = 'https://app.shunyaos.com';

if (!existsSync(RESULTS_DIR)) mkdirSync(RESULTS_DIR, { recursive: true });

const LOG_FILE = resolve(RESULTS_DIR, 'audit-report.txt');
const log = (msg) => {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  writeFileSync(LOG_FILE, line + '\n', { flag: 'a' });
};

const VIOLATION_COUNTS = new Map(); // page -> { critical, serious, moderate, minor }
const ALL_VIOLATIONS = []; // flat list with page info

function categorize(violations) {
  let counts = { critical: 0, serious: 0, moderate: 0, minor: 0 };
  for (const v of violations) {
    if (v.impact === 'critical') counts.critical++;
    else if (v.impact === 'serious') counts.serious++;
    else if (v.impact === 'moderate') counts.moderate++;
    else counts.minor++;
  }
  return counts;
}

async function runAxeOnPage(page, url, label) {
  log(`\n═══════════════════════════════════════`);
  log(`SCANNING: ${label} — ${url}`);
  log(`═══════════════════════════════════════\n`);

  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  } catch (e) {
    log(`  ⚠ Failed to load ${url}: ${e.message}`);
    return { violations: [], incomplete: [], counts: { critical: 0, serious: 0, moderate: 0, minor: 0 } };
  }

  await page.waitForTimeout(2000);

  // Run axe-core
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'])
    .analyze();

  const counts = categorize(results.violations);
  VIOLATION_COUNTS.set(label, counts);

  log(`  Violations: ${results.violations.length} total`);
  log(`    Critical: ${counts.critical}  Serious: ${counts.serious}  Moderate: ${counts.moderate}  Minor: ${counts.minor}`);
  log(`  Incomplete items: ${results.incomplete.length}`);

  for (const v of results.violations) {
    const impact = v.impact || 'unknown';
    ALL_VIOLATIONS.push({ page: label, url, ...v });
    log(`\n  ── ${impact.toUpperCase()}: ${v.id} — ${v.help}`);
    log(`     Help: ${v.helpUrl}`);
    log(`     Tags: ${v.tags.join(', ')}`);
    log(`     Elements affected: ${v.nodes.length}`);
    for (const node of v.nodes.slice(0, 3)) {
      const target = node.target?.join(', ') || 'unknown';
      const snippet = (node.html || '').substring(0, 120);
      log(`       • ${target}`);
      log(`         ${snippet}`);
      if (node.failureSummary) {
        log(`         FAIL: ${node.failureSummary.substring(0, 200)}`);
      }
    }
    if (v.nodes.length > 3) {
      log(`       ... and ${v.nodes.length - 3} more elements`);
    }
  }

  // Save full JSON
  const jsonPath = resolve(RESULTS_DIR, `${label.replace(/[^a-zA-Z0-9_-]/g, '_')}.json`);
  writeFileSync(jsonPath, JSON.stringify(results, null, 2));
  log(`\n  Full results saved to: ${jsonPath}`);

  return results;
}

// Keyboard-only navigation test
async function testKeyboardNavigation(page, url, label) {
  log(`\n── KEYBOARD NAVIGATION TEST: ${label} ──`);
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);
  } catch (e) {
    log(`  ⚠ Could not load for keyboard test: ${e.message}`);
    return;
  }

  // Check if there's a visible focusable element
  const focusableCount = await page.evaluate(() => {
    const focusable = document.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    return focusable.length;
  });
  log(`  Focusable elements found: ${focusableCount}`);

  // Tab through first 10 elements
  let focusOrder = [];
  for (let i = 0; i < Math.min(20, focusableCount); i++) {
    await page.keyboard.press('Tab');
    await page.waitForTimeout(50);
    const el = await page.evaluate(() => {
      const a = document.activeElement;
      if (!a) return null;
      return {
        tag: a.tagName,
        role: a.getAttribute('role') || '',
        ariaLabel: a.getAttribute('aria-label') || '',
        text: (a.textContent || '').trim().substring(0, 60),
        id: a.id || '',
        visible: (() => {
          try {
            const rect = a.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
          } catch { return false; }
        })(),
        focused: a === document.activeElement
      };
    });
    if (el) {
      focusOrder.push(el);
      log(`  Tab #${i + 1}: <${el.tag}> ${el.text || el.ariaLabel || el.id} (visible: ${el.visible})`);
    }
  }
  log(`  Focus order captured: ${focusOrder.length} elements`);

  // Test Escape key
  const hasEscapeHandler = await page.evaluate(() => {
    // Check for common escape handlers
    const dialogs = document.querySelectorAll('[role="dialog"], [role="alertdialog"]');
    return dialogs.length > 0;
  });
  log(`  Dialogs present (Escape target): ${hasEscapeHandler}`);

  return focusOrder;
}

// Zoom/reflow test
async function testZoomReflow(page, url, label) {
  log(`\n── ZOOM/REFLOW TEST: ${label} ──`);
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);
  } catch (e) {
    return;
  }

  // Set zoom to 200% via viewport
  const originalViewport = page.viewportSize();
  try {
    await page.setViewportSize({
      width: Math.round(originalViewport.width / 2),
      height: Math.round(originalViewport.height / 2)
    });
    await page.waitForTimeout(500);

    // Check for horizontal scroll at 200% zoom (width 640px equivalent)
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth + 20;
    });
    log(`  At 200% zoom (viewport ${Math.round(originalViewport.width / 2)}px): horizontal scroll = ${hasHorizontalScroll}`);

    // Check if content is still readable
    const bodyText = await page.evaluate(() => document.body?.innerText?.length || 0);
    log(`  Body text length at 200%: ${bodyText} chars`);

    // Restore
    await page.setViewportSize(originalViewport);
  } catch (e) {
    log(`  ⚠ Zoom test error: ${e.message}`);
  }
}

// Reduced motion test
async function testReducedMotion(page, url, label) {
  log(`\n── REDUCED MOTION TEST: ${label} ──`);
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);
  } catch (e) {
    return;
  }

  const hasReducedMotion = await page.evaluate(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    return mediaQuery.matches;
  });
  log(`  prefers-reduced-motion: reduce active: ${hasReducedMotion}`);

  // Check for CSS animations/transitions
  const animCount = await page.evaluate(() => {
    const sheets = document.styleSheets;
    let count = 0;
    try {
      for (const sheet of sheets) {
        try {
          for (const rule of sheet.cssRules || []) {
            if (rule.cssText && (rule.cssText.includes('animation') || rule.cssText.includes('transition'))) {
              count++;
            }
          }
        } catch { /* intentionally empty */ }
      }
    } catch { /* intentionally empty */ }
    return count;
  });
  log(`  CSS animation/transition rules: ${animCount}`);

  // Check for framer-motion reduced motion
  const fmReducedMotion = await page.evaluate(() => {
    return document.documentElement.getAttribute('data-reduced-motion') || 'not set';
  });
  log(`  data-reduced-motion attribute: ${fmReducedMotion}`);
}

// Landmark & heading structure test
async function testStructure(page, url, label) {
  log(`\n── STRUCTURE TEST: ${label} ──`);
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);
  } catch (e) {
    return;
  }

  const structure = await page.evaluate(() => {
    const landmarks = document.querySelectorAll('[role="banner"], [role="navigation"], [role="main"], [role="complementary"], [role="contentinfo"], [role="search"], [role="form"], [role="region"][aria-label], header:not([role="banner"]), footer:not([role="contentinfo"]), nav, main, aside');
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const labels = document.querySelectorAll('label');
    const inputs = document.querySelectorAll('input, select, textarea');
    const inputsWithLabels = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]), select, textarea');

    let labeledInputs = 0;
    let unlabeledInputs = 0;
    for (const input of inputsWithLabels) {
      if (input.getAttribute('aria-label') || input.getAttribute('aria-labelledby') || input.id && document.querySelector(`label[for="${input.id}"]`)) {
        labeledInputs++;
      } else {
        unlabeledInputs++;
      }
    }

    return {
      landmarks: Array.from(landmarks).map(l => ({
        tag: l.tagName,
        role: l.getAttribute('role') || '',
        label: l.getAttribute('aria-label') || l.getAttribute('title') || ''
      })),
      headings: Array.from(headings).map(h => ({
        level: h.tagName,
        text: (h.textContent || '').trim().substring(0, 80)
      })),
      totalLabels: labels.length,
      totalInputs: inputs.length,
      labeledInputs,
      unlabeledInputs
    };
  });

  log(`  Landmarks found: ${structure.landmarks.length}`);
  for (const lm of structure.landmarks) {
    log(`    <${lm.tag}> role="${lm.role}" label="${lm.label}"`);
  }

  log(`  Headings found: ${structure.headings.length}`);
  const headingLevels = structure.headings.map(h => h.level);
  const headingText = structure.headings.map(h => `      ${h.level}: ${h.text}`).join('\n');
  log(`  Heading levels: ${headingLevels.join(', ')}`);
  log(`  ${headingText}`);

  // Check heading hierarchy
  let lastLevel = 0;
  let hierarchyIssues = [];
  for (const h of structure.headings) {
    const level = parseInt(h.level.substring(1));
    if (level - lastLevel > 1 && lastLevel > 0) {
      hierarchyIssues.push(`Heading jump: h${lastLevel} → h${level} ("${h.text}")`);
    }
    lastLevel = level;
  }
  if (hierarchyIssues.length > 0) {
    log(`  ⚠ Heading hierarchy issues:`);
    for (const issue of hierarchyIssues) log(`    ${issue}`);
  } else {
    log(`  ✓ Heading hierarchy looks good`);
  }

  log(`  Form inputs: ${structure.totalInputs} total, ${structure.labeledInputs} labeled, ${structure.unlabeledInputs} UNLABELED`);
}

// Color contrast check
async function testColorContrast(page, url, label) {
  log(`\n── COLOR CONTRAST TEST: ${label} ──`);
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);
  } catch (e) {
    return;
  }

  const contrastData = await page.evaluate(() => {
    const results = [];
    // Check common elements
    const elements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, a, button, label, li, td, th');
    const seen = new Set();
    for (const el of elements) {
      try {
        const style = window.getComputedStyle(el);
        const color = style.color;
        const bg = style.backgroundColor;
        const fontSize = style.fontSize;
        const text = (el.textContent || '').trim();
        if (text && !seen.has(color + bg)) {
          seen.add(color + bg);
          const rect = el.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            results.push({ color, bg, fontSize, text: text.substring(0, 40), tag: el.tagName });
          }
        }
      } catch { /* intentionally empty */ }
    }
    return results;
  });

  log(`  Unique color combinations found: ${contrastData.length}`);
  for (const c of contrastData.slice(0, 10)) {
    log(`    <${c.tag}> color: ${c.color} bg: ${c.bg} font: ${c.fontSize} — "${c.text}"`);
  }
  if (contrastData.length > 10) {
    log(`    ... and ${contrastData.length - 10} more`);
  }
}

// Main function
async function main() {
  const args = process.argv.slice(2);
  const doAuth = args.includes('--auth');
  const doKeyboard = !args.includes('--no-keyboard');

  log('══════════════════════════════════════════════════════════════');
  log('  SHUNYA OS — C-07 ACCESSIBILITY AUDIT');
  log('  Started: ' + new Date().toISOString());
  log('  User-Agent: Playwright + @axe-core/playwright');
  log('  Scan scope: WCAG 2.0/2.1/2.2 AA + best-practice');
  log('══════════════════════════════════════════════════════════════\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
  });

  // Check if we can reach the sites
  const testPage = await context.newPage();
  try {
    await testPage.goto('https://shunyaos.com', { timeout: 15000 });
    log(`✓ shunyaos.com is reachable`);
  } catch (e) {
    log(`✗ shunyaos.com is NOT reachable: ${e.message}`);
  }
  try {
    await testPage.goto('https://app.shunyaos.com', { timeout: 15000 });
    log(`✓ app.shunyaos.com is reachable`);
  } catch (e) {
    log(`✗ app.shunyaos.com is NOT reachable: ${e.message}`);
  }
  await testPage.close();

  // ===================================================================
  // UNAUTHENTICATED PAGES
  // ===================================================================
  log('\n\n╔══════════════════════════════════════════════════════════════╗');
  log('║           UNAUTHENTICATED PAGES                              ║');
  log('╚══════════════════════════════════════════════════════════════╝\n');

  const unauthenticatedPages = [
    { url: BASE_URL, label: 'landing_page' },
    { url: `${BASE_URL}/login`, label: 'login_page' },
    { url: `${BASE_URL}/pricing`, label: 'pricing_page' },
  ];

  for (const { url, label } of unauthenticatedPages) {
    const page = await context.newPage();
    await runAxeOnPage(page, url, label);
    if (doKeyboard) {
      await testKeyboardNavigation(page, url, label);
    }
    await testStructure(page, url, label);
    await testColorContrast(page, url, label);
    await testZoomReflow(page, url, label);
    await testReducedMotion(page, url, label);
    await page.close();
  }

  // ===================================================================
  // AUTHENTICATED PAGES (if --auth flag or credentials available)
  // ===================================================================
  log('\n\n╔══════════════════════════════════════════════════════════════╗');
  log('║           AUTHENTICATED PAGES                                 ║');
  log('╚══════════════════════════════════════════════════════════════╝\n');

  if (doAuth) {
    // Try to authenticate
    const authPage = await context.newPage();
    const email = process.env.SHUNYA_EMAIL || '';
    const password = process.env.SHUNYA_PASSWORD || '';

    if (email && password) {
      log('  Attempting authentication...');
      try {
        await authPage.goto(`${APP_URL}/login`, { waitUntil: 'networkidle', timeout: 30000 });
        await authPage.waitForTimeout(1000);

        // Fill login form
        const emailInput = await authPage.$('input[type="email"], input[name="email"]');
        const passInput = await authPage.$('input[type="password"]');
        if (emailInput && passInput) {
          await emailInput.fill(email);
          await passInput.fill(password);
          await authPage.keyboard.press('Enter');
          await authPage.waitForTimeout(5000);

          const currentUrl = authPage.url();
          log(`  After login URL: ${currentUrl}`);

          if (!currentUrl.includes('/login')) {
            log('  ✓ Authentication successful!');

            const authenticatedPages = [
              { url: currentUrl, label: 'app_dashboard' },
            ];

            // Try to navigate to settings
            try {
              await authPage.goto(`${APP_URL}/settings`, { waitUntil: 'networkidle', timeout: 15000 });
              await authPage.waitForTimeout(1000);
              authenticatedPages.push({ url: authPage.url(), label: 'app_settings' });
            } catch (e) {
              log(`  ⚠ Could not load settings: ${e.message}`);
            }

            // Try to navigate to objects
            try {
              await authPage.goto(`${APP_URL}/objects`, { waitUntil: 'networkidle', timeout: 15000 });
              await authPage.waitForTimeout(1000);
              authenticatedPages.push({ url: authPage.url(), label: 'app_objects' });
            } catch (e) {
              log(`  ⚠ Could not load objects: ${e.message}`);
            }

            for (const { url, label } of authenticatedPages) {
              const p = await context.newPage();
              await runAxeOnPage(p, url, label);
              if (doKeyboard) {
                await testKeyboardNavigation(p, url, label);
              }
              await testStructure(p, url, label);
              await testColorContrast(p, url, label);
              await testZoomReflow(p, url, label);
              await testReducedMotion(p, url, label);
              await p.close();
            }
          } else {
            log('  ✗ Authentication failed — scanning login page only');
          }
        } else {
          log('  ⚠ Login form not found on app.shunyaos.com/login');
          // Check if it redirects to Supabase auth
          log(`  Current URL: ${authPage.url()}`);
        }
      } catch (e) {
        log(`  ⚠ Auth flow error: ${e.message}`);
      }
    } else {
      log('  ⚠ No SHUNYA_EMAIL / SHUNYA_PASSWORD environment variables set.');
      log('  Set these to test authenticated pages, or check if there is a test account.');
      log('  Scanning login page as unauthenticated user instead.');
    }
    await authPage.close();
  } else {
    log('  Skipping authenticated pages (pass --auth to enable).');
    log('  Set SHUNYA_EMAIL and SHUNYA_PASSWORD env vars for auth.');
  }

  await browser.close();

  // ===================================================================
  // SUMMARY
  // ===================================================================
  log('\n\n╔══════════════════════════════════════════════════════════════╗');
  log('║           AUDIT SUMMARY                                       ║');
  log('╚══════════════════════════════════════════════════════════════╝\n');

  let totalCritical = 0, totalSerious = 0, totalModerate = 0, totalMinor = 0;
  for (const [page, counts] of VIOLATION_COUNTS) {
    totalCritical += counts.critical;
    totalSerious += counts.serious;
    totalModerate += counts.moderate;
    totalMinor += counts.minor;
    log(`  ${page}: ${counts.critical} critical, ${counts.serious} serious, ${counts.moderate} moderate, ${counts.minor} minor`);
  }

  log(`\n  TOTAL: ${totalCritical} critical, ${totalSerious} serious, ${totalModerate} moderate, ${totalMinor} minor`);

  // Group by violation ID
  const violationSummary = new Map();
  for (const v of ALL_VIOLATIONS) {
    const key = `${v.id} (${v.impact})`;
    if (!violationSummary.has(key)) {
      violationSummary.set(key, { id: v.id, impact: v.impact, help: v.help, helpUrl: v.helpUrl, pages: new Set(), totalNodes: 0 });
    }
    const entry = violationSummary.get(key);
    entry.pages.add(v.page);
    entry.totalNodes += v.nodes.length;
  }

  log(`\n  Violations by type:`);
  for (const [key, info] of violationSummary) {
    log(`    ${info.impact.toUpperCase()}: ${info.id}`);
    log(`      ${info.help}`);
    log(`      Pages: ${[...info.pages].join(', ')}`);
    log(`      Total nodes: ${info.totalNodes}`);
  }

  log(`\n  Results saved to: ${RESULTS_DIR}/`);
  log('══════════════════════════════════════════════════════════════');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});