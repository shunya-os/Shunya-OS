/**
 * UnifiedAuth — Single auth page combining Sign In, Sign Up, and Forgot Password.
 *
 * Z-03A Articles IV-V: Unified authentication with inline toggle.
 * Future-ready: slots for Magic Link and Social auth.
 * Browser Back button works naturally (no broken history).
 */

import { useState, useRef, useEffect } from 'react';
import { authStyles } from './auth-styles';

type AuthMode = 'signin' | 'signup' | 'forgot';
type Phase = 'form' | 'loading' | 'success' | 'error';

interface Props {
  initialMode?: AuthMode;
  onSubmit?: (
    name: string | undefined,
    email: string,
    password: string,
    mode: 'signin' | 'signup',
  ) => Promise<{ success: boolean; error?: string }>;
  onForgotPassword?: (email: string) => Promise<{ success: boolean; error?: string }>;
}

function getValidationError(
  name: string | undefined,
  email: string,
  password: string,
  confirm: string,
  mode: AuthMode,
): string | null {
  if (!email.trim()) return 'Email is required.';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) return 'Enter a valid email address.';
  if (mode === 'signup') {
    if (!name?.trim()) return 'Name is required.';
    if (password.length < 8) return 'Password must be at least 8 characters.';
    if (password !== confirm) return 'Passwords do not match.';
  }
  if (mode === 'signin' && !password.trim()) return 'Password is required.';
  return null;
}

export function UnifiedAuth({ initialMode, onSubmit, onForgotPassword }: Props) {
  const [mode, setMode] = useState<AuthMode>(initialMode || 'signin');
  const [phase, setPhase] = useState<Phase>('form');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [showForgot, setShowForgot] = useState(initialMode === 'forgot');
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotPhase, setForgotPhase] = useState<'idle' | 'loading' | 'sent' | 'error'>('idle');
  const [forgotError, setForgotError] = useState('');
  const emailRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    emailRef.current?.focus();
  }, [mode]);

  const handleModeSwitch = (newMode: AuthMode) => {
    setMode(newMode);
    setPhase('form');
    setErrorMsg('');
    setSuccessMsg('');
    setShowForgot(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErr = getValidationError(mode === 'signup' ? name : undefined, email, password, confirm, mode);
    if (validationErr) {
      setPhase('error');
      setErrorMsg(validationErr);
      return;
    }
    setPhase('loading');
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const fn = onSubmit;
      if (!fn) {
        // Default inline submission
        const endpoint = mode === 'signin' ? '/api/v1/founder/signin' : '/api/v1/founder/signup';
        const body =
          mode === 'signin'
            ? JSON.stringify({ email: email.trim().toLowerCase(), password })
            : JSON.stringify({ name: name.trim(), email: email.trim().toLowerCase(), password });
        const resp = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body,
          credentials: 'include',
        });
        const data = await resp.json();
        if (data.success) {
          setPhase('success');
          if (mode === 'signup') {
            setSuccessMsg('Account created! Check your email to verify your address.');
          }
        } else {
          setPhase('error');
          setErrorMsg(data.error ?? (mode === 'signin' ? 'Sign in failed.' : 'Failed to create account.'));
        }
      } else {
        const result = await fn(
          mode === 'signup' ? name.trim() : undefined,
          email.trim().toLowerCase(),
          password,
          mode === 'signup' ? 'signup' : 'signin',
        );
        if (result.success) {
          setPhase('success');
          if (mode === 'signup') {
            setSuccessMsg('Account created! Check your email to verify your address.');
          }
        } else {
          setPhase('error');
          setErrorMsg(result.error ?? (mode === 'signin' ? 'Sign in failed.' : 'Failed to create account.'));
        }
      }
    } catch {
      setPhase('error');
      setErrorMsg('Could not connect. Check that the server is running.');
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotEmail.trim()) {
      setForgotPhase('error');
      setForgotError('Please enter your email address.');
      return;
    }
    setForgotPhase('loading');
    setForgotError('');

    try {
      const fn = onForgotPassword;
      if (fn) {
        const result = await fn(forgotEmail.trim().toLowerCase());
        if (result.success) {
          setForgotPhase('sent');
        } else {
          setForgotPhase('error');
          setForgotError(result.error ?? 'Failed to send reset email.');
        }
      } else {
        const resp = await fetch('/api/v1/auth/forgot-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: forgotEmail.trim().toLowerCase() }),
          credentials: 'include',
        });
        const data = await resp.json();
        if (data.success) {
          setForgotPhase('sent');
        } else {
          setForgotPhase('error');
          setForgotError(data.error ?? 'Failed to send reset email.');
        }
      }
    } catch {
      setForgotPhase('error');
      setForgotError('Could not connect. Check that the server is running.');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && mode !== 'forgot') {
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

        {/* ── Tab Toggle ── */}
        {!showForgot && (
          <div className="sh-auth-tabs" role="tablist" aria-label="Authentication mode">
            <button
              className={`sh-auth-tab ${mode === 'signin' ? 'active' : ''}`}
              onClick={() => handleModeSwitch('signin')}
              role="tab"
              aria-selected={mode === 'signin'}
              disabled={phase === 'loading'}
              tabIndex={0}
            >
              Sign In
            </button>
            <button
              className={`sh-auth-tab ${mode === 'signup' ? 'active' : ''}`}
              onClick={() => handleModeSwitch('signup')}
              role="tab"
              aria-selected={mode === 'signup'}
              disabled={phase === 'loading'}
              tabIndex={0}
            >
              Create Account
            </button>
          </div>
        )}

        {/* ── Forgot Password ── */}
        {showForgot && (
          <div style={{ width: '100%' }}>
            <form className="sh-auth-form" onSubmit={handleForgotSubmit} role="main" aria-label="Reset password">
              {forgotPhase === 'sent' ? (
                <>
                  <div className="sh-auth-success" role="status">
                    If an account exists with that email, we've sent a password reset link.
                  </div>
                  <button
                    className="sh-auth-btn"
                    onClick={() => {
                      setShowForgot(false);
                      setForgotPhase('idle');
                      setMode('signin');
                    }}
                    type="button"
                    tabIndex={0}
                  >
                    Back to Sign In
                  </button>
                </>
              ) : (
                <>
                  <div className="sh-auth-field">
                    <label htmlFor="forgot-email">Email</label>
                    <input
                      id="forgot-email"
                      type="email"
                      value={forgotEmail}
                      onChange={(e) => setForgotEmail(e.target.value)}
                      placeholder="you@company.com"
                      autoFocus
                      disabled={forgotPhase === 'loading'}
                      autoComplete="email"
                    />
                  </div>
                  {forgotPhase === 'error' && (
                    <div className="sh-auth-error" role="alert">
                      {forgotError}
                    </div>
                  )}
                  <button
                    type="submit"
                    className="sh-auth-btn"
                    disabled={forgotPhase === 'loading' || !forgotEmail.trim()}
                    tabIndex={0}
                  >
                    {forgotPhase === 'loading' ? (
                      <>
                        <span className="sh-auth-spinner" />
                        Sending…
                      </>
                    ) : (
                      'Send Reset Link'
                    )}
                  </button>
                  <button
                    className="sh-auth-btn-secondary"
                    onClick={() => {
                      setShowForgot(false);
                      setForgotPhase('idle');
                      setMode('signin');
                    }}
                    type="button"
                    disabled={forgotPhase === 'loading'}
                    tabIndex={0}
                  >
                    Back to Sign In
                  </button>
                </>
              )}
            </form>
          </div>
        )}

        {/* ── Sign In / Sign Up Form ── */}
        {!showForgot && (
          <>
            {/* Success message for signup */}
            {phase === 'success' && mode === 'signup' && (
              <>
                <div className="sh-auth-success" role="status">
                  {successMsg}
                </div>
                <button
                  className="sh-auth-btn"
                  onClick={() => handleModeSwitch('signin')}
                  type="button"
                  autoFocus
                  tabIndex={0}
                >
                  Sign in
                </button>
              </>
            )}

            {(phase !== 'success' || mode === 'signin') && (
              <>
                <form
                  className="sh-auth-form"
                  onSubmit={handleSubmit}
                  role="main"
                  aria-label={mode === 'signin' ? 'Sign in' : 'Create account'}
                >
                  {mode === 'signup' && (
                    <div className="sh-auth-field">
                      <label htmlFor="ua-name">Full name</label>
                      <input
                        id="ua-name"
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Your name"
                        disabled={phase === 'loading'}
                        autoComplete="name"
                        ref={mode === 'signup' ? emailRef : undefined}
                        tabIndex={0}
                      />
                    </div>
                  )}

                  <div className="sh-auth-field">
                    <label htmlFor="ua-email">Email</label>
                    <input
                      id="ua-email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@company.com"
                      disabled={phase === 'loading'}
                      autoComplete="email"
                      ref={mode === 'signin' ? emailRef : undefined}
                      tabIndex={0}
                    />
                  </div>

                  <div className="sh-auth-field">
                    <label htmlFor="ua-password">Password</label>
                    <input
                      id="ua-password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={mode === 'signup' ? 'At least 8 characters' : 'Enter your password'}
                      disabled={phase === 'loading'}
                      autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                      tabIndex={0}
                    />
                  </div>

                  {mode === 'signup' && (
                    <div className="sh-auth-field">
                      <label htmlFor="ua-confirm">Confirm password</label>
                      <input
                        id="ua-confirm"
                        type="password"
                        value={confirm}
                        onChange={(e) => setConfirm(e.target.value)}
                        placeholder="Re-enter password"
                        disabled={phase === 'loading'}
                        autoComplete="new-password"
                        tabIndex={0}
                      />
                    </div>
                  )}

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
                      !email.trim() ||
                      !password.trim() ||
                      (mode === 'signup' && (!name.trim() || !confirm.trim()))
                    }
                    tabIndex={0}
                  >
                    {phase === 'loading' ? (
                      <>
                        <span className="sh-auth-spinner" />
                        {mode === 'signin' ? 'Signing in…' : 'Creating account…'}
                      </>
                    ) : mode === 'signin' ? (
                      'Sign In'
                    ) : (
                      'Create Account'
                    )}
                  </button>
                </form>

                {/* Forgot password link */}
                {mode === 'signin' && (
                  <button
                    className="sh-auth-link"
                    onClick={() => {
                      setShowForgot(true);
                      setForgotEmail(email);
                      setForgotPhase('idle');
                    }}
                    type="button"
                    disabled={phase === 'loading'}
                    tabIndex={0}
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--sh-gold, #A4865F)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: 0,
                    }}
                  >
                    Forgot password?
                  </button>
                )}

                {/* Divider + Social Auth */}
                <div className="sh-auth-divider">OR</div>
                <div className="sh-auth-oauth">
                  <button
                    className="sh-auth-btn-oauth sh-auth-btn-oauth--google"
                    onClick={() => window.location.href = '/api/v1/auth/google/login'}
                    type="button"
                    disabled={phase === 'loading'}
                  >
                    <svg className="sh-auth-oauth-icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                    <span>Sign in with Google</span>
                  </button>
                  <button
                    className="sh-auth-btn-oauth sh-auth-btn-oauth--github"
                    onClick={() => window.location.href = '/api/v1/auth/github/login'}
                    type="button"
                    disabled={phase === 'loading'}
                  >
                    <svg className="sh-auth-oauth-icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                      <path fill="currentColor" d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
                    </svg>
                    <span>Sign in with GitHub</span>
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </div>

      <style>{authStyles}</style>
    </div>
  );
}
