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

                {/* Divider + future social auth slot */}
                <div className="sh-auth-divider">OR</div>

                {/* Future: Magic Link / Social Auth */}
                <div
                  className="sh-auth-social"
                  style={{ width: '100%', textAlign: 'center', fontSize: '0.75rem', color: '#555' }}
                >
                  Social login and Magic Link coming soon.
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
