/**
 * StepComplete — Onboarding complete screen.
 *
 * Shows "Your personal SHUNYA workspace is ready" with a summary
 * of what the user chose to share. Reframed per M2C directive.
 */
import { useState, useEffect, useRef } from 'react';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  purposeResult: { action: string; detail?: string } | null;
  onComplete: () => void;
}

const ACTION_LABELS: Record<string, { icon: string; text: string }> = {
  upload: { icon: '📤', text: 'Uploaded a file for analysis' },
  describe: { icon: '✍️', text: 'Told SHUNYA about your work' },
  working_on: { icon: '🔨', text: 'Added something you\'re working on' },
  create_org: { icon: '🏢', text: 'Created an organization' },
  connect_org: { icon: '🔗', text: 'Connected to an organization' },
  empty: { icon: '🌱', text: 'Started with an empty workspace' },
};

export function StepComplete({ purposeResult, onComplete }: Props) {
  const [loading, setLoading] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    btnRef.current?.focus();
  }, []);

  const handleEnter = () => {
    setLoading(true);
    onComplete();
  };

  const actionLabel = purposeResult ? ACTION_LABELS[purposeResult.action] : null;
  const actionText = purposeResult?.detail
    ? `${actionLabel?.text || ''}: "${purposeResult.detail}"`
    : actionLabel?.text || 'Personal workspace ready';

  return (
    <div className="sh-onboarding">
      <div className="sh-onboarding-content">
        <div className="sh-onboarding-card sh-onb-fade-in">
          <div className="sh-onboarding-zero">शून्य</div>
          <div className="sh-onboarding-title">Your Personal SHUNYA Is Ready</div>
          <div className="sh-onboarding-subtitle">
            Your personal workspace is set up and waiting for you.
          </div>

          <div className="sh-onboarding-summary">
            <div className="sh-onboarding-summary-item">
              <div className="sh-onboarding-summary-icon gold">👤</div>
              <div className="sh-onboarding-summary-text">
                Personal workspace: <strong>Nishesh's SHUNYA</strong>
              </div>
            </div>
            {purposeResult && purposeResult.action !== 'empty' && actionLabel && (
              <div className="sh-onboarding-summary-item">
                <div className="sh-onboarding-summary-icon green">{actionLabel.icon}</div>
                <div className="sh-onboarding-summary-text">
                  {actionText}
                </div>
              </div>
            )}
          </div>

          <div className="sh-onboarding-subtitle" style={{ fontSize: '0.8rem', color: '#666' }}>
            From here, you can work in your personal space, create or join an organization,
            upload files, and explore everything SHUNYA can do.
          </div>

          <button
            className="sh-onboarding-btn"
            onClick={handleEnter}
            disabled={loading}
            ref={btnRef}
            autoFocus
            tabIndex={0}
            aria-label="Enter my SHUNYA workspace"
          >
            {loading ? (
              <><span className="sh-onboarding-spinner" />Loading…</>
            ) : (
              'Enter My SHUNYA'
            )}
          </button>
        </div>
      </div>
      <style>{onboardingStyles}</style>
    </div>
  );
}