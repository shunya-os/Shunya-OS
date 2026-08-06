/**
 * OnboardingFlow — Main onboarding orchestration component (Z-03A).
 *
 * Steps: Identity → Organization → Team → Import → Complete
 *
 * Features:
 * - Step indicator at top
 * - sessionStorage progress persistence (survives page refresh)
 * - Back navigation between steps
 * - Keyboard navigation (Tab, Enter, Escape)
 * - API error handling with retry options
 * - DB-backed completion flag (survives logout, browser restart, deployment)
 * - Auto-creates 26 foundational objects (Article XII)
 * - No educational detours (Z-04B Article VI)
 * - AI and Objects steps removed — no object-selection confusion
 */

import { useState, useEffect, useCallback } from 'react';
import { StepIdentity, type IdentityChoice } from './step-identity';
import { StepOrganization } from './step-organization';
import { StepTeam } from './step-team';
import { StepImport } from './step-import';
import { StepComplete } from './step-complete';
import { api } from '../../api/client';

interface Props {
  onComplete: () => void;
}

const TOTAL_STEPS = 5;
const STORAGE_STEP_KEY = 'shunya_onboarding_step';
const STORAGE_COMPLETE_KEY = 'shunya_onboarding_complete';
const STORAGE_IDENTITY_KEY = 'shunya_onboarding_identity';

const STEP_LABELS = ['Identity', 'Organization', 'Team', 'Import', 'Complete'];

// ── Helpers ──

function loadSavedStep(): number {
  try {
    const val = sessionStorage.getItem(STORAGE_STEP_KEY);
    if (val !== null) {
      const n = parseInt(val, 10);
      if (!isNaN(n) && n >= 0 && n < TOTAL_STEPS) return n;
    }
  } catch {
    /* noop */
  }
  return 0;
}

function saveStep(step: number) {
  try {
    sessionStorage.setItem(STORAGE_STEP_KEY, String(step));
  } catch {
    /* noop */
  }
}

function saveIdentityChoice(choice: IdentityChoice) {
  try {
    sessionStorage.setItem(STORAGE_IDENTITY_KEY, choice);
  } catch {
    /* noop */
  }
}

function loadIdentityChoice(): IdentityChoice | null {
  try {
    return sessionStorage.getItem(STORAGE_IDENTITY_KEY) as IdentityChoice | null;
  } catch {
    return null;
  }
}

// ── Component ──

export function OnboardingFlow({ onComplete }: Props) {
  const [step, setStep] = useState<number>(() => loadSavedStep());
  const [identityChoice, setIdentityChoice] = useState<IdentityChoice | null>(() => loadIdentityChoice());
  const [orgInfo, setOrgInfo] = useState<{ orgId: string; orgName: string } | null>(null);

  // Persist step changes
  useEffect(() => {
    saveStep(step);
  }, [step]);

  // Persist identity choice
  useEffect(() => {
    if (identityChoice) saveIdentityChoice(identityChoice);
  }, [identityChoice]);

  const handleNext = useCallback(() => {
    if (step < TOTAL_STEPS - 1) {
      setStep((prev) => prev + 1);
    }
  }, [step]);

  const handleBack = useCallback(() => {
    if (step > 0) {
      setStep((prev) => prev - 1);
    }
  }, [step]);

  const handleIdentityChosen = useCallback((choice: IdentityChoice) => {
    setIdentityChoice(choice);
    // If business, go to org step (step 1). If join or personal, skip to team (step 2)
    if (choice === 'business') {
      setStep(1); // Organization step
    } else {
      setStep(2); // Skip to Team step (no educational detours)
    }
  }, []);

  const handleOrgCreated = useCallback(
    (info: { orgId: string; orgName: string }) => {
      setOrgInfo(info);
      handleNext(); // Go to Team step
    },
    [handleNext],
  );

  const handleComplete = useCallback(() => {
    // Set DB-backed completion flag (survives anything)
    api.completeOnboarding().catch(() => {});
    // Also set legacy localStorage flag for backward compatibility
    try {
      localStorage.setItem(STORAGE_COMPLETE_KEY, 'true');
    } catch {
      /* noop */
    }
    // Clear progress data since it's now complete
    try {
      sessionStorage.removeItem(STORAGE_STEP_KEY);
      sessionStorage.removeItem(STORAGE_IDENTITY_KEY);
    } catch {
      /* noop */
    }
    onComplete();
  }, [onComplete]);

  // ── Render Step ──

  const renderStep = () => {
    switch (step) {
      case 0:
        return <StepIdentity onNext={handleIdentityChosen} />;
      case 1:
        return <StepOrganization onNext={handleOrgCreated} onBack={handleBack} />;
      case 2:
        return <StepTeam onNext={handleNext} onBack={handleBack} />;
      case 3:
        return <StepImport onNext={handleNext} onBack={handleBack} />;
      case 4:
        return <StepComplete orgInfo={identityChoice === 'business' ? orgInfo : null} onComplete={handleComplete} />;
      default:
        return <StepIdentity onNext={handleIdentityChosen} />;
    }
  };

  // ── Step Indicator ──

  const renderStepIndicator = () => (
    <div className="sh-onboarding-steps" role="navigation" aria-label="Onboarding progress">
      {Array.from({ length: TOTAL_STEPS }, (_, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <div
            className={`sh-onboarding-step-dot ${i === step ? 'active' : ''} ${i < step ? 'completed' : ''}`}
            aria-label={`Step ${i + 1}: ${STEP_LABELS[i]}${i === step ? ' (current)' : ''}`}
          />
          <span
            className="sh-onboarding-step-label"
            style={{ color: i === step ? '#D4A84B' : i < step ? '#4ade80' : '#555' }}
          >
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

// Re-export helpers for use in app.tsx
export { STORAGE_COMPLETE_KEY };

/**
 * Check if onboarding is complete using DB-backed status (Z-03A Article XIV).
 * Falls back to localStorage for backward compatibility.
 */
export async function checkOnboardingComplete(): Promise<boolean> {
  try {
    const resp = await api.checkOnboardingStatus();
    if (resp.success && resp.data?.completed) {
      return true;
    }
  } catch {
    /* fall through to localStorage check */
  }
  try {
    return localStorage.getItem(STORAGE_COMPLETE_KEY) === 'true';
  } catch {
    return false;
  }
}

export function isOnboardingComplete(): boolean {
  // Synchronous check uses localStorage only; async checkOnboardingComplete() is preferred
  try {
    return localStorage.getItem(STORAGE_COMPLETE_KEY) === 'true';
  } catch {
    return false;
  }
}

export function clearOnboardingFlag() {
  try {
    localStorage.removeItem(STORAGE_COMPLETE_KEY);
  } catch {
    /* noop */
  }
}

export function clearOnboardingProgress() {
  try {
    sessionStorage.removeItem(STORAGE_STEP_KEY);
    sessionStorage.removeItem(STORAGE_IDENTITY_KEY);
    localStorage.removeItem(STORAGE_COMPLETE_KEY);
  } catch {
    /* noop */
  }
}
