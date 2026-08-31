import React from 'react';
import ReactDOM from 'react-dom/client';
import '@mantine/core/styles.css';
import { MantineProvider, createTheme } from '@mantine/core';
import { App } from './app';
import { injectAdaptiveStyles } from './runtimes/adaptive';

// Inject adaptive surface styles at bootstrap
injectAdaptiveStyles();

// SHUNYA theme — calm, restrained, premium
const shunyaTheme = createTheme({
  primaryColor: 'violet',
  defaultRadius: 'sm',
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  colors: {
    dark: [
      '#C1C2C5', '#A6A7AB', '#909296', '#5C5F66',
      '#373A40', '#2C2E33', '#25262B', '#1A1B1E',
      '#141517', '#101113',
    ],
  },
  defaultGradient: { deg: 135, from: '#6C63FF', to: '#A4865F' },
  respectReducedMotion: true,
});

// Global error capture for headless browser debugging
const errorLog: Array<{ msg: string; stack: string; source: string }> = [];
(window as any).__SHUNYA_E = errorLog;

window.addEventListener('error', (e: Event) => {
  const err = e as ErrorEvent;
  errorLog.push({
    msg: err.message || 'unknown',
    stack: err.error?.stack || '',
    source: 'window.error',
  });
});

window.addEventListener('unhandledrejection', (e: PromiseRejectionEvent) => {
  errorLog.push({
    msg: e.reason?.message || String(e.reason || 'unknown'),
    stack: e.reason?.stack || '',
    source: 'unhandledrejection',
  });
});

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error: string }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: '' };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error?.message || String(error) };
  }
  componentDidCatch(error: Error, _info: React.ErrorInfo) {
    const msg = error?.message || String(error);
    const stack = error?.stack || '';
    errorLog.push({ msg, stack, source: 'react.catch' });
  }
  render() {
    if (this.state.hasError) {
      return React.createElement(
        'div',
        { style: { padding: '40px', color: '#fff', background: '#0a0a0f' } },
        React.createElement('h1', { style: { fontWeight: 300, fontSize: 24, margin: '0 0 8px' } }, 'SHUNYA'),
        React.createElement('p', { style: { color: '#888', fontSize: 14 } }, this.state.error),
        React.createElement(
          'p',
          { style: { color: '#666', fontSize: 12, marginTop: 16 } },
          'Please refresh or sign in again.',
        ),
      );
    }
    return this.props.children;
  }
}

// PWA Push Notification subscription
async function subscribeToPush(reg: ServiceWorkerRegistration) {
  if (!('PushManager' in window)) return;
  try {
    const resp = await fetch('/api/v1/notifications/vapid-public-key');
    if (!resp.ok) return;
    const { public_key } = await resp.json();

    const keyBytes = Uint8Array.from(atob(public_key), (c) => c.charCodeAt(0));

    let subscription = await reg.pushManager.getSubscription();
    if (!subscription) {
      subscription = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: keyBytes,
      });
    }

    await fetch('/api/v1/notifications/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(subscription.toJSON()),
    });
  } catch (err: any) {
    if (err?.name === 'NotAllowedError') {
      return; // User denied notification permission — normal
    }
    errorLog.push({ msg: 'Push notification subscription failed: ' + (err?.message || String(err)), stack: '', source: 'push.subscribe' });
  }
}

try {
  const rootEl = document.getElementById('root');
  if (rootEl) {
    ReactDOM.createRoot(rootEl).render(
      <MantineProvider theme={shunyaTheme} defaultColorScheme="dark">
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </MantineProvider>,
    );

    // Register service worker for PWA support
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').then((reg) => {
        reg.onupdatefound = () => {
          const installing = reg.installing;
          if (installing) {
            installing.addEventListener('statechange', () => {
              if (installing.state === 'installed' && navigator.serviceWorker.controller) {
                errorLog.push({ msg: 'SHUNYA updated — new version available. Close and reopen all tabs for the latest.', stack: '', source: 'sw.update' });
              }
            });
          }
        };

        // Subscribe to push notifications after SW registration
        subscribeToPush(reg);
      }).catch((err) => {
        errorLog.push({ msg: 'Service worker registration failed: ' + (err?.message || String(err)), stack: '', source: 'sw.register' });
      });
    }
  }
} catch (e: any) {
  errorLog.push({
    msg: e?.message || 'Unknown error',
    stack: e?.stack || '',
    source: 'render.catch',
  });
  document.body.innerHTML =
    '<div style="padding:40px;color:#fff;background:#0a0a0f">' +
    '<h1 style="font-weight:300;font-size:24px;margin:0 0 8px">SHUNYA</h1>' +
    '<p style="color:#888;font-size:14px">' +
    (e?.message || 'Unknown error') +
    '</p></div>';
}