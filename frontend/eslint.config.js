import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';

export default [
  {
    ignores: [
      'dist/',
      'node_modules/',
      '*.config.*',
      'storybook-static/',
      'axe-results/',
      'screenshots/',
      'audit/',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx,js,jsx}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.es2021,
        process: 'readonly',
      },
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: { react, 'react-hooks': reactHooks },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-explicit-any': 'warn',
      'no-console': 'warn',
    },
  },
  // Playwright/Node tooling scripts (axe-audit.mjs, axe-comprehensive.mjs)
  {
    files: ['axe-*.mjs'],
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.browser,
        ...globals.es2021,
      },
    },
    rules: {
      'no-console': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    },
  },
  // Service worker (public/sw.js)
  {
    files: ['public/sw.js'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.serviceworker,
        ...globals.es2021,
      },
    },
    rules: {
      'no-console': 'off',
    },
  },
  // Node scripts (scripts/check-source-integrity.js)
  {
    files: ['scripts/**/*.js', '*.mjs'],
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.es2021,
      },
    },
    rules: {
      'no-console': 'off',
    },
  },
];
