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
  text-transform: uppercase; color: var(--shunya-gold, #A4865F); margin-top: 12px;
}
.sh-intro-skip {
  margin-top: 32px; font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
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