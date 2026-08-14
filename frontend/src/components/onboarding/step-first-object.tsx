/**
 * Step 4: First Object — Create the founder's first business object.
 *
 * States: form → loading → error → success.
 * Simple form with name and type (Document, Task, Note, Lead, Invoice).
 * After creation, shows success message with object details.
 */

import { useState, useRef, useEffect } from 'react';
import { api } from '../../api/client';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: (objectInfo: { objectId: string; objectType: string; objectName: string }) => void;
  onBack: () => void;
}

const OBJECT_TYPES = [
  { value: 'Document', label: 'Document', icon: '📄', desc: 'Store notes, plans, reports, or any text-based information you want to reference later.' },
  { value: 'Task', label: 'Task', icon: '✅', desc: 'Track something you or your team needs to complete — a to-do, checklist item, or action item.' },
  { value: 'Note', label: 'Note', icon: '📝', desc: 'Quick notes, ideas, or observations you want to keep — like a sticky note that stays organized.' },
  { value: 'Lead', label: 'Lead', icon: '🔍', desc: 'A potential customer or sales opportunity — someone interested in your product or service.' },
  { value: 'Invoice', label: 'Invoice', icon: '💰', desc: 'A bill you send to a customer for products or services provided — tracked as a receivable.' },
];

type Phase = 'form' | 'loading' | 'error' | 'success';

export function StepFirstObject({ onNext, onBack }: Props) {
  const [phase, setPhase] = useState<Phase>('form');
  const [objectName, setObjectName] = useState('');
  const [objectType, setObjectType] = useState('Document');
  const [errorMsg, setErrorMsg] = useState('');
  const [createdInfo, setCreatedInfo] = useState<{ id: string; type: string; name: string } | null>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    nameRef.current?.focus();
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!objectName.trim()) {
      setPhase('error');
      setErrorMsg('Please enter a name for your object.');
      return;
    }
    setPhase('loading');
    setErrorMsg('');

    try {
      const resp = await api.createObject(objectName.trim(), objectType);
      if (resp.success && resp.object_id) {
        const info = { id: resp.object_id, type: objectType, name: objectName.trim() };
        setCreatedInfo(info);
        setPhase('success');
      } else {
        setPhase('error');
        setErrorMsg(resp.error ?? 'Failed to create object. Please try again.');
      }
    } catch {
      setPhase('error');
      setErrorMsg('Could not connect to the server. Please check your connection and try again.');
    }
  };

  const handleContinue = () => {
    if (createdInfo) {
      onNext({ objectId: createdInfo.id, objectType: createdInfo.type, objectName: createdInfo.name });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && phase === 'form') {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      if (phase === 'success') return; // Don't go back from success
      onBack();
    }
  };

  const handleRetry = () => {
    setPhase('form');
    setErrorMsg('');
  };

  const selectedTypeMeta = OBJECT_TYPES.find(t => t.value === objectType);

  return (
    <div className="sh-onboarding" onKeyDown={handleKeyDown}>
      <div className="sh-onboarding-content">
        <div className="sh-onboarding-card sh-onb-fade-in">
          <div className="sh-onboarding-title">Your First Business Object</div>
          <div className="sh-onboarding-subtitle">
            Business objects are the building blocks of SHUNYA. Create your first one to get started.
          </div>

          {phase === 'success' && createdInfo && (
            <>
              <div className="sh-onboarding-success">
                <div style={{ fontSize: '1.2rem', marginBottom: 4 }}>
                  {selectedTypeMeta?.icon} {createdInfo.name}
                </div>
                <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
                  {createdInfo.type} created successfully
                </div>
              </div>
              <button
                className="sh-onboarding-btn"
                onClick={handleContinue}
                autoFocus
                tabIndex={0}
              >
                Continue
              </button>
            </>
          )}

          {(phase === 'form' || phase === 'loading' || phase === 'error') && (
            <>
              <form className="sh-onboarding-form" onSubmit={handleSubmit} role="main" aria-label="Create business object">
                <div className="sh-onboarding-field">
                  <label htmlFor="obj-name">Object Name</label>
                  <input
                    id="obj-name"
                    type="text"
                    value={objectName}
                    onChange={e => setObjectName(e.target.value)}
                    placeholder="e.g., Q4 Strategy Doc"
                    autoFocus
                    disabled={phase === 'loading'}
                    ref={nameRef}
                    tabIndex={0}
                  />
                </div>

                <div className="sh-onboarding-field">
                  <label htmlFor="obj-type">Object Type</label>
                  <select
                    id="obj-type"
                    value={objectType}
                    onChange={e => setObjectType(e.target.value)}
                    disabled={phase === 'loading'}
                    tabIndex={0}
                  >
                    {OBJECT_TYPES.map(t => (
                      <option key={t.value} value={t.value}>{t.icon} {t.label}</option>
                    ))}
                  </select>
                  {selectedTypeMeta && (
                    <div className="sh-onboarding-desc" style={{fontSize:'0.8rem',color:'#888',marginTop:4}}>
                      {selectedTypeMeta.desc}
                    </div>
                  )}
                </div>

                {phase === 'error' && (
                  <div className="sh-onboarding-error" role="alert">
                    {errorMsg}
                    <div style={{ marginTop: 8 }}>
                      <button
                        className="sh-onboarding-btn-secondary"
                        onClick={handleRetry}
                        style={{ padding: '6px 12px', fontSize: '0.8rem', width: 'auto' }}
                        tabIndex={0}
                      >
                        Retry
                      </button>
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  className="sh-onboarding-btn"
                  disabled={phase === 'loading' || !objectName.trim()}
                  tabIndex={0}
                >
                  {phase === 'loading' ? (
                    <><span className="sh-onboarding-spinner" />Creating…</>
                  ) : (
                    'Create Object'
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

export { OBJECT_TYPES };