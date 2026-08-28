/**
 * Step 1: Welcome — "Welcome to Your Personal SHUNYA Workspace"
 *
 * Reframed per M2C directive: explicitly communicates that the user
 * is setting up their PERSONAL workspace, not a company.
 */
import { useState } from 'react';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: () => void;
}

export function StepWelcome({ onNext }: Props) {
  const [loading, setLoading] = useState(false);

  const handleGetStarted = () => {
    setLoading(true);
    setTimeout(() => { onNext(); }, 400);
  };

  return (
    <div className="sh-onboarding">
      <div className="sh-onboarding-content">
        <div className="sh-onboarding-card sh-onb-fade-in">
          <div className="sh-onboarding-zero">शून्य</div>
          <div className="sh-onboarding-title">Welcome to Your Personal SHUNYA</div>
          <div className="sh-onboarding-subtitle">
            You're setting up <strong>your personal workspace</strong> — a private space where
            SHUNYA can help you understand and organize what matters to you.
          </div>
          <div className="sh-onboarding-features">
            <div className="sh-onboarding-feature">
              <span className="sh-onboarding-feature-icon">📋</span>
              <span>Your work and projects</span>
            </div>
            <div className="sh-onboarding-feature">
              <span className="sh-onboarding-feature-icon">📄</span>
              <span>Documents and files</span>
            </div>
            <div className="sh-onboarding-feature">
              <span className="sh-onboarding-feature-icon">✅</span>
              <span>Tasks and commitments</span>
            </div>
            <div className="sh-onboarding-feature">
              <span className="sh-onboarding-feature-icon">💡</span>
              <span>Ideas and knowledge</span>
            </div>
          </div>
          <div className="sh-onboarding-note">
            Later, you can create or join an organization — but first, let's set up <strong>your</strong> SHUNYA.
          </div>
          <button
            className="sh-onboarding-btn"
            onClick={handleGetStarted}
            disabled={loading}
            autoFocus
            tabIndex={0}
            aria-label="Set up my personal workspace"
          >
            {loading ? (
              <><span className="sh-onboarding-spinner" />Loading…</>
            ) : (
              'Set Up My Workspace'
            )}
          </button>
        </div>
      </div>
      <style>{onboardingStyles}</style>
    </div>
  );
}