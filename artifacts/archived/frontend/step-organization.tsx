/**
 * Step 2: Organization Setup — Create the founder's organization.
 *
 * States: form → loading → error / success (auto-advance).
 * Form with company name, business type dropdown.
 * Creates org via POST /api/v1/orgs.
 */

import { useState, useEffect, useRef } from 'react';
import { api } from '../../api/client';
import { SessionManager } from '../../api/session';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: (orgInfo: { orgId: string; orgName: string }) => void;
  onBack: () => void;
}

const BUSINESS_TYPES = [
  'Technology',
  'Consulting',
  'Healthcare',
  'Finance',
  'Real Estate',
  'Education',
  'Other',
];

type Phase = 'form' | 'loading' | 'error' | 'success';

export function StepOrganization({ onNext, onBack }: Props) {
  const [phase, setPhase] = useState<Phase>('form');
  const [companyName, setCompanyName] = useState('');
  const [businessType, setBusinessType] = useState('Technology');
  const [errorMsg, setErrorMsg] = useState('');
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    nameRef.current?.focus();
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!companyName.trim()) {
      setPhase('error');
      setErrorMsg('Please enter a company name.');
      return;
    }
    setPhase('loading');
    setErrorMsg('');

    try {
      const resp = await api.createOrg(companyName.trim(), businessType);
      if (resp.success && resp.org_id) {
        // Update session with org info
        const session = SessionManager.load();
        if (session) {
          session.orgId = resp.org_id;
          session.orgName = resp.org_name || companyName.trim();
          SessionManager.save(session);
        }

        setPhase('success');
        // Auto-advance after a brief pause
        setTimeout(() => {
          onNext({ orgId: resp.org_id!, orgName: resp.org_name || companyName.trim() });
        }, 600);
      } else {
        setPhase('error');
        setErrorMsg(resp.error ?? 'Failed to create organization. Please try again.');
      }
    } catch {
      setPhase('error');
      setErrorMsg('Could not connect to the server. Please check your connection and try again.');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && phase === 'form') {
      e.preventDefault();
      handleSubmit();
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
          <div className="sh-onboarding-title">Set Up Your Organization</div>
          <div className="sh-onboarding-subtitle">
            Tell us about your business so we can tailor SHUNYA to your needs.
          </div>

          {phase === 'success' && (
            <div className="sh-onboarding-success">
              Organization created! Redirecting…
            </div>
          )}

          {(phase === 'form' || phase === 'loading' || phase === 'error') && (
            <>
              <form className="sh-onboarding-form" onSubmit={handleSubmit} role="main" aria-label="Organization setup">
                <div className="sh-onboarding-field">
                  <label htmlFor="org-name">Company Name</label>
                  <input
                    id="org-name"
                    type="text"
                    value={companyName}
                    onChange={e => setCompanyName(e.target.value)}
                    placeholder="e.g., Acme Corp"
                    autoFocus
                    disabled={phase === 'loading'}
                    autoComplete="organization"
                    ref={nameRef}
                    tabIndex={0}
                  />
                </div>

                <div className="sh-onboarding-field">
                  <label htmlFor="org-type">Business Type</label>
                  <select
                    id="org-type"
                    value={businessType}
                    onChange={e => setBusinessType(e.target.value)}
                    disabled={phase === 'loading'}
                    tabIndex={0}
                  >
                    {BUSINESS_TYPES.map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>

                {phase === 'error' && (
                  <div className="sh-onboarding-error" role="alert">
                    {errorMsg}
                  </div>
                )}

                <button
                  type="submit"
                  className="sh-onboarding-btn"
                  disabled={phase === 'loading' || !companyName.trim()}
                  tabIndex={0}
                >
                  {phase === 'loading' ? (
                    <><span className="sh-onboarding-spinner" />Creating…</>
                  ) : (
                    'Create Organization'
                  )}
                </button>
              </form>

              <button
                className="sh-onboarding-btn-secondary"
                onClick={onBack}
                disabled={phase === 'loading'}
                tabIndex={0}
              >
                Back
              </button>
            </>
          )}
        </div>
      </div>
      <style>{onboardingStyles}</style>
    </div>
  );
}

export { BUSINESS_TYPES };