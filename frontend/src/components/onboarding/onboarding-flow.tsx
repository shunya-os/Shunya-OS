/**
 * OnboardingFlow — Main onboarding orchestration component.
 *
 * Steps: Welcome → Organization Setup → AI Introduction → First Object → Complete
 *
 * Features:
 * - Step indicator at top (Step 1 of 5 style)
 * - sessionStorage progress persistence (survives page refresh)
 * - Back navigation between steps
 * - Keyboard navigation (Tab, Enter, Escape)
 * - API error handling with retry options
 * - Sets completion flag after finishing
 */

import { useState, useEffect, useCallback } from 'react';
import { StepWelcome } from './step-welcome';
import { StepOrganization } from './step-organization';
import { StepAiIntro } from './step-ai-intro';
import { StepFirstObject } from './step-first-object';
import { StepComplete } from './step-complete';

interface Props {
  onComplete: () => void;
}

const TOTAL_STEPS = 5;
const STORAGE_STEP_KEY = 'shunya_onboarding_step';
const STORAGE_COMPLETE_KEY = 'shunya_onboarding_complete';
const STORAGE_ORG_KEY = 'shunya_onboarding_org';
const STORAGE_OBJECT_KEY = 'shunya_onboarding_object';

const STEP_LABELS = ['Welcome', 'Organization', 'AI', 'First Object', 'Complete'];

// ── Helpers ──

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

function saveOrgInfo(info: { orgId: string; orgName: string }) {
  try { sessionStorage.setItem(STORAGE_ORG_KEY, JSON.stringify(info)); } catch { /* noop */ }
}

function loadOrgInfo(): { orgId: string; orgName: string } | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_ORG_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function saveObjectInfo(info: { objectId: string; objectType: string; objectName: string }) {
  try { sessionStorage.setItem(STORAGE_OBJECT_KEY, JSON.stringify(info)); } catch { /* noop */ }
}

function loadObjectInfo(): { objectId: string; objectType: string; objectName: string } | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_OBJECT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
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
    sessionStorage.removeItem(STORAGE_OBJECT_KEY);
    sessionStorage.removeItem(STORAGE_COMPLETE_KEY);
  } catch { /* noop */ }
}

// ── Component ──

export function OnboardingFlow({ onComplete }: Props) {
  const [step, setStep] = useState<number>(() => loadSavedStep());
  const [orgInfo, setOrgInfo] = useState<{ orgId: string; orgName: string } | null>(() => loadOrgInfo());
  const [objectInfo, setObjectInfo] = useState<{ objectId: string; objectType: string; objectName: string } | null>(() => loadObjectInfo());

  // Persist step changes
  useEffect(() => {
    saveStep(step);
  }, [step]);

  // Persist org info changes
  useEffect(() => {
    if (orgInfo) saveOrgInfo(orgInfo);
  }, [orgInfo]);

  // Persist object info changes
  useEffect(() => {
    if (objectInfo) saveObjectInfo(objectInfo);
  }, [objectInfo]);

  const handleNext = useCallback(() => {
    if (step < TOTAL_STEPS - 1) {
      setStep(prev => prev + 1);
    }
  }, [step]);

  const handleBack = useCallback(() => {
    if (step > 0) {
      setStep(prev => prev - 1);
    }
  }, [step]);

  const handleOrgCreated = useCallback((info: { orgId: string; orgName: string }) => {
    setOrgInfo(info);
    handleNext();
  }, [handleNext]);

  const handleObjectCreated = useCallback((info: { objectId: string; objectType: string; objectName: string }) => {
    setObjectInfo(info);
    handleNext();
  }, [handleNext]);

  const handleComplete = useCallback(() => {
    setOnboardingComplete();
    // Clear progress data since it's now complete
    try {
      sessionStorage.removeItem(STORAGE_STEP_KEY);
      sessionStorage.removeItem(STORAGE_ORG_KEY);
      sessionStorage.removeItem(STORAGE_OBJECT_KEY);
    } catch { /* noop */ }
    onComplete();
  }, [onComplete]);

  // ── Render Step ──

  const renderStep = () => {
    switch (step) {
      case 0:
        return <StepWelcome onNext={handleNext} />;
      case 1:
        return (
          <StepOrganization
            onNext={handleOrgCreated}
            onBack={handleBack}
          />
        );
      case 2:
        return (
          <StepAiIntro
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 3:
        return (
          <StepFirstObject
            onNext={handleObjectCreated}
            onBack={handleBack}
          />
        );
      case 4:
        return (
          <StepComplete
            orgInfo={orgInfo}
            objectInfo={objectInfo}
            onComplete={handleComplete}
          />
        );
      default:
        return <StepWelcome onNext={handleNext} />;
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

// Re-export helpers for use in app.tsx
export { STORAGE_COMPLETE_KEY };