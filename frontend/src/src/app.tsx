import { useEffect, useState } from 'react';
import { TokenProvider } from './tokens/token-provider';
import { WorkspaceBar } from './components/workspace/workspace-bar';
import { WorkspaceContainer } from './components/workspace/workspace-container';
import { SearchBar } from './components/search/universal-search';
import { LoginPage } from './components/auth/login-page';
import { ForgotPassword } from './components/auth/forgot-password';
import { ResetPassword } from './components/auth/reset-password';
import { Signup } from './components/auth/signup';
import { InvitationAccept } from './components/auth/invitation-accept';
import { VerifyEmail } from './components/auth/verify-email';
import { HomePage, homepageStyles } from './components/public/homepage';
import { registerAllRuntimes } from './runtimes/registration';
import { orchestrator } from './runtimes/orchestrator';
import { ModuleRegistry } from './runtimes/module-registry';
import { SessionManager } from './api/session';
import { api } from './api/client';
import { OnboardingFlow, isOnboardingComplete } from './components/onboarding/onboarding-flow';
import { authStyles } from './components/auth/auth-styles';
import { useWorkspaceHydration } from './hooks/workspace-hooks';
import { useWorkspaceStore } from './runtimes/workspace/store';
import { bus } from './runtimes/event-bus';

type Phase = 'public' | 'login' | 'onboarding' | 'booting' | 'ready';

let bootstrapped = false;
let loggingInitialized = false;

function BootScreen({ message }: { message: string }) {
  return (
    <div className="sh-boot" role="status">
      <div className="sh-boot-zero">शून्य</div>
      <div className="sh-boot-text">{message}</div>
    </div>
  );
}

function initRuntimeLogger() {
  if (loggingInitialized) return;
  loggingInitialized = true;
  const logEvents = [
    'WorkspaceOpened', 'WorkspaceDestroyed', 'WorkspaceChanged', 'WorkspaceError',
    'ObjectLoaded', 'ObjectSaved', 'ObjectSaveFailed', 'ObjectDirtyChanged', 'ObjectClosed',
    'NavigationChanged',
  ];
  const logSet = new Set(logEvents);
  bus.onAny((event) => {
    if (logSet.has(event.type)) {
      const ts = new Date().toISOString().slice(11, 23);
      console.log(`[Runtime ${ts}] ${event.type}`, event);
    }
  });
}

function initUnsavedChangesHandler() {
  const handler = (e: BeforeUnloadEvent) => {
    const dirty = useWorkspaceStore.getState().hasDirty();
    if (dirty) {
      e.preventDefault();
      e.returnValue = '';
    }
  };
  window.addEventListener('beforeunload', handler);
  return () => window.removeEventListener('beforeunload', handler);
}

function initBrowserHistory() {
  return useWorkspaceStore.subscribe((state) => {
    const active = state.workspaces.find(w => w.identity.id === state.activeId);
    if (active && active.identity.type === 'object') {
      const url = `/workspace/${active.identity.objectType}/${active.identity.objectId}`;
      if (window.location.pathname !== url) {
        window.history.pushState({ workspaceId: active.identity.id }, '', url);
        bus.emit({ type: 'NavigationChanged', workspaceId: active.identity.id, url });
      }
    } else if (!active || active.identity.type === 'home') {
      if (window.location.pathname !== '/') {
        window.history.pushState({ workspaceId: null }, '', '/');
      }
    }
  });
}

// ── Invitation Page Wrapper ──
function InvitationPage({ token, onBackToLogin }: { token: string; onBackToLogin: () => void }) {
  const [invite, setInvite] = useState<{ email?: string; orgName?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await api.getInvitation(token);
        if (cancelled) return;
        if (resp.success) {
          setInvite({ email: resp.email, orgName: resp.orgName });
        } else {
          setError(resp.error ?? 'Invalid or expired invitation.');
        }
      } catch {
        if (!cancelled) setError('Could not connect. Check that the server is running.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  if (loading) {
    return (
      <TokenProvider>
        <div className="sh-auth"><div className="sh-auth-card"><p className="sh-auth-info">Loading invitation…</p></div><style>{authStyles}</style></div>
      </TokenProvider>
    );
  }

  if (error) {
    return (
      <TokenProvider>
        <div className="sh-auth">
          <div className="sh-auth-card sh-auth-fade-in">
            <div className="sh-auth-header">
              <div className="sh-auth-zero">शून्य</div>
              <div className="sh-auth-sub">SHUNYA</div>
            </div>
            <div className="sh-auth-error" role="alert">{error}</div>
            <button className="sh-auth-btn" onClick={onBackToLogin}>Back to Sign In</button>
          </div>
          <style>{authStyles}</style>
        </div>
      </TokenProvider>
    );
  }

  return (
    <TokenProvider>
      <InvitationAccept
        token={token}
        orgName={invite?.orgName}
        invitationEmail={invite?.email}
        onBackToLogin={onBackToLogin}
        onSubmit={async (t, name, password) => {
          const resp = await api.acceptInvitation(t, name, password);
          return { success: resp.success, error: resp.error };
        }}
      />
    </TokenProvider>
  );
}

function AppShell() {
  useWorkspaceHydration();
  const [phase, setPhase] = useState<Phase>('public');
  const [bootMsg, setBootMsg] = useState('');

  useEffect(() => { initRuntimeLogger(); }, []);
  useEffect(() => initUnsavedChangesHandler(), []);

  useEffect(() => {
    const handler = (e: PopStateEvent) => {
      const wsId = e.state?.workspaceId;
      if (wsId) {
        useWorkspaceStore.getState().activate(wsId);
      } else {
        const home = useWorkspaceStore.getState().workspaces.find(w => w.identity.type === 'home');
        if (home) useWorkspaceStore.getState().activate(home.identity.id);
      }
    };
    window.addEventListener('popstate', handler);
    return () => window.removeEventListener('popstate', handler);
  }, []);

  useEffect(() => {
    const unsub = initBrowserHistory();
    return unsub;
  }, []);

  // Inject homepage styles early
  useEffect(() => {
    const el = document.createElement('style');
    el.textContent = homepageStyles;
    el.id = 'shunya-homepage-styles';
    if (!document.getElementById('shunya-homepage-styles')) {
      document.head.appendChild(el);
    }
  }, []);

  const bootstrap = async () => {
    if (bootstrapped) return;
    bootstrapped = true;
    setPhase('booting');
    setBootMsg('Starting platform…');

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

      setPhase('ready');
    } catch {
      setPhase('ready');
    }
  };

  const handleEnterApp = () => {
    const saved = SessionManager.load();
    if (saved) {
      bootstrap();
    } else {
      setPhase('login');
    }
  };

  useEffect(() => {
    // If user has a session and navigates directly to /, go to workspace
    const saved = SessionManager.load();
    if (window.location.pathname.startsWith('/auth/')) {
      // Auth routes handled by AuthRouter below — phase stays 'public' until
      // the route is determined, but we ensure the auth page renders.
      setPhase('login');
      return;
    }
    if (saved) {
      // If onboarding is complete, bootstrap directly; otherwise show onboarding
      if (isOnboardingComplete()) {
        bootstrap();
      } else {
        setPhase('onboarding');
      }
    }
    // Otherwise stay on public homepage
  }, []);

  // ── Auth Router ──
  function AuthRouter() {
    const path = window.location.pathname;

    // Extract token from query params (used by reset-password, verify-email, invitation)
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token') || '';

    const goToLogin = () => {
      window.history.pushState({}, '', '/auth/login');
      window.dispatchEvent(new PopStateEvent('popstate'));
    };

    if (path === '/auth/login' || path === '/auth/') {
      return (
        <TokenProvider>
          <LoginPage onLogin={(s) => {
            SessionManager.save(s);
            if (isOnboardingComplete()) {
              bootstrap();
            } else {
              setPhase('onboarding');
            }
          }} />
        </TokenProvider>
      );
    }

    if (path === '/auth/forgot-password') {
      return (
        <TokenProvider>
          <ForgotPassword
            onBackToLogin={goToLogin}
            onSubmit={async (email) => {
              const resp = await api.forgotPassword(email);
              return { success: resp.success, error: resp.error };
            }}
          />
        </TokenProvider>
      );
    }

    if (path === '/auth/reset-password') {
      return (
        <TokenProvider>
          <ResetPassword
            token={token}
            onBackToLogin={goToLogin}
            onSubmit={async (t, password) => {
              const resp = await api.resetPassword(t, password);
              return { success: resp.success, error: resp.error };
            }}
          />
        </TokenProvider>
      );
    }

    if (path === '/auth/signup') {
      return (
        <TokenProvider>
          <Signup
            onBackToLogin={goToLogin}
            onSubmit={async (name, email, password) => {
              const resp = await api.signup(email, password, name);
              return { success: resp.success, error: resp.error };
            }}
          />
        </TokenProvider>
      );
    }

    if (path === '/auth/invitation') {
      return (
        <TokenProvider>
          <InvitationPage
            token={token}
            onBackToLogin={goToLogin}
          />
        </TokenProvider>
      );
    }

    if (path === '/auth/verify-email') {
      return (
        <TokenProvider>
          <VerifyEmail
            token={token}
            onBackToLogin={goToLogin}
            onSubmit={async (t) => {
              const resp = await api.verifyEmail(t);
              return { success: resp.success, error: resp.error };
            }}
          />
        </TokenProvider>
      );
    }

    // Fallback: unknown /auth/ path → redirect to login
    return (
      <TokenProvider>
        <LoginPage onLogin={(s) => {
          SessionManager.save(s);
          if (isOnboardingComplete()) {
            bootstrap();
          } else {
            setPhase('onboarding');
          }
        }} />
      </TokenProvider>
    );
  }

  // ── Public Homepage ──
  if (phase === 'public') {
    return <HomePage onEnterApp={handleEnterApp} />;
  }

  // ── Login / Auth Pages ──
  if (phase === 'login') {
    return <AuthRouter />;
  }

  // ── Onboarding ──
  if (phase === 'onboarding') {
    return (
      <TokenProvider>
        <OnboardingFlow onComplete={bootstrap} />
      </TokenProvider>
    );
  }

  // ── Booting ──
  if (phase === 'booting') {
    return (
      <TokenProvider>
        <BootScreen message={bootMsg} />
      </TokenProvider>
    );
  }

  // ── Authenticated Workspace ──
  return (
    <TokenProvider>
      <div className="sh-app">
        <WorkspaceBar />
        <WorkspaceContainer />
      </div>
      <SearchBar />
    </TokenProvider>
  );
}

const styles = `
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #root { height: 100%; width: 100%; }
body { font-family: var(--shunya-font-family); font-size: var(--shunya-font-size-md); color: var(--shunya-text); background: var(--shunya-bg); -webkit-font-smoothing: antialiased; }
.sh-app { display: flex; flex-direction: column; height: 100vh; }
.sh-boot { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: var(--shunya-bg, #0a0a0f); gap: var(--shunya-spacing-md); padding: var(--shunya-spacing-xl); text-align: center; }
.sh-boot-zero { font-size: clamp(2rem, 6vw, 4rem); color: #fff; font-weight: 300; opacity: 0.6; }
.sh-boot-text { font-size: var(--shunya-font-size-lg); color: var(--shunya-text-secondary, #666); }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  el.id = 'shunya-base-styles';
  document.head.appendChild(el);
}

export function App() { return <AppShell />; }