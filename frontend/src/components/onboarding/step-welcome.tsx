/**
 * Step 1: Welcome — "Welcome to SHUNYA" screen.
 *
 * States: idle → loading (transition) → complete.
 * Shows the शून्य logo with a brief explanation and "Get Started" button.
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
    // Brief delay for a smooth transition
    setTimeout(() => {
      onNext();
    }, 400);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleGetStarted();
    }
    if (e.key === 'Escape') {
      // No back from welcome — nothing to do
    }
  };

  return (
    <div className="sh-onboarding">
      <div className="sh-onboarding-content" onKeyDown={handleKeyDown}>
        <div className="sh-onboarding-card sh-onb-fade-in">
          <div className="sh-onboarding-zero">शून्य</div>
          <div className="sh-onboarding-title">Welcome to SHUNYA</div>
          <div className="sh-onboarding-subtitle">
            Your business operating system. We'll help you get set up in just a few steps —
            create your organization, explore AI capabilities, and build your first business object.
          </div>

          <button
            className="sh-onboarding-btn"
            onClick={handleGetStarted}
            disabled={loading}
            autoFocus
            tabIndex={0}
            aria-label="Get started with onboarding"
          >
            {loading ? (
              <><span className="sh-onboarding-spinner" />Loading…</>
            ) : (
              'Get Started'
            )}
          </button>
        </div>
      </div>
      <style>{onboardingStyles}</style>
    </div>
  );
}