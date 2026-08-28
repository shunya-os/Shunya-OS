/**
 * OnboardingFlow — Redesigned onboarding.
 *
 * Steps: Welcome → Purpose → Complete
 * The "Create Object" step is removed. Purpose step offers meaningful choices
 * that connect the user's real work to their personal SHUNYA workspace.
 */
import { useState, useEffect, useCallback } from 'react';
import { StepWelcome } from './step-welcome';
import { StepPurpose } from './step-purpose';
import { StepComplete } from './step-complete';

interface Props {
  onComplete: () => void;
}

const TOTAL_STEPS = 3;
const STORAGE_STEP_KEY = 'shunya_onboarding_step';
const STORAGE_COMPLETE_KEY = 'shunya_onboarding_complete';
const STORAGE_ORG_KEY = 'shunya_onboarding_org';

const STEP_LABELS = ['Welcome', 'Purpose', 'Complete'];

function loadSavedStep(): number {
  try {
    const val = sessionStorage.getItem(STORAGE_STEP_KEY);
    if (val !== null) {
      const n = parseInt(val, 10);
      if (!isNaN(n) && n >= 0 && n < TOTAL_STEPS) return n;
    }
  } catch { /* noop */ }
  return 0;
}

function saveStep(step: number) {
  try { sessionStorage.setItem(STORAGE_STEP_KEY, String(step)); } catch { /* noop */ }
}

export function setOnboardingComplete() {
  try { sessionStorage.setItem(STORAGE_COMPLETE_KEY, 'true'); } catch { /* noop */ }
}

export function isOnboardingComplete(): boolean {
  try { return sessionStorage.getItem(STORAGE_COMPLETE_KEY) === 'true'; } catch { return false; }
}

export function clearOnboardingFlag() {
  try { sessionStorage.removeItem(STORAGE_COMPLETE_KEY); } catch { /* noop */ }
}

export function clearOnboardingProgress() {
  try {
    sessionStorage.removeItem(STORAGE_STEP_KEY);
    sessionStorage.removeItem(STORAGE_ORG_KEY);
    sessionStorage.removeItem(STORAGE_COMPLETE_KEY);
  } catch { /* noop */ }
}

export function OnboardingFlow({ onComplete }: Props) {
  const [step, setStep] = useState<number>(() => loadSavedStep());
  const [purposeResult, setPurposeResult] = useState<{ action: string; detail?: string } | null>(null);

  useEffect(() => { saveStep(step); }, [step]);

  const handleNext = useCallback(() => {
    if (step < TOTAL_STEPS - 1) setStep(prev => prev + 1);
  }, [step]);

  const handleBack = useCallback(() => {
    if (step > 0) setStep(prev => prev - 1);
  }, [step]);

  const handlePurposeComplete = useCallback((result: { action: string; detail?: string }) => {
    setPurposeResult(result);
    handleNext();
  }, [handleNext]);

  const handleComplete = useCallback(() => {
    setOnboardingComplete();
    try {
      sessionStorage.removeItem(STORAGE_STEP_KEY);
      sessionStorage.removeItem(STORAGE_ORG_KEY);
    } catch { /* noop */ }
    fetch('/api/v1/onboarding/complete', { method: 'POST', credentials: 'include' }).catch(() => {});
    onComplete();
  }, [onComplete]);

  const renderStep = () => {
    switch (step) {
      case 0:
        return <StepWelcome onNext={handleNext} />;
      case 1:
        return (
          <StepPurpose
            onNext={handlePurposeComplete}
            onBack={handleBack}
            onSkip={() => handlePurposeComplete({ action: 'empty' })}
          />
        );
      case 2:
        return (
          <StepComplete
            purposeResult={purposeResult}
            onComplete={handleComplete}
          />
        );
      default:
        return <StepWelcome onNext={handleNext} />;
    }
  };

  const renderStepIndicator = () => (
    <div className="sh-onboarding-steps" role="navigation" aria-label="Onboarding progress">
      {Array.from({ length: TOTAL_STEPS }, (_, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <div
            className={`sh-onboarding-step-dot ${i === step ? 'active' : ''} ${i < step ? 'completed' : ''}`}
            aria-label={`Step ${i + 1}: ${STEP_LABELS[i]}${i === step ? ' (current)' : ''}`}
          />
          <span className="sh-onboarding-step-label" style={{ color: i === step ? '#D4A84B' : i < step ? '#4ade80' : '#555' }}>
            {STEP_LABELS[i]}
          </span>
        </div>
      ))}
    </div>
  );

  return (
    <>
      {renderStepIndicator()}
      {renderStep()}
    </>
  );
}

export { STORAGE_COMPLETE_KEY };