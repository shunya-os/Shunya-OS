import { useState, useEffect } from 'react';
import { TokenProvider } from './tokens/token-provider';
import { LivingWorkspace } from './components/living-workspace';
import { LoginPage } from './components/auth/login-page';
import { ForgotPassword } from './components/auth/forgot-password';
import { ResetPassword } from './components/auth/reset-password';
import { Signup } from './components/auth/signup';
import { InvitationAccept } from './components/auth/invitation-accept';
import { VerifyEmail } from './components/auth/verify-email';
import { HomePage } from './components/public/homepage';
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
import { useActiveContext } from './hooks/use-active-context';

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

  // Styles are injected by each component via <style> tags

  const bootstrap = async () => {
    if (bootstrapped) return;
    bootstrapped = true;

    // Stage 0 — Context: initialize active organization context from backend session
    useActiveContext.getState().init();

    // Stage 1 — Immediate: show the workspace shell immediately
    // The app shell, identity, and navigation render without waiting for
    // runtimes, modules, or capabilities.
    setPhase('ready');
    setBootMsg(''); // Clear boot message — shell is visible

    // Stage 2 — Interactive: start runtimes in the background
    // Runtimes declare their criticality, so non-critical ones don't block
    // the workspace. The user can start navigating and working immediately.
    setTimeout(async () => {
      try {
        registerAllRuntimes();
        // startAll is non-blocking; critical runtimes initialize first,
        // non-critical ones hydrate in the background
        orchestrator.startAll().catch(() => {});
        ModuleRegistry.loadAll().catch(() => {});
        ModuleRegistry.discoverAll().then(data => ModuleRegistry.registerAll(data)).catch(() => {});
      } catch {
        // Stage failures never blank the workspace
      }
    }, 0);
  };

  const handleEnterApp = async () => {
    const saved = SessionManager.load();
    if (saved) {
      bootstrap();
    } else {
      // Try restoring from backend Flask session cookie
      try {
        const r = await fetch('/api/v1/auth/session', { credentials: 'include' });
        if (r.ok) {
          const data = await r.json();
          if (data.authenticated) {
            SessionManager.save({
              identityId: data.identity_id || '',
              email: data.email || '',
              name: data.name || '',
              orgId: String(data.org_id || ''),
              orgName: data.org_name || '',
            });
            bootstrap();
            return;
          }
        }
      } catch { /* No backend session — show login */ }
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
    } else {
      // Try restoring from backend Flask session cookie
      (async () => {
        try {
          const r = await fetch('/api/v1/auth/session', { credentials: 'include' });
          if (r.ok) {
            const data = await r.json();
            if (data.authenticated) {
              SessionManager.save({
                identityId: data.identity_id || '',
                email: data.email || '',
                name: data.name || '',
                orgId: String(data.org_id || ''),
                orgName: data.org_name || '',
              });
              if (isOnboardingComplete()) {
                bootstrap();
              } else {
                setPhase('onboarding');
              }
              return;
            }
          }
        } catch { /* No backend session — stay on public page */ }
        // Otherwise stay on public homepage
      })();
    }
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
          }} onSignUp={() => {
            window.location.href = '/auth/signup';
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
        }} onSignUp={() => {
          window.location.href = '/auth/signup';
        }} />
      </TokenProvider>
    );
  }

  // ── Public Homepage ──
  if (phase === 'public') {
    return (
      <>
        <a href="#main-content" className="sh-skip-link">Skip to main content</a>
        <div id="main-content">
          <HomePage onEnterApp={handleEnterApp} />
        </div>
      </>
    );
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

  // ── Authenticated Workspace (separate component to respect React hooks rules) ──
  if (phase === 'ready') {
    return <AuthenticatedWorkspace />;
  }

  // Fallback — should not reach here
  return <BootScreen message="Loading…" />;
}

function AuthenticatedWorkspace() {
  return (
    <TokenProvider>
      <LivingWorkspace />
    </TokenProvider>
  );
}

const styles = `
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #root { height: 100%; width: 100%; }
body {
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  font-size: var(--shunya-text-base, 14px);
  line-height: 1.5;
  color: var(--shunya-text, #1A1C1D);
  background: var(--shunya-bg, #FBF8F5);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
.sh-boot {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 100vh;
  background: var(--shunya-bg, #FBF8F5);
  gap: 16px; padding: 40px;
  text-align: center;
}
.sh-boot-zero {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: clamp(2rem, 6vw, 4rem);
  color: var(--shunya-text, #1A1C1D);
  font-weight: 400;
  letter-spacing: var(--shunya-tracking-wider, 0.06em);
}
.sh-boot-text {
  font-size: var(--shunya-text-md, 16px);
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
}
.sh-skip-link {
  position: fixed; top: -100%; left: 8px; z-index: 9999;
  padding: 8px 16px; background: var(--shunya-text, #1A1C1D);
  color: var(--shunya-surface, #FFFFFF);
  font-size: var(--shunya-text-sm, 12px); border-radius: 0 0 8px 8px;
  text-decoration: none; font-family: var(--shunya-font-body, 'Inter', sans-serif);
  transition: top var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-skip-link:focus { top: 0; outline: 2px solid var(--shunya-gold, #A4865F); }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  el.id = 'shunya-base-styles';
  document.head.appendChild(el);
}

// Set data-reduced-motion attribute for framer-motion
if (typeof window !== 'undefined') {
  const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
  document.documentElement.setAttribute('data-reduced-motion', mq.matches ? 'true' : 'false');
  mq.addEventListener('change', (e) => {
    document.documentElement.setAttribute('data-reduced-motion', e.matches ? 'true' : 'false');
  });
}

export function App() { return <AppShell />; }