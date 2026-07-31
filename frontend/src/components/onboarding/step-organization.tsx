/**
 * Step 2: Enhanced Organization Setup (Z-03A Articles VII-VIII).
 *
 * Collects meaningful company info during org creation.
 * Business category influences SHUNYA's suggested objects, dashboards, AI prompts.
 */

import { useState, useEffect, useRef } from 'react';
import { api } from '../../api/client';
import { SessionManager } from '../../api/session';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: (orgInfo: { orgId: string; orgName: string }) => void;
  onBack: () => void;
}

const BUSINESS_CATEGORIES = [
  'Travel Company', 'Restaurant', 'Manufacturer', 'Hospital', 'Law Firm',
  'Agency', 'Retail', 'Education', 'Construction', 'Real Estate',
  'Consultant', 'Hotel', 'Distributor', 'Service Business', 'Other',
];

const INDUSTRIES = [
  'Technology', 'Healthcare', 'Finance', 'Legal', 'Real Estate',
  'Hospitality', 'Manufacturing', 'Retail', 'Education', 'Construction',
  'Consulting', 'Transportation', 'Energy', 'Agriculture', 'Media',
  'Telecommunications', 'Other',
];

const COUNTRIES = [
  'United States', 'Canada', 'United Kingdom', 'India', 'Germany',
  'France', 'Australia', 'Brazil', 'Japan', 'Singapore',
  'United Arab Emirates', 'Netherlands', 'Spain', 'Italy', 'Mexico',
  'Other',
];

const TIMEZONES = [
  'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'America/Toronto', 'America/Sao_Paulo', 'America/Mexico_City',
  'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Madrid',
  'Asia/Kolkata', 'Asia/Dubai', 'Asia/Singapore', 'Asia/Tokyo',
  'Australia/Sydney', 'Pacific/Auckland', 'UTC',
];

const CURRENCIES = [
  'USD', 'EUR', 'GBP', 'INR', 'AED', 'CAD', 'AUD', 'SGD', 'JPY', 'BRL', 'MXN', 'Other',
];

type Phase = 'form' | 'loading' | 'error' | 'success';

export function StepOrganization({ onNext, onBack }: Props) {
  const [phase, setPhase] = useState<Phase>('form');
  const [companyName, setCompanyName] = useState('');
  const [companyEmail, setCompanyEmail] = useState('');
  const [website, setWebsite] = useState('');
  const [phone, setPhone] = useState('');
  const [industry, setIndustry] = useState('Technology');
  const [businessCategory, setBusinessCategory] = useState('Other');
  const [country, setCountry] = useState('United States');
  const [timezone, setTimezone] = useState('America/New_York');
  const [currency, setCurrency] = useState('USD');
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
      const resp = await api.createOrgExtended({
        company_name: companyName.trim(),
        business_type: businessCategory,
        business_category: businessCategory,
        company_email: companyEmail.trim(),
        website: website.trim(),
        phone: phone.trim(),
        industry: industry,
        country: country,
        timezone: timezone,
        currency: currency,
      });
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
                  <label htmlFor="org-name">Company Name *</label>
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
                  <label htmlFor="org-email">Company Email</label>
                  <input
                    id="org-email"
                    type="email"
                    value={companyEmail}
                    onChange={e => setCompanyEmail(e.target.value)}
                    placeholder="admin@mycompany.com"
                    disabled={phase === 'loading'}
                    autoComplete="email"
                    tabIndex={0}
                  />
                </div>

                <div className="sh-onboarding-row">
                  <div className="sh-onboarding-field" style={{ flex: 1 }}>
                    <label htmlFor="org-website">Website</label>
                    <input
                      id="org-website"
                      type="text"
                      value={website}
                      onChange={e => setWebsite(e.target.value)}
                      placeholder="https://mycompany.com"
                      disabled={phase === 'loading'}
                      tabIndex={0}
                    />
                  </div>
                  <div className="sh-onboarding-field" style={{ flex: 1 }}>
                    <label htmlFor="org-phone">Phone</label>
                    <input
                      id="org-phone"
                      type="tel"
                      value={phone}
                      onChange={e => setPhone(e.target.value)}
                      placeholder="+1 555-0123"
                      disabled={phase === 'loading'}
                      tabIndex={0}
                    />
                  </div>
                </div>

                <div className="sh-onboarding-field">
                  <label htmlFor="org-category">Business Category</label>
                  <select
                    id="org-category"
                    value={businessCategory}
                    onChange={e => setBusinessCategory(e.target.value)}
                    disabled={phase === 'loading'}
                    tabIndex={0}
                  >
                    {BUSINESS_CATEGORIES.map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                <div className="sh-onboarding-field">
                  <label htmlFor="org-industry">Industry</label>
                  <select
                    id="org-industry"
                    value={industry}
                    onChange={e => setIndustry(e.target.value)}
                    disabled={phase === 'loading'}
                    tabIndex={0}
                  >
                    {INDUSTRIES.map(i => (
                      <option key={i} value={i}>{i}</option>
                    ))}
                  </select>
                </div>

                <div className="sh-onboarding-row">
                  <div className="sh-onboarding-field" style={{ flex: 1 }}>
                    <label htmlFor="org-country">Country</label>
                    <select
                      id="org-country"
                      value={country}
                      onChange={e => setCountry(e.target.value)}
                      disabled={phase === 'loading'}
                      tabIndex={0}
                    >
                      {COUNTRIES.map(c => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div className="sh-onboarding-field" style={{ flex: 1 }}>
                    <label htmlFor="org-currency">Currency</label>
                    <select
                      id="org-currency"
                      value={currency}
                      onChange={e => setCurrency(e.target.value)}
                      disabled={phase === 'loading'}
                      tabIndex={0}
                    >
                      {CURRENCIES.map(c => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="sh-onboarding-field">
                  <label htmlFor="org-timezone">Time Zone</label>
                  <select
                    id="org-timezone"
                    value={timezone}
                    onChange={e => setTimezone(e.target.value)}
                    disabled={phase === 'loading'}
                    tabIndex={0}
                  >
                    {TIMEZONES.map(t => (
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
      <style>{`
        ${onboardingStyles}

        .sh-onboarding-row {
          display: flex; gap: 12px; width: 100%;
        }
        @media (max-width: 480px) {
          .sh-onboarding-row { flex-direction: column; gap: 16px; }
        }
      `}</style>
    </div>
  );
}