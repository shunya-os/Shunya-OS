import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './app';

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

try {
  const rootEl = document.getElementById('root');
  if (rootEl) {
    ReactDOM.createRoot(rootEl).render(
      <ErrorBoundary>
        <App />
      </ErrorBoundary>,
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
