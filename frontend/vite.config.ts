import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';

const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:5001';

// Optional HTTPS for local test stacks that must honour Secure cookies.
// Set VITE_HTTPS_KEY + VITE_HTTPS_CERT to a self-signed pair; unset → HTTP.
const httpsKey = process.env.VITE_HTTPS_KEY;
const httpsCert = process.env.VITE_HTTPS_CERT;
const httpsConfig = httpsKey && httpsCert
  ? { key: fs.readFileSync(httpsKey), cert: fs.readFileSync(httpsCert) }
  : undefined;

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@shunya': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    ...(httpsConfig ? { https: httpsConfig } : {}),
    proxy: {
      '/api': proxyTarget,
    },
  },
  // ══ vitest options (ignored by vite build) ═══════════════
  test: {
    environmentOptions: {
      jsdom: { url: 'http://localhost/' },
    },
  },
});