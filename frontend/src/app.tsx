/**
 * SHUNYA LX-01 — Experience Entry Point
 *
 * Routing decision:
 * - /auth/* paths → auth pages
 * - /living → LX-01 Canonical Living Workspace (new experience lab)
 * - /* → existing unified OS HomePage
 */

import { useEffect, useState } from 'react';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import { TokenProvider } from './tokens/token-provider';
import { ResetPassword } from './components/auth/reset-password';
import { InvitationAccept } from './components/auth/invitation-accept';
import { VerifyEmail } from './components/auth/verify-email';
import { LivingWorkspace } from './components/living-workspace';
import './components/living-workspace/living-styles.css';
import { api } from './api/client';

// ── Auth Router for deep-link auth paths ──
function AuthRouter({ onAuthSuccess: _onAuthSuccess }: { onAuthSuccess: () => void }) {
  const path = window.location.pathname;
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token') || '';

  const goHome = () => {
    window.location.href = '/';
  };

  if (path === '/auth/reset-password') {
    return (
      <TokenProvider>
        <ResetPassword
          token={token}
          onBackToLogin={goHome}
          onSubmit={async (t, password) => {
            const resp = await api.resetPassword(t, password);
            return { success: resp.success, error: resp.error };
          }}
        />
      </TokenProvider>
    );
  }

  if (path === '/auth/invitation') {
    return (
      <TokenProvider>
        <InvitationPlaceholder token={token} onBackToLogin={goHome} />
      </TokenProvider>
    );
  }

  if (path === '/auth/verify-email') {
    return (
      <TokenProvider>
        <VerifyEmail
          token={token}
          onBackToLogin={goHome}
          onSubmit={async (t) => {
            const resp = await api.verifyEmail(t);
            return { success: resp.success, error: resp.error };
          }}
        />
      </TokenProvider>
    );
  }

  window.location.href = '/';
  return null;
}

function InvitationPlaceholder({ token, onBackToLogin }: { token: string; onBackToLogin: () => void }) {
  const [invite, setInvite] = useState<{ email?: string; orgName?: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await api.getInvitation(token);
        if (cancelled) return;
        if (resp.success) setInvite({ email: resp.email, orgName: resp.orgName });
      } catch {
        if (!cancelled) setInvite(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  if (loading)
    return (
      <TokenProvider>
        <div className="sh-auth">
          <div className="sh-auth-card">
            <p>Loading invitation…</p>
          </div>
        </div>
      </TokenProvider>
    );

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
  const path = window.location.pathname;

  // Auth deep-link paths
  if (path.startsWith('/auth/')) {
    return <AuthRouter onAuthSuccess={() => window.location.reload()} />;
  }

  // LX-01 Canonical Living Workspace
  //   / and /living both render the same component.
  //   The workspace awakens progressively using production state only.
  //   Authentication changes only Identity + Reality ownership.
  //   The visitor never enters a different application.
  return <LivingWorkspace />;
}

const styles = `
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #root { height: 100%; width: 100%; }
body {
  font-family: var(--sh-font-body);
  font-size: var(--sh-text-base);
  color: var(--sh-text, #1A1C1D);
  background: var(--sh-bg, #1A1818);
  -webkit-font-smoothing: antialiased;
}
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  el.id = 'shunya-base-styles';
  document.head.appendChild(el);
}

export function App() {
  return <AppShell />;
}