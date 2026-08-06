/**
 * Invitation Accept — Accepts an invitation to join an organization.
 *
 * States: form → loading → success / error.
 * Keyboard: autoFocus on name, Enter to submit, Tab through.
 * Responsive via shared authStyles.
 */

import { useState } from 'react';
import { authStyles } from './auth-styles';

interface Props {
  token: string;
  /** The org name shown in the heading, if available */
  orgName?: string;
  invitationEmail?: string;
  onBackToLogin: () => void;
  onSubmit?: (token: string, name: string, password: string) => Promise<{ success: boolean; error?: string }>;
}

type Phase = 'form' | 'loading' | 'success' | 'error';

async function defaultAcceptInvitation(
  token: string,
  name: string,
  password: string,
): Promise<{ success: boolean; error?: string }> {
  const resp = await fetch('/api/v1/auth/accept-invitation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, name, password }),
    credentials: 'include',
  });
  const data = await resp.json();
  if (!resp.ok) return { success: false, error: data.error ?? 'Failed to accept invitation.' };
  return { success: true };
}

export function InvitationAccept({ token, orgName, invitationEmail, onBackToLogin, onSubmit }: Props) {
  const [phase, setPhase] = useState<Phase>('form');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const getValidationError = (): string | null => {
    if (!name.trim()) return 'Name is required.';
    if (password.length < 8) return 'Password must be at least 8 characters.';
    if (password !== confirm) return 'Passwords do not match.';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErr = getValidationError();
    if (validationErr) {
      setPhase('error');
      setErrorMsg(validationErr);
      return;
    }
    setPhase('loading');
    setErrorMsg('');
    try {
      const fn = onSubmit ?? defaultAcceptInvitation;
      const result = await fn(token, name.trim(), password);
      if (result.success) {
        setPhase('success');
      } else {
        setPhase('error');
        setErrorMsg(result.error ?? 'Failed to accept invitation. The link may have expired.');
      }
    } catch {
      setPhase('error');
      setErrorMsg('Could not connect. Check that the server is running.');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <div className="sh-auth" onKeyDown={handleKeyDown}>
      <div className="sh-auth-card sh-auth-fade-in">
        {/* ── Header ── */}
        <div className="sh-auth-header">
          <div className="sh-auth-zero">शून्य</div>
          <div className="sh-auth-sub">SHUNYA</div>
        </div>

        {/* ── Success ── */}
        {phase === 'success' && (
          <>
            <div className="sh-auth-success">
              {orgName
                ? `You've joined ${orgName}! Your account is ready.`
                : 'Invitation accepted! Your account is ready.'}
            </div>
            <button className="sh-auth-btn" onClick={onBackToLogin} type="button" autoFocus>
              Sign in
            </button>
          </>
        )}

        {/* ── Form ── */}
        {(phase === 'form' || phase === 'loading' || phase === 'error') && (
          <>
            <div className="sh-auth-info">
              {orgName
                ? `You've been invited to join ${orgName}. Set up your account to get started.`
                : "You've been invited to join an organization. Set up your account to get started."}
            </div>

            {invitationEmail && (
              <div
                className="sh-auth-info"
                style={{ border: '1px solid #2a2a3a', borderRadius: 6, padding: '6px 12px' }}
              >
                📧 {invitationEmail}
              </div>
            )}

            <form className="sh-auth-form" onSubmit={handleSubmit} role="main" aria-label="Accept invitation">
              <div className="sh-auth-field">
                <label htmlFor="invite-name">Full name</label>
                <input
                  id="invite-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  autoFocus
                  disabled={phase === 'loading'}
                  autoComplete="name"
                />
              </div>

              <div className="sh-auth-field">
                <label htmlFor="invite-password">Password</label>
                <input
                  id="invite-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  disabled={phase === 'loading'}
                  autoComplete="new-password"
                />
              </div>

              <div className="sh-auth-field">
                <label htmlFor="invite-confirm">Confirm password</label>
                <input
                  id="invite-confirm"
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Re-enter password"
                  disabled={phase === 'loading'}
                  autoComplete="new-password"
                />
              </div>

              {phase === 'error' && (
                <div className="sh-auth-error" role="alert">
                  {errorMsg}
                </div>
              )}

              <button
                type="submit"
                className="sh-auth-btn"
                disabled={phase === 'loading' || !name.trim() || !password.trim() || !confirm.trim()}
              >
                {phase === 'loading' ? (
                  <>
                    <span className="sh-auth-spinner" />
                    Setting up account…
                  </>
                ) : (
                  'Accept Invitation'
                )}
              </button>
            </form>

            <div className="sh-auth-footer">
              <button className="sh-auth-link" onClick={onBackToLogin} type="button" disabled={phase === 'loading'}>
                Sign in instead
              </button>
            </div>
          </>
        )}
      </div>

      <style>{authStyles}</style>
    </div>
  );
}
