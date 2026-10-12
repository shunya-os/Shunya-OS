import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@shunya': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://127.0.0.1:5001',
    },
  },
  // ══ vitest options (ignored by vite build) ═══════════════
  // jsdom needs a non-opaque origin URL for localStorage/sessionStorage to
  // exist; without it tests touching storage fail with "localStorage is
  // undefined" (jsdom returns opaque-origin behavior for about:blank).
  test: {
    environmentOptions: {
      jsdom: { url: 'http://localhost/' },
    },
  },
});