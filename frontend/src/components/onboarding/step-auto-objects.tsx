/**
 * Step: Auto-Created Foundational Objects (Z-03A Article XII).
 *
 * SHUNYA already knows its business model. All foundational objects
 * exist automatically — the founder never asks "what object should I create?"
 *
 * States: loading → success (shows objects) | error (with retry)
 * After auto-creation, shows a summary of what was created.
 */

import { useState, useEffect, useRef } from 'react';
import { api } from '../../api/client';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: (objectInfo: { objectId: string; objectType: string; objectName: string } | null) => void;
  onBack: () => void;
  businessCategory?: string;
}

type Phase = 'creating' | 'success' | 'error';

export function StepAutoObjects({ onNext, onBack, businessCategory }: Props) {
  const [phase, setPhase] = useState<Phase>('creating');
  const [objects, setObjects] = useState<{ object_id: string; name: string; object_type: string }[]>([]);
  const [count, setCount] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
  const btnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    btnRef.current?.focus();
  }, [phase]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await api.autoCreateFoundationalObjects(businessCategory);
        if (cancelled) return;
        if (resp.success && resp.data) {
          setObjects(resp.data.objects || []);
          setCount(resp.data.count);
          setPhase('success');
        } else {
          setPhase('error');
          setErrorMsg('Failed to prepare your workspace. Please try again.');
        }
      } catch {
        if (!cancelled) {
          setPhase('error');
          setErrorMsg('Could not connect to the server. Your objects will be created once connected.');
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [businessCategory]);

  const handleContinue = () => {
    if (objects.length > 0) {
      onNext({ objectId: objects[0].object_id, objectType: objects[0].object_type, objectName: objects[0].name });
    } else {
      onNext(null);
    }
  };

  const handleRetry = () => {
    setPhase('creating');
    setErrorMsg('');
    setObjects([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && phase === 'success') {
      e.preventDefault();
      handleContinue();
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
          {/* ── Creating ── */}
          {phase === 'creating' && (
            <>
              <div className="sh-onboarding-zero">शून्य</div>
              <div className="sh-onboarding-title">Setting Up Your Business Objects</div>
              <div className="sh-onboarding-info" style={{ width: '100%', textAlign: 'center' }}>
                <span className="sh-onboarding-spinner" />
                <span style={{ marginLeft: 8 }}>SHUNYA is creating your foundational objects…</span>
              </div>
            </>
          )}

          {/* ── Success ── */}
          {phase === 'success' && (
            <>
              <div className="sh-onboarding-zero" style={{ color: '#4ade80' }}>
                ✓
              </div>
              <div className="sh-onboarding-title">Your Workspace Is Ready</div>
              <div className="sh-onboarding-subtitle">
                SHUNYA has created <strong>{count}</strong> foundational objects for your business. Everything you need
                is already here — no setup required.
              </div>

              {/* Object grid */}
              <div className="sh-auto-objects-grid">
                {objects.slice(0, 12).map((obj) => (
                  <div key={obj.object_id} className="sh-auto-object-card">
                    <span className="sh-auto-object-icon">{getIconForType(obj.object_type)}</span>
                    <span className="sh-auto-object-name">{obj.name}</span>
                    <span className="sh-auto-object-type">{obj.object_type}</span>
                  </div>
                ))}
                {objects.length > 12 && <div className="sh-auto-object-more">+{objects.length - 12} more</div>}
              </div>

              <button className="sh-onboarding-btn" onClick={handleContinue} ref={btnRef} autoFocus tabIndex={0}>
                Continue to Workspace ›
              </button>
            </>
          )}

          {/* ── Error ── */}
          {phase === 'error' && (
            <>
              <div className="sh-onboarding-title">Something Went Wrong</div>
              <div className="sh-onboarding-error" role="alert" style={{ width: '100%' }}>
                {errorMsg}
              </div>
              <div style={{ display: 'flex', gap: 10, width: '100%' }}>
                <button className="sh-onboarding-btn" onClick={handleRetry} tabIndex={0} style={{ flex: 1 }}>
                  Retry
                </button>
                <button
                  className="sh-onboarding-btn-secondary"
                  onClick={() => onNext(null)}
                  tabIndex={0}
                  style={{ flex: 1 }}
                >
                  Skip
                </button>
              </div>
            </>
          )}

          {phase === 'success' && (
            <button className="sh-onboarding-btn-secondary" onClick={onBack} tabIndex={0}>
              Back
            </button>
          )}
        </div>
      </div>

      <style>{`
        ${onboardingStyles}

        .sh-auto-objects-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
          gap: 8px;
          width: 100%;
          max-height: 280px;
          overflow-y: auto;
          padding: 4px;
        }

        .sh-auto-object-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 10px 8px;
          background: #1a1a24;
          border: 1px solid #2a2a3a;
          border-radius: 8px;
          text-align: center;
          transition: border-color 0.2s;
        }
        .sh-auto-object-card:hover {
          border-color: #D4A84B;
        }

        .sh-auto-object-icon {
          font-size: 1.3rem;
        }

        .sh-auto-object-name {
          font-size: 0.78rem;
          font-weight: 500;
          color: #fff;
        }

        .sh-auto-object-type {
          font-size: 0.65rem;
          color: #666;
        }

        .sh-auto-object-more {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 10px;
          font-size: 0.8rem;
          color: #D4A84B;
          background: #1a1a24;
          border: 1px dashed #2a2a3a;
          border-radius: 8px;
        }

        @media (max-width: 480px) {
          .sh-auto-objects-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 6px;
          }
        }
      `}</style>
    </div>
  );
}

function getIconForType(type: string): string {
  const icons: Record<string, string> = {
    Customer: '👤',
    Supplier: '🚚',
    Company: '🏢',
    Employee: '🧑‍💼',
    Lead: '🔍',
    Opportunity: '💎',
    Proposal: '📋',
    Quote: '💰',
    Invoice: '📄',
    Payment: '💳',
    Task: '✅',
    Meeting: '📅',
    Conversation: '💬',
    Email: '📧',
    WhatsApp: '📱',
    Document: '📄',
    Note: '📝',
    Reminder: '⏰',
    Commitment: '🤝',
    Product: '📦',
    Service: '🛠️',
    Project: '📊',
    Knowledge: '📚',
    'Calendar Event': '📅',
    Relationship: '🔗',
    Memory: '🧠',
  };
  return icons[type] || '📦';
}
