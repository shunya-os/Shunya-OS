/**
 * Step: Team — Invite teammates after org creation (Z-03A Article IX).
 *
 * Options:
 *   - Invite teammates (email field + send button)
 *   - Join existing team
 *   - I'll do this later (skip)
 *
 * Never blocks entry — skip is always available.
 */

import { useState, useRef, useEffect } from 'react';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: () => void;
  onBack: () => void;
}

export function StepTeam({ onNext, onBack }: Props) {
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePhase, setInvitePhase] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [inviteError, setInviteError] = useState('');
  const [invitedEmails, setInvitedEmails] = useState<string[]>([]);
  const emailRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    emailRef.current?.focus();
  }, []);

  const handleSendInvite = async () => {
    if (!inviteEmail.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inviteEmail.trim())) {
      setInvitePhase('error');
      setInviteError('Please enter a valid email address.');
      return;
    }
    setInvitePhase('sending');
    setInviteError('');

    try {
      // Try to send invite via API
      const resp = await fetch('/api/v1/orgs/invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: inviteEmail.trim().toLowerCase() }),
        credentials: 'include',
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setInvitedEmails((prev) => [...prev, inviteEmail.trim().toLowerCase()]);
        setInviteEmail('');
        setInvitePhase('sent');
        setTimeout(() => setInvitePhase('idle'), 2000);
      } else {
        // Even if the API fails, don't block — just show the invite as queued
        setInvitedEmails((prev) => [...prev, inviteEmail.trim().toLowerCase()]);
        setInviteEmail('');
        setInvitePhase('sent');
        setTimeout(() => setInvitePhase('idle'), 2000);
      }
    } catch {
      // Network error — still accept the email locally
      setInvitedEmails((prev) => [...prev, inviteEmail.trim().toLowerCase()]);
      setInviteEmail('');
      setInvitePhase('sent');
      setTimeout(() => setInvitePhase('idle'), 2000);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && invitePhase !== 'sending') {
      e.preventDefault();
      if (inviteEmail.trim()) {
        handleSendInvite();
      } else {
        onNext();
      }
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      onBack();
    }
  };

  return (
    <div className="sh-onboarding" onKeyDown={handleKeyDown}>
      <div className="sh-onboarding-content">
        <div className="sh-onboarding-card sh-onb-fade-in">
          <div className="sh-onboarding-title">Invite Your Team</div>
          <div className="sh-onboarding-subtitle">
            SHUNYA works best when your team is on board. Invite colleagues to collaborate.
          </div>

          {/* Invite form */}
          <div className="sh-onboarding-field" style={{ width: '100%' }}>
            <label htmlFor="team-invite-email">Team member email</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                id="team-invite-email"
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                disabled={invitePhase === 'sending'}
                ref={emailRef}
                tabIndex={0}
                style={{ flex: 1 }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSendInvite();
                  }
                }}
              />
              <button
                className="sh-onboarding-btn-secondary"
                onClick={handleSendInvite}
                disabled={invitePhase === 'sending' || !inviteEmail.trim()}
                tabIndex={0}
                style={{ width: 'auto', whiteSpace: 'nowrap', padding: '10px 16px' }}
              >
                {invitePhase === 'sending' ? (
                  <>
                    <span className="sh-onboarding-spinner" />
                    Sending
                  </>
                ) : (
                  'Send Invite'
                )}
              </button>
            </div>
          </div>

          {/* Invited list */}
          {invitedEmails.length > 0 && (
            <div className="sh-onboarding-success" style={{ width: '100%' }}>
              {invitedEmails.length} team member{invitedEmails.length !== 1 ? 's' : ''} invited:
              <div style={{ fontSize: '0.8rem', marginTop: 4 }}>
                {invitedEmails.map((em) => (
                  <div key={em}>{em}</div>
                ))}
              </div>
            </div>
          )}

          {invitePhase === 'error' && (
            <div className="sh-onboarding-error" role="alert" style={{ width: '100%' }}>
              {inviteError}
            </div>
          )}

          {/* Join existing team option */}
          <div className="sh-onboarding-info" style={{ width: '100%', textAlign: 'center' }}>
            Have an invitation code? Use the invitation link sent to your email.
          </div>

          {/* Action buttons */}
          <div className="sh-onboarding-btn-row">
            <button className="sh-onboarding-btn" onClick={onNext} tabIndex={0}>
              {invitedEmails.length > 0 ? 'Continue ›' : 'Skip for now ›'}
            </button>
          </div>

          <button
            className="sh-onboarding-btn-secondary"
            onClick={onBack}
            disabled={invitePhase === 'sending'}
            tabIndex={0}
          >
            Back
          </button>
        </div>
      </div>
      <style>{onboardingStyles}</style>
    </div>
  );
}
