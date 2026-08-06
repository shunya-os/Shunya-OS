/**
 * Verify Email — Verifies an email address via a token.
 *
 * States: verifying (loading) → verified (success) / error.
 * On mount, immediately attempts verification with the provided token.
 * Keyboard: autoFocus on action buttons after verification.
 * Responsive via shared authStyles.
 */

import { useState, useEffect } from 'react';
import { authStyles } from './auth-styles';

interface Props {
  token: string;
  onBackToLogin: () => void;
  onSubmit?: (token: string) => Promise<{ success: boolean; error?: string }>;
}

type Phase = 'verifying' | 'success' | 'error';

async function defaultVerifyEmail(token: string): Promise<{ success: boolean; error?: string }> {
  const resp = await fetch('/api/v1/auth/verify-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
    credentials: 'include',
  });
  const data = await resp.json();
  if (!resp.ok) return { success: false, error: data.error ?? 'Verification failed.' };
  return { success: true };
}

export function VerifyEmail({ token, onBackToLogin, onSubmit }: Props) {
  const [phase, setPhase] = useState<Phase>('verifying');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    let cancelled = false;
    const fn = onSubmit ?? defaultVerifyEmail;
    fn(token)
      .then((result) => {
        if (cancelled) return;
        if (result.success) {
          setPhase('success');
        } else {
          setPhase('error');
          setErrorMsg(result.error ?? 'Verification failed. The link may have expired.');
        }
      })
      .catch(() => {
        if (cancelled) return;
        setPhase('error');
        setErrorMsg('Could not connect. Check that the server is running.');
      });
    return () => {
      cancelled = true;
    };
  }, [token, onSubmit]);

  const handleRetry = () => {
    setPhase('verifying');
    setErrorMsg('');
    const fn = onSubmit ?? defaultVerifyEmail;
    fn(token)
      .then((result) => {
        if (result.success) {
          setPhase('success');
        } else {
          setPhase('error');
          setErrorMsg(result.error ?? 'Verification failed. The link may have expired.');
        }
      })
      .catch(() => {
        setPhase('error');
        setErrorMsg('Could not connect. Check that the server is running.');
      });
  };

  return (
    <div className="sh-auth">
      <div className="sh-auth-card sh-auth-fade-in">
        {/* ── Header ── */}
        <div className="sh-auth-header">
          <div className="sh-auth-zero">शून्य</div>
          <div className="sh-auth-sub">SHUNYA</div>
        </div>

        {/* ── Verifying (loading) ── */}
        {phase === 'verifying' && (
          <>
            <div className="sh-auth-spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
            <div className="sh-auth-info">Verifying your email address…</div>
          </>
        )}

        {/* ── Success ── */}
        {phase === 'success' && (
          <>
            <div className="sh-auth-success">Email verified successfully!</div>
            <button className="sh-auth-btn" onClick={onBackToLogin} type="button" autoFocus>
              Sign in
            </button>
          </>
        )}

        {/* ── Error ── */}
        {phase === 'error' && (
          <>
            <div className="sh-auth-error" role="alert">
              {errorMsg}
            </div>
            <div className="sh-auth-info">
              The verification link may have expired. You can request a new one from your account settings.
            </div>
            <button className="sh-auth-btn" onClick={handleRetry} type="button">
              Try again
            </button>
            <div className="sh-auth-footer">
              <button className="sh-auth-link" onClick={onBackToLogin} type="button">
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
