/**
 * SHUNYA — MFA Setup Component
 *
 * Two-factor authentication using TOTP (Google Authenticator, Authy, etc.).
 * Wired into the Settings panel Security tab.
 *
 * Backend endpoints:
 *   GET  /auth/mfa/status    — check MFA status
 *   POST /auth/mfa/setup     — generate secret + QR URI
 *   POST /auth/mfa/verify    — verify TOTP code to enable
 *   POST /auth/mfa/disable   — disable MFA (requires password)
 */

import { useState, useEffect } from 'react';

interface MfaStatus {
  enabled: boolean;
  configured: boolean;
}

interface SetupData {
  secret: string;
  uri: string;
  recovery_codes: string[];
}

export function MfaSetup() {
  const [status, setStatus] = useState<MfaStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [phase, setPhase] = useState<'idle' | 'setup' | 'verify' | 'done'>('idle');
  const [setupData, setSetupData] = useState<SetupData | null>(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [verifyError, setVerifyError] = useState('');
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');
  const [disableError, setDisableError] = useState('');
  const [disableLoading, setDisableLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/auth/mfa/status', { credentials: 'include' })
      .then(r => r.json())
      .then(json => {
        if (json.success) setStatus(json.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSetup = async () => {
    setError('');
    try {
      const resp = await fetch('/auth/mfa/setup', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      const json = await resp.json();
      if (json.success) {
        setSetupData(json.data);
        setPhase('setup');
      } else {
        setError(json.error || 'Setup failed');
      }
    } catch {
      setError('Could not connect');
    }
  };

  const handleVerify = async () => {
    if (verifyCode.length !== 6) return;
    setVerifyError('');
    setVerifyLoading(true);
    try {
      const resp = await fetch('/auth/mfa/verify', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: verifyCode }),
      });
      const json = await resp.json();
      if (json.success) {
        setPhase('done');
        setStatus({ enabled: true, configured: true });
      } else {
        setVerifyError(json.error || 'Invalid code');
      }
    } catch {
      setVerifyError('Could not connect');
    } finally {
      setVerifyLoading(false);
    }
  };

  const handleDisable = async () => {
    if (!disablePassword) return;
    setDisableError('');
    setDisableLoading(true);
    try {
      const resp = await fetch('/auth/mfa/disable', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: disablePassword }),
      });
      const json = await resp.json();
      if (json.success) {
        setStatus({ enabled: false, configured: false });
        setPhase('idle');
        setSetupData(null);
        setDisablePassword('');
      } else {
        setDisableError(json.error || 'Invalid password');
      }
    } catch {
      setDisableError('Could not connect');
    } finally {
      setDisableLoading(false);
    }
  };

  if (loading) {
    return <div className="mfa-section"><div className="mfa-loading">Loading...</div></div>;
  }

  if (status?.enabled) {
    return (
      <div className="mfa-section">
        <div className="mfa-section-title">Two-Factor Authentication</div>
        <div className="mfa-status-badge mfa-enabled">✓ Enabled</div>
        <p className="mfa-description">Your account is protected with TOTP two-factor authentication.</p>
        <div className="mfa-disable-form">
          <input
            type="password"
            className="mfa-input"
            placeholder="Enter your password to disable"
            value={disablePassword}
            onChange={(e) => setDisablePassword(e.target.value)}
          />
          <button
            className="mfa-btn mfa-btn-danger"
            onClick={handleDisable}
            disabled={disableLoading || !disablePassword}
          >
            {disableLoading ? 'Disabling...' : 'Disable MFA'}
          </button>
          {disableError && <div className="mfa-error">{disableError}</div>}
        </div>
      </div>
    );
  }

  if (phase === 'done') {
    return (
      <div className="mfa-section">
        <div className="mfa-section-title">Two-Factor Authentication</div>
        <div className="mfa-status-badge mfa-enabled">✓ Enabled</div>
        <p className="mfa-description">MFA is now active. Keep your recovery codes safe.</p>
      </div>
    );
  }

  if (phase === 'setup' && setupData) {
    return (
      <div className="mfa-section">
        <div className="mfa-section-title">Set Up Two-Factor Authentication</div>
        <div className="mfa-setup-steps">
          <div className="mfa-step">
            <div className="mfa-step-num">1</div>
            <div className="mfa-step-body">
              <div className="mfa-step-label">Scan this QR code with your authenticator app</div>
              <div className="mfa-qr-info">
                <div className="mfa-secret-box">
                  <span className="mfa-secret-label">Manual entry code:</span>
                  <code className="mfa-secret">{setupData.secret}</code>
                </div>
                <div className="mfa-uri-box">
                  <span className="mfa-secret-label">Or open this URI:</span>
                  <code className="mfa-uri-small">{setupData.uri.slice(0, 60)}...</code>
                </div>
              </div>
            </div>
          </div>
          <div className="mfa-step">
            <div className="mfa-step-num">2</div>
            <div className="mfa-step-body">
              <div className="mfa-step-label">Enter the 6-digit code from your authenticator app</div>
              <div className="mfa-verify-row">
                <input
                  type="text"
                  className="mfa-input mfa-code-input"
                  placeholder="000000"
                  maxLength={6}
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ''))}
                />
                <button
                  className="mfa-btn mfa-btn-primary"
                  onClick={handleVerify}
                  disabled={verifyLoading || verifyCode.length !== 6}
                >
                  {verifyLoading ? 'Verifying...' : 'Verify & Enable'}
                </button>
              </div>
              {verifyError && <div className="mfa-error">{verifyError}</div>}
            </div>
          </div>
          <div className="mfa-step">
            <div className="mfa-step-num">3</div>
            <div className="mfa-step-body">
              <div className="mfa-step-label">Save your recovery codes</div>
              <div className="mfa-recovery-codes">
                {setupData.recovery_codes.map((code, i) => (
                  <code key={i} className="mfa-recovery-code">{code}</code>
                ))}
              </div>
              <p className="mfa-warning">These codes can only be used once. Save them somewhere safe.</p>
            </div>
          </div>
        </div>
        {error && <div className="mfa-error">{error}</div>}
      </div>
    );
  }

  return (
    <div className="mfa-section">
      <div className="mfa-section-title">Two-Factor Authentication</div>
      <div className="mfa-status-badge mfa-disabled">○ Not Enabled</div>
      <p className="mfa-description">
        Add an extra layer of security to your account by enabling two-factor authentication.
        Use any TOTP-compatible authenticator app (Google Authenticator, Authy, etc.).
      </p>
      <button className="mfa-btn mfa-btn-primary" onClick={handleSetup}>
        Set Up MFA
      </button>
      {error && <div className="mfa-error">{error}</div>}
      <style>{`
.mfa-section {
  background: var(--shunya-surface-2, #1a1a26);
  border: 1px solid var(--shunya-surface-1, #22222e);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
}
.mfa-section-title {
  font-size: 14px; font-weight: 600;
  color: var(--shunya-text, #e0e0e0);
  margin-bottom: 12px;
}
.mfa-status-badge {
  display: inline-block;
  font-size: 12px; font-weight: 500;
  padding: 4px 10px; border-radius: 6px;
  margin-bottom: 12px;
}
.mfa-enabled { background: rgba(16,185,129,0.15); color: #34d399; }
.mfa-disabled { background: rgba(100,116,139,0.15); color: #94a3b8; }
.mfa-description { font-size: 13px; color: var(--shunya-text-secondary, #888); line-height: 1.5; margin-bottom: 16px; }
.mfa-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 8px;
  font-size: 13px; font-weight: 500; cursor: pointer;
  border: 1px solid transparent; transition: all 0.15s;
}
.mfa-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.mfa-btn-primary { background: #6C4AE2; color: #fff; }
.mfa-btn-primary:hover:not(:disabled) { background: #5a3dcc; }
.mfa-btn-danger { background: rgba(239,68,68,0.15); color: #f88; border-color: rgba(239,68,68,0.3); }
.mfa-btn-danger:hover:not(:disabled) { background: rgba(239,68,68,0.25); }
.mfa-input {
  background: var(--shunya-surface-1, #22222e);
  border: 1px solid var(--shunya-border, #334155);
  border-radius: 6px; padding: 8px 12px;
  color: var(--shunya-text, #e0e0e0); font-size: 13px;
  outline: none; width: 100%;
}
.mfa-input:focus { border-color: #6C4AE2; }
.mfa-code-input { width: 140px; text-align: center; font-size: 18px; letter-spacing: 6px; font-family: monospace; }
.mfa-error { font-size: 12px; color: #f88; margin-top: 8px; }
.mfa-disable-form { display: flex; flex-direction: column; gap: 8px; }
.mfa-setup-steps { display: flex; flex-direction: column; gap: 16px; }
.mfa-step { display: flex; gap: 12px; }
.mfa-step-num {
  width: 28px; height: 28px; border-radius: 50%;
  background: #6C4AE2; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 600; flex-shrink: 0;
}
.mfa-step-body { flex: 1; }
.mfa-step-label { font-size: 13px; color: var(--shunya-text, #e0e0e0); margin-bottom: 8px; }
.mfa-secret-box, .mfa-uri-box { margin-bottom: 8px; }
.mfa-secret-label { display: block; font-size: 11px; color: var(--shunya-text-secondary, #888); margin-bottom: 4px; }
.mfa-secret {
  font-size: 14px; font-family: monospace;
  background: var(--shunya-surface-1, #22222e);
  padding: 6px 10px; border-radius: 4px;
  color: var(--shunya-text, #e0e0e0); word-break: break-all;
}
.mfa-uri-small { font-size: 11px; word-break: break-all; color: var(--shunya-text-secondary, #888); }
.mfa-verify-row { display: flex; gap: 8px; align-items: center; }
.mfa-recovery-codes {
  display: flex; flex-wrap: wrap; gap: 6px;
  margin-bottom: 8px;
}
.mfa-recovery-code {
  font-size: 13px; font-family: monospace;
  background: rgba(16,185,129,0.1);
  border: 1px solid rgba(16,185,129,0.2);
  color: #34d399; padding: 4px 8px; border-radius: 4px;
}
.mfa-warning { font-size: 12px; color: var(--shunya-text-secondary, #888); }
.mfa-loading { padding: 20px; text-align: center; color: var(--shunya-text-secondary, #888); }
      `}</style>
    </div>
  );
}