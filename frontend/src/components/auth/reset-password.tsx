/**
 * Reset Password — Sets a new password via a reset token.
 *
 * States: form → loading → success / error.
 * Keyboard: autoFocus on new password, Enter to submit, Tab through.
 * Responsive via shared authStyles.
 */

import { useState } from 'react';
import { authStyles } from './auth-styles';

interface Props {
  token: string;
  onBackToLogin: () => void;
  onSubmit?: (token: string, password: string) => Promise<{ success: boolean; error?: string }>;
}

type Phase = 'form' | 'loading' | 'success' | 'error';

async function defaultResetPassword(token: string, password: string): Promise<{ success: boolean; error?: string }> {
  const resp = await fetch('/api/v1/auth/reset-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, password }),
    credentials: 'include',
  });
  const data = await resp.json();
  if (!resp.ok) return { success: false, error: data.error ?? 'Failed to reset password.' };
  return { success: true };
}

export function ResetPassword({ token, onBackToLogin, onSubmit }: Props) {
  const [phase, setPhase] = useState<Phase>('form');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const getValidationError = (): string | null => {
    if (password.length < 8) return 'Password must be at least 8 characters.';
    if (password !== confirm) return 'Passwords do not match.';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim() || !confirm.trim()) return;
    const validationErr = getValidationError();
    if (validationErr) {
      setPhase('error');
      setErrorMsg(validationErr);
      return;
    }
    setPhase('loading');
    setErrorMsg('');
    try {
      const fn = onSubmit ?? defaultResetPassword;
      const result = await fn(token, password);
      if (result.success) {
        setPhase('success');
      } else {
        setPhase('error');
        setErrorMsg(result.error ?? 'Failed to reset password. The link may have expired.');
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
            <div className="sh-auth-success">Password reset successfully!</div>
            <button className="sh-auth-btn" onClick={onBackToLogin} type="button" autoFocus>
              Sign in with new password
            </button>
          </>
        )}

        {/* ── Form ── */}
        {(phase === 'form' || phase === 'loading' || phase === 'error') && (
          <>
            <div className="sh-auth-info">Enter your new password.</div>

            <form className="sh-auth-form" onSubmit={handleSubmit} role="main" aria-label="Reset password">
              <div className="sh-auth-field">
                <label htmlFor="reset-password">New password</label>
                <input
                  id="reset-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  autoFocus
                  disabled={phase === 'loading'}
                  aria-describedby={phase === 'error' ? 'reset-error' : undefined}
                />
              </div>

              <div className="sh-auth-field">
                <label htmlFor="reset-confirm">Confirm password</label>
                <input
                  id="reset-confirm"
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Re-enter password"
                  disabled={phase === 'loading'}
                />
              </div>

              {phase === 'error' && (
                <div id="reset-error" className="sh-auth-error" role="alert">
                  {errorMsg}
                </div>
              )}

              <button
                type="submit"
                className="sh-auth-btn"
                disabled={phase === 'loading' || !password.trim() || !confirm.trim()}
              >
                {phase === 'loading' ? (
                  <>
                    <span className="sh-auth-spinner" />
                    Resetting…
                  </>
                ) : (
                  'Reset Password'
                )}
              </button>
            </form>

            <div className="sh-auth-footer">
              <button className="sh-auth-link" onClick={onBackToLogin} type="button" disabled={phase === 'loading'}>
                Back to sign in
              </button>
            </div>
          </>
        )}
      </div>

      <style>{authStyles}</style>
    </div>
  );
}
