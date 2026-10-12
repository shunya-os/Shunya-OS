import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

// Vitest 4 prefers vitest.config.ts over vite.config.ts. This mirrors the
// app's vite config (react plugin + @shunya alias) and adds test-only
// environment options:
//   - jsdom needs a non-opaque origin URL for localStorage/sessionStorage to
//     exist; without it tests touching storage fail with "localStorage is
//     undefined" (jsdom gives opaque-origin behavior for about:blank).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@shunya': path.resolve(__dirname, 'src'),
    },
  },
  test: {
    setupFiles: ['./vitest.setup.ts'],
    environmentOptions: {
      jsdom: { url: 'http://localhost/' },
    },
  },
});