#!/usr/bin/env node
/**
 * ESLint Baseline Governance Check
 *
 * Compares current ESLint output against the committed baseline.
 * Fails CI if:
 *   - There are new errors (errors always fail)
 *   - Warning count exceeds baseline (regression)
 *   - The baseline file is missing
 *
 * To update the baseline after fixing warnings:
 *   npx eslint . --format=json > .eslint-current.json
 *   node scripts/update-eslint-baseline.js
 */
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { execSync } from 'child_process';

const BASELINE_PATH = new URL('../.eslint-baseline.json', import.meta.url).pathname;
const CURRENT_PATH = '/tmp/eslint-current.json';

if (!existsSync(BASELINE_PATH)) {
  console.error('❌ ESLint baseline not found at .eslint-baseline.json');
  process.exit(1);
}

// Run ESLint
execSync(`npx eslint . --format=json --output-file=${CURRENT_PATH}`, {
  stdio: 'inherit',
});

const baseline = JSON.parse(readFileSync(BASELINE_PATH, 'utf-8'));
const current = JSON.parse(readFileSync(CURRENT_PATH, 'utf-8'));

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