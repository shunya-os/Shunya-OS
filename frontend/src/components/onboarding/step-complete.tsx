/**
 * Step 5: Complete — Onboarding complete screen.
 *
 * Shows "You're all set!" message with a summary of what was created.
 * "Enter SHUNYA" button transitions to the main workspace.
 */

import { useState, useEffect, useRef } from 'react';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  orgInfo: { orgId: string; orgName: string } | null;
  objectInfo: { objectId: string; objectType: string; objectName: string } | null;
  onComplete: () => void;
}

export function StepComplete({ orgInfo, objectInfo, onComplete }: Props) {
  const [loading, setLoading] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    btnRef.current?.focus();
  }, []);

  const handleEnter = () => {
    setLoading(true);
    onComplete();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleEnter();
    }
  };

  return (
    <div className="sh-onboarding" onKeyDown={handleKeyDown}>
      <div className="sh-onboarding-content">
        <div className="sh-onboarding-card sh-onb-fade-in">
          <div className="sh-onboarding-zero">शून्य</div>
          <div className="sh-onboarding-title">You're All Set!</div>
          <div className="sh-onboarding-subtitle">
            Your SHUNYA environment is ready. Here's what we created:
          </div>

          {/* Summary */}
          <div className="sh-onboarding-summary">
            {orgInfo && (
              <div className="sh-onboarding-summary-item">
                <div className="sh-onboarding-summary-icon gold">🏢</div>
                <div className="sh-onboarding-summary-text">
                  Organization: <strong>{orgInfo.orgName}</strong>
                </div>
              </div>
            )}
            {objectInfo && (
              <div className="sh-onboarding-summary-item">
                <div className="sh-onboarding-summary-icon green">📦</div>
                <div className="sh-onboarding-summary-text">
                  First object: <strong>{objectInfo.objectName}</strong>
                  <span style={{ color: '#888' }}> ({objectInfo.objectType})</span>
                </div>
              </div>
            )}
          </div>

          <div className="sh-onboarding-subtitle" style={{ fontSize: '0.8rem', color: '#666' }}>
            You can always create more objects, invite team members, and configure your workspace
            from the main dashboard.
          </div>

          <button
            className="sh-onboarding-btn"
            onClick={handleEnter}
            disabled={loading}
            ref={btnRef}
            autoFocus
            tabIndex={0}
            aria-label="Enter SHUNYA workspace"
          >
            {loading ? (
              <><span className="sh-onboarding-spinner" />Loading…</>
            ) : (
              'Enter SHUNYA'
            )}
          </button>
        </div>
      </div>
      <style>{onboardingStyles}</style>
    </div>
  );
}