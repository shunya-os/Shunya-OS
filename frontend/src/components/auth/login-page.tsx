/**
 * Login Page — Canonical warm-light authentication.
 *
 * Visual Design Bible §6: Light mode only v1.0
 * Background: #fbfaf8, Card: #ffffff
 * Gold dot for identity. Dark text buttons.
 *
 * Directive §17: Public → authenticated continuity.
 */

import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import { SessionManager, type Session } from '../../api/session';
import { authStyles } from './auth-styles';

interface Props {
  onLogin: (session: Session) => void;
  onSignUp?: () => void;
}

export function LoginPage({ onLogin, onSignUp }: Props) {
  const [phase, setPhase] = useState<'intro' | 'form' | 'loading' | 'error'>('intro');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [showSub, setShowSub] = useState(false);
  const [showTagline, setShowTagline] = useState(false);

  useEffect(() => {
    if (phase !== 'intro') return;
    const t1 = setTimeout(() => setShowSub(true), 1200);
    const t2 = setTimeout(() => setShowTagline(true), 2400);
    const t3 = setTimeout(() => setPhase('form'), 4000);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [phase]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;
    setPhase('loading');
    setErrorMsg('');
    try {
      const resp = await api.signin(email.trim().toLowerCase(), password);
      if (resp.success) {
        const session: Session = { identityId: resp.identity_id || '', email: email.trim().toLowerCase() };
        SessionManager.save(session);
        // If user already has workspace/org, skip onboarding
        if (resp.onboarding_complete) {
          window.sessionStorage.setItem('shunya_onboarding_complete', 'true');
          window.localStorage.setItem('shunya_onboarding_complete', 'true');
        }
        onLogin(session);
      } else {
        setPhase('error');
        setErrorMsg(resp.error ?? 'Sign in failed.');
      }
    } catch {
      setPhase('error');
      setErrorMsg('Could not connect.');
    }
  };

  const handleSkipIntro = () => setPhase('form');

  return (
    <div className="sh-cinematic">
      {phase === 'intro' && (
        <div className="sh-intro" onClick={handleSkipIntro}>
          <div className="sh-intro-dot" aria-hidden="true" />
          <div className="sh-intro-zero">शून्य</div>
          {showSub && <div className="sh-intro-sub fade-in">SHUNYA</div>}
          {showTagline && <div className="sh-intro-tagline fade-in">Infinite Intelligence. Zero Noise.</div>}
          <div className="sh-intro-skip">Tap to continue</div>
        </div>
      )}

      {(phase === 'form' || phase === 'loading' || phase === 'error') && (
        <div className="sh-auth">
          <div className="sh-auth-card sh-auth-fade-in">
            <div className="sh-auth-header">
              <div className="sh-auth-zero">शून्य</div>
              <div className="sh-auth-sub">SHUNYA</div>
              <div className="sh-auth-gold-dot" aria-hidden="true" />
            </div>
            <form className="sh-auth-form" onSubmit={handleSubmit} role="main" aria-label="Sign in">
              <div className="sh-auth-field">
                <label htmlFor="email">Email</label>
                <input id="email" type="email" value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@company.com" autoFocus
                  disabled={phase === 'loading'} />
              </div>
              <div className="sh-auth-field">
                <label htmlFor="password">Password</label>
                <input id="password" type="password" value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  disabled={phase === 'loading'} />
              </div>
              {phase === 'error' && <div className="sh-auth-error" role="alert">{errorMsg}</div>}
              <button className="sh-auth-btn" type="submit"
                disabled={phase === 'loading' || !email.trim() || !password.trim()}>
                {phase === 'loading' ? 'Signing in\u2026' : 'Sign In'}
              </button>
            </form>
            <div className="sh-auth-footer">
              <span onClick={() => window.location.href = '/auth/forgot-password'} className="sh-auth-link">
                Forgot password?
              </span>
              {onSignUp && (
                <>
                  <span style={{margin: '0 8px', color: 'var(--shunya-border, rgba(26,28,29,0.07))'}}>·</span>
                  <span onClick={onSignUp} className="sh-auth-link">Create account</span>
                </>
              )}
            </div>

            {/* ── OAuth Login ── */}
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
          </div>
          <style>{authStyles}</style>
        </div>
      )}

      <style>{`
.sh-cinematic {
  position: fixed; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--shunya-bg, #FBF8F5);
  color: var(--shunya-text, #1A1C1D);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
}
.sh-intro {
  text-align: center; cursor: pointer; padding: 40px;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.sh-intro-dot {
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--shunya-gold, #A4865F); margin-bottom: 8px;
}
.sh-intro-zero {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 3.5rem; font-weight: 400;
  letter-spacing: var(--shunya-tracking-wider, 0.06em);
  color: var(--shunya-text, #1A1C1D);
}
.sh-intro-sub {
  font-family: var(--shunya-font-display, 'Playfair Display', serif);
  font-size: 2rem; font-weight: 400;
  letter-spacing: var(--shunya-tracking-tight, -0.025em);
  color: var(--shunya-text, #1A1C1D); margin-top: 4px;
}
.sh-intro-tagline {
  font-family: var(--shunya-font-display, 'Playfair Display', serif);
  font-size: 0.95rem; font-weight: 400; font-style: italic;
  letter-spacing: var(--shunya-tracking-ultra, 0.2em);
  text-transform: uppercase; color: var(--shunya-gold-accessible, #7A6848); margin-top: 12px;
}
.sh-intro-skip {
  margin-top: 32px; font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, #888888);
  letter-spacing: var(--shunya-tracking-wider, 0.06em);
}
.fade-in {
  animation: sh-intro-fade var(--shunya-duration-slow, 600ms) var(--shunya-ease-out, cubic-bezier(0.16,1,0.3,1)) both;
}
@keyframes sh-intro-fade {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: reduce) {
  .fade-in { animation: none; opacity: 1; }
}
      `}</style>
    </div>
  );
}