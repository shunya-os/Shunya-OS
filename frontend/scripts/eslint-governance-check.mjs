#!/usr/bin/env node
/**
 * ESLint Baseline Governance Check
 *
 * Compares current ESLint output against the committed baseline.
 * Fails CI if:
 *   - There are new errors (errors always fail)
 *   - Warning count exceeds baseline (regression)
 *   - The baseline file is missing
 */
import { readFileSync, existsSync } from 'fs';
import { execSync } from 'child_process';

const BASELINE_PATH = new URL('../.eslint-baseline.json', import.meta.url).pathname;

if (!existsSync(BASELINE_PATH)) {
  console.error('❌ ESLint baseline not found at .eslint-baseline.json');
  process.exit(1);
}

// Run ESLint and capture output. maxBuffer is large because axe-audit.mjs
// embeds a large inline source string that inflates the JSON output.
const stdout = execSync('npx eslint . --format=json', { encoding: 'utf-8', maxBuffer: 64 * 1024 * 1024 });
const current = JSON.parse(stdout);

const baseline = JSON.parse(readFileSync(BASELINE_PATH, 'utf-8'));

const currentErrors = current.reduce((sum, f) => sum + f.messages.filter(m => m.severity === 2).length, 0);
const currentWarnings = current.reduce((sum, f) => sum + f.messages.filter(m => m.severity === 1).length, 0);

let exitCode = 0;

if (currentErrors > 0) {
  console.error(`❌ ESLint errors: ${currentErrors} — errors must be 0`);
  exitCode = 1;
}

if (currentWarnings > baseline.total) {
  console.error(`❌ Warning regression: ${currentWarnings} > ${baseline.total} (baseline)`);
  console.error('   Fix warnings or update .eslint-baseline.json');
  exitCode = 1;
} else if (currentWarnings < baseline.total) {
  console.log(`✅ Warnings decreased: ${baseline.total} → ${currentWarnings} (${baseline.total - currentWarnings} fewer)`);
}

if (exitCode === 0) {
  console.log(`✅ ESLint check passed: ${currentErrors} errors, ${currentWarnings} warnings (baseline: ${baseline.total})`);
}

process.exit(exitCode);