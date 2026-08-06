/**
 * Login Page — Cinematic introduction for SHUNYA.
 *
 * First thing every founder sees. Dark, calm, intentional.
 * शून्य appears first. The story comes before the form.
 */

import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import { SessionManager, type Session } from '../../api/session';

interface Props {
  onLogin: (session: Session) => void;
}

export function LoginPage({ onLogin }: Props) {
  const [phase, setPhase] = useState<'intro' | 'form' | 'loading' | 'error'>('intro');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [showSub, setShowSub] = useState(false);
  const [showTagline, setShowTagline] = useState(false);

  // Cinematic introduction sequence
  useEffect(() => {
    if (phase !== 'intro') return;
    const t1 = setTimeout(() => setShowSub(true), 1200);
    const t2 = setTimeout(() => setShowTagline(true), 2400);
    const t3 = setTimeout(() => setPhase('form'), 4000);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
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
        setErrorMsg(resp.error ?? 'Sign in failed. Please check your credentials.');
      }
    } catch {
      setPhase('error');
      setErrorMsg('Could not connect. Check that the server is running.');
    }
  };

  const handleSkipIntro = () => {
    setPhase('form');
  };

  return (
    <div className="sh-cinematic">
      {phase === 'intro' && (
        <div className="sh-intro" onClick={handleSkipIntro}>
          <div className="sh-intro-zero">शून्य</div>
          {showSub && <div className="sh-intro-sub fade-in">SHUNYA</div>}
          {showTagline && <div className="sh-intro-tagline fade-in">One Operating System for Your Business</div>}
          <div className="sh-intro-skip">Tap to continue</div>
        </div>
      )}

      {(phase === 'form' || phase === 'loading' || phase === 'error') && (
        <div className="sh-login fade-in">
          <div className="sh-login-header">
            <div className="sh-login-zero">शून्य</div>
            <div className="sh-login-sub">SHUNYA</div>
          </div>
          <form className="sh-login-form" onSubmit={handleSubmit} role="main" aria-label="Sign in">
            <div className="sh-login-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                autoFocus
                disabled={phase === 'loading'}
              />
            </div>
            <div className="sh-login-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                disabled={phase === 'loading'}
              />
            </div>
            {phase === 'error' && (
              <div className="sh-login-error" role="alert">
                {errorMsg}
              </div>
            )}
            <button
              type="submit"
              className="sh-login-btn"
              disabled={phase === 'loading' || !email.trim() || !password.trim()}
            >
              {phase === 'loading' ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
          <div className="sh-login-footer">SHUNYA — One Operating System</div>
        </div>
      )}

      <style>{`
.sh-cinematic {
  position: fixed; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: #0a0a0f;
  color: #e0e0e0;
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
  overflow: hidden;
}
.sh-intro {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0; cursor: pointer; user-select: none;
  animation: sh-fade-in 1s ease-out;
}
.sh-intro-zero {
  font-size: clamp(3rem, 12vw, 8rem);
  font-weight: 300;
  color: #ffffff;
  letter-spacing: 0.05em;
  font-family: 'Noto Sans Devanagari', 'Segoe UI', sans-serif;
}
.sh-intro-sub {
  font-size: clamp(1.2rem, 4vw, 2.5rem);
  font-weight: 300;
  color: #888;
  letter-spacing: 0.3em;
  margin-top: 8px;
  text-transform: uppercase;
}
.sh-intro-tagline {
  font-size: clamp(0.8rem, 2vw, 1.1rem);
  color: #555;
  margin-top: 24px;
  letter-spacing: 0.05em;
}
.sh-intro-skip {
  position: absolute; bottom: 40px;
  font-size: 0.75rem; color: #333; letter-spacing: 0.1em;
}
.sh-login {
  display: flex; flex-direction: column; align-items: center;
  gap: 32px; width: 100%; max-width: 380px; padding: 24px;
}
.sh-login-header { text-align: center; }
.sh-login-zero { font-size: 2.5rem; color: #fff; font-weight: 300; }
.sh-login-sub { font-size: 0.85rem; color: #666; letter-spacing: 0.2em; text-transform: uppercase; margin-top: 4px; }
.sh-login-form { width: 100%; display: flex; flex-direction: column; gap: 16px; }
.sh-login-field label { display: block; font-size: 0.75rem; color: #888; margin-bottom: 4px; letter-spacing: 0.05em; }
.sh-login-field input {
  width: 100%; padding: 10px 14px;
  background: #1a1a24; border: 1px solid #2a2a3a; border-radius: 6px;
  color: #e0e0e0; font-size: 0.95rem; outline: none; transition: border-color 0.2s;
}
.sh-login-field input:focus { border-color: #555; }
.sh-login-field input:disabled { opacity: 0.5; }
.sh-login-error { font-size: 0.8rem; color: #f55; text-align: center; }
.sh-login-btn {
  width: 100%; padding: 10px 14px;
  background: #fff; color: #0a0a0f;
  border: none; border-radius: 6px; font-size: 0.95rem; font-weight: 500;
  cursor: pointer; transition: opacity 0.2s;
}
.sh-login-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-login-btn:hover:not(:disabled) { opacity: 0.85; }
.sh-login-footer { font-size: 0.7rem; color: #444; letter-spacing: 0.1em; }
.fade-in { animation: sh-fade-in 0.8s ease-out both; }
@keyframes sh-fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
`}</style>
    </div>
  );
}
