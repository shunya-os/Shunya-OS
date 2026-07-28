import { useEffect, useState, useRef } from 'react';
import { TokenProvider } from './tokens/token-provider';
import { WorkspaceBar } from './components/workspace/workspace-bar';
import { WorkspaceContainer } from './components/workspace/workspace-container';
import { SearchBar } from './components/search/universal-search';
import { LoginPage } from './components/auth/login-page';
import { registerAllRuntimes } from './runtimes/registration';
import { orchestrator } from './runtimes/orchestrator';
import { ModuleRegistry } from './runtimes/module-registry';
import { SessionManager } from './api/session';
import { useWorkspaceHydration } from './hooks/workspace-hooks';
import { useWorkspaceStore } from './runtimes/workspace/store';

type Phase = 'login' | 'booting' | 'timedout' | 'ready';
const BOOT_TIMEOUT = 15000; // 15 seconds

let bootstrapped = false;

function BootScreen({ message, error, retry }: { message: string; error?: string; retry?: () => void }) {
  return (
    <div className="sh-boot" role="status">
      <div className="sh-boot-spinner" />
      <div className="sh-boot-text">{message}</div>
      {error && (
        <div className="sh-boot-error">
          <p>{error}</p>
          {retry && <button className="sh-boot-retry" onClick={retry}>Retry</button>}
        </div>
      )}
    </div>
  );
}

function AppShell() {
  useWorkspaceHydration();
  const [phase, setPhase] = useState<Phase>('booting');
  const [bootMsg, setBootMsg] = useState('');
  const [error, setError] = useState('');
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const startBootTimer = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setPhase('timedout');
      setError('Platform is taking longer than expected. The backend may be unavailable.');
    }, BOOT_TIMEOUT);
  };

  const bootstrap = async () => {
    if (bootstrapped) return;
    bootstrapped = true;
    setError('');
    setPhase('booting');
    setBootMsg('Starting platform…');
    startBootTimer();

    try {
      registerAllRuntimes();
      await orchestrator.startAll();

      setBootMsg('Loading modules…');
      await ModuleRegistry.loadAll();

      if (ModuleRegistry.hasModules) {
        setBootMsg('Discovering capabilities…');
        const data = await ModuleRegistry.discoverAll();
        await ModuleRegistry.registerAll(data);
      }

      if (timerRef.current) clearTimeout(timerRef.current);
      setPhase('ready');
    } catch (err: any) {
      if (timerRef.current) clearTimeout(timerRef.current);
      setError(err.message ?? 'Platform failed to start');
      setPhase('timedout');
    }
  };

  useEffect(() => {
    const saved = SessionManager.load();
    if (saved) bootstrap();
    else setPhase('login');
  }, []);

  // Wire ⌘1-⌘9 workspace shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key >= '1' && e.key <= '9') {
        e.preventDefault();
        const idx = parseInt(e.key) - 1;
        const ws = useWorkspaceStore.getState().workspaces[idx];
        if (ws) useWorkspaceStore.getState().activate(ws.identity.id);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  if (phase === 'login') return (
    <TokenProvider>
      <LoginPage onLogin={(s) => { SessionManager.save(s); bootstrap(); }} />
    </TokenProvider>
  );

  if (phase === 'booting' || phase === 'ready') {
    const showBoot = phase === 'booting';
    if (showBoot) return <TokenProvider><BootScreen message={bootMsg} error={error} retry={error ? () => { bootstrapped = false; bootstrap(); } : undefined} /></TokenProvider>;

    return (
      <TokenProvider>
        <div className="sh-shell">
          <WorkspaceBar />
          <SearchBar />
          <WorkspaceContainer />
          <div className="sh-cmd-hint"><kbd>⌘K</kbd> search · <kbd>⌘1</kbd>–<kbd>⌘9</kbd> workspaces</div>
        </div>
      </TokenProvider>
    );
  }

  // Timed out — show retry
  return (
    <TokenProvider>
      <BootScreen
        message="Connection issue"
        error={error || 'Could not connect to the backend. Check that the server is running.'}
        retry={() => { bootstrapped = false; bootstrap(); }}
      />
    </TokenProvider>
  );
}

const styles = `
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #root { height: 100%; width: 100%; }
body { font-family: var(--shunya-font-family); font-size: var(--shunya-font-size-md); color: var(--shunya-text); background: var(--shunya-bg); -webkit-font-smoothing: antialiased; }
.sh-shell { display: flex; flex-direction: column; height: 100vh; }
.sh-boot { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: var(--shunya-bg); gap: var(--shunya-spacing-md); padding: var(--shunya-spacing-xl); text-align: center; }
.sh-boot-spinner { width: 32px; height: 32px; border: 3px solid var(--shunya-color-primary); border-top-color: var(--shunya-color-secondary); border-radius: 50%; animation: sh-spin 0.8s linear infinite; }
@keyframes sh-spin { to { transform: rotate(360deg); } }
.sh-boot-text { font-size: var(--shunya-font-size-lg); color: var(--shunya-text-secondary); }
.sh-boot-error { display: flex; flex-direction: column; align-items: center; gap: var(--shunya-spacing-sm); font-size: var(--shunya-font-size-sm); color: var(--shunya-color-danger); }
.sh-boot-retry { padding: var(--shunya-spacing-sm) var(--shunya-spacing-lg); background: var(--shunya-color-primary); color: white; border: none; border-radius: var(--shunya-radius-sm); font-size: var(--shunya-font-size-sm); cursor: pointer; margin-top: var(--shunya-spacing-sm); }
.sh-boot-retry:hover { opacity: 0.85; }
.sh-cmd-hint { position: fixed; bottom: var(--shunya-spacing-md); left: 50%; transform: translateX(-50%); font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); background: var(--shunya-surface-2); padding: var(--shunya-spacing-xs) var(--shunya-spacing-md); border-radius: var(--shunya-radius-md); box-shadow: var(--shunya-elevation-2); pointer-events: none; opacity: 0.6; z-index: 100; }
.sh-cmd-hint kbd { padding: 1px 4px; border: 1px solid var(--shunya-color-primary); border-radius: 3px; font-family: monospace; }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  document.head.appendChild(el);
}

export function App() { return <AppShell />; }