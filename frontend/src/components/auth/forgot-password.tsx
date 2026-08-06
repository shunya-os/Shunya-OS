/**
 * Forgot Password — Sends a password reset email.
 *
 * States: form → loading → success / error.
 * Keyboard: autoFocus on email, Enter to submit, Tab through.
 * Responsive via shared authStyles.
 */

import { useState } from 'react';
import { authStyles } from './auth-styles';

interface Props {
  onBackToLogin: () => void;
  /** Override for testing / Storybook */
  onSubmit?: (email: string) => Promise<{ success: boolean; error?: string }>;
}

type Phase = 'form' | 'loading' | 'success' | 'error';

async function defaultSendReset(email: string): Promise<{ success: boolean; error?: string }> {
  const resp = await fetch('/api/v1/auth/forgot-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
    credentials: 'include',
  });
  const data = await resp.json();
  if (!resp.ok) return { success: false, error: data.error ?? 'Failed to send reset email.' };
  return { success: true };
}

export function ForgotPassword({ onBackToLogin, onSubmit }: Props) {
  const [phase, setPhase] = useState<Phase>('form');
  const [email, setEmail] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setPhase('loading');
    setErrorMsg('');
    try {
      const fn = onSubmit ?? defaultSendReset;
      const result = await fn(email.trim().toLowerCase());
      if (result.success) {
        setPhase('success');
      } else {
        setPhase('error');
        setErrorMsg(result.error ?? 'Something went wrong. Please try again.');
      }
    } catch {
      setPhase('error');
      setErrorMsg('Could not connect. Check that the server is running.');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Ctrl+Enter / Cmd+Enter shortcut
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
            <div className="sh-auth-success">Reset link sent! Check your email inbox.</div>
            <div className="sh-auth-info">Didn't receive it? Check your spam folder or try again.</div>
            <button
              className="sh-auth-btn"
              onClick={() => {
                setPhase('form');
                setEmail('');
                setErrorMsg('');
              }}
              type="button"
            >
              Send another
            </button>
            <div className="sh-auth-footer">
              <button className="sh-auth-link" onClick={onBackToLogin} type="button">
                Back to sign in
              </button>
            </div>
          </>
        )}

        {/* ── Success already shown above; form for 'form' | 'loading' | 'error' ── */}
        {(phase === 'form' || phase === 'loading' || phase === 'error') && (
          <>
            <div className="sh-auth-info">Enter your email and we'll send you a reset link.</div>

            <form className="sh-auth-form" onSubmit={handleSubmit} role="main" aria-label="Forgot password">
              <div className="sh-auth-field">
                <label htmlFor="forgot-email">Email</label>
                <input
                  id="forgot-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  autoFocus
                  disabled={phase === 'loading'}
                  aria-describedby={phase === 'error' ? 'forgot-error' : undefined}
                />
              </div>

              {phase === 'error' && (
                <div id="forgot-error" className="sh-auth-error" role="alert">
                  {errorMsg}
                </div>
              )}

              <button type="submit" className="sh-auth-btn" disabled={phase === 'loading' || !email.trim()}>
                {phase === 'loading' ? (
                  <>
                    <span className="sh-auth-spinner" />
                    Sending…
                  </>
                ) : (
                  'Send Reset Link'
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
