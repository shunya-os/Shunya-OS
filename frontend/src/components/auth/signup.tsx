/**
 * Sign Up — Creates a new SHUNYA account.
 *
 * States: form → loading → success / error.
 * Keyboard: autoFocus on name, Enter to submit, Tab through.
 * Responsive via shared authStyles.
 */

import { useState } from 'react';
import { authStyles } from './auth-styles';

interface Props {
  onBackToLogin: () => void;
  onSignupSuccess?: () => void;
  onSubmit?: (name: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>;
}

type Phase = 'form' | 'loading' | 'success' | 'error';

async function defaultSignup(name: string, email: string, password: string): Promise<{ success: boolean; error?: string }> {
  const resp = await fetch('/api/v1/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
    credentials: 'include',
  });
  const data = await resp.json();
  if (!resp.ok) return { success: false, error: data.error ?? 'Failed to create account.' };
  return { success: true };
}

export function Signup({ onBackToLogin, onSignupSuccess, onSubmit }: Props) {
  const [phase, setPhase] = useState<Phase>('form');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const getValidationError = (): string | null => {
    if (!name.trim()) return 'Name is required.';
    if (!email.trim()) return 'Email is required.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) return 'Enter a valid email address.';
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
      const fn = onSubmit ?? defaultSignup;
      const result = await fn(name.trim(), email.trim().toLowerCase(), password);
      if (result.success) {
        setPhase('success');
        onSignupSuccess?.();
      } else {
        setPhase('error');
        setErrorMsg(result.error ?? 'Failed to create account.');
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
              Account created! Check your email to verify your address.
            </div>
            <button className="sh-auth-btn" onClick={onBackToLogin} type="button" autoFocus>
              Sign in
            </button>
          </>
        )}

        {/* ── Form ── */}
        {(phase === 'form' || phase === 'loading' || phase === 'error') && (
          <>
            <form className="sh-auth-form" onSubmit={handleSubmit} role="main" aria-label="Create account">
              <div className="sh-auth-field">
                <label htmlFor="signup-name">Full name</label>
                <input
                  id="signup-name"
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Your name"
                  autoFocus
                  disabled={phase === 'loading'}
                  autoComplete="name"
                />
              </div>

              <div className="sh-auth-field">
                <label htmlFor="signup-email">Email</label>
                <input
                  id="signup-email"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  disabled={phase === 'loading'}
                  autoComplete="email"
                />
              </div>

              <div className="sh-auth-field">
                <label htmlFor="signup-password">Password</label>
                <input
                  id="signup-password"
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  disabled={phase === 'loading'}
                  autoComplete="new-password"
                />
              </div>

              <div className="sh-auth-field">
                <label htmlFor="signup-confirm">Confirm password</label>
                <input
                  id="signup-confirm"
                  type="password"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
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
                disabled={
                  phase === 'loading' ||
                  !name.trim() ||
                  !email.trim() ||
                  !password.trim() ||
                  !confirm.trim()
                }
              >
                {phase === 'loading' ? (
                  <><span className="sh-auth-spinner" />Creating account…</>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>

            <div className="sh-auth-divider">OR</div>

            <div className="sh-auth-footer">
              Already have an account?{' '}
              <button className="sh-auth-link" onClick={onBackToLogin} type="button" disabled={phase === 'loading'}>
                Sign in
              </button>
            </div>
          </>
        )}
      </div>

      <style>{authStyles}</style>
    </div>
  );
}
