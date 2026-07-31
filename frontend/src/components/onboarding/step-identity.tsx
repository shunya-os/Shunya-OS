/**
 * Step 1: Identity — "How would you like to use SHUNYA?"
 *
 * Z-03A Article VI: Identity Before Organization.
 * Options:
 *   1. My Business (founder owns/manages a company) → org creation
 *   2. Join an existing company (invitation flow)
 *   3. Personal Workspace (individual, no org)
 *
 * For options 2 and 3, org creation is skipped.
 */

import { useState, useRef, useEffect } from 'react';
import { onboardingStyles } from './onboarding-styles';

export type IdentityChoice = 'business' | 'join' | 'personal';

interface Props {
  onNext: (choice: IdentityChoice) => void;
}

const OPTIONS: { value: IdentityChoice; icon: string; title: string; desc: string }[] = [
  {
    value: 'business',
    icon: '🏢',
    title: 'My Business',
    desc: 'I own or manage a company and want to run it with SHUNYA.',
  },
  {
    value: 'join',
    icon: '🤝',
    title: 'Join an Existing Company',
    desc: 'I was invited to join a team. I\'ll use an invitation to get in.',
  },
  {
    value: 'personal',
    icon: '🧑‍💻',
    title: 'Personal Workspace',
    desc: 'I\'m using SHUNYA for myself — no company organization needed.',
  },
];

export function StepIdentity({ onNext }: Props) {
  const [selected, setSelected] = useState<IdentityChoice | null>(null);
  const btnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    btnRef.current?.focus();
  }, [selected]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && selected) {
      e.preventDefault();
      onNext(selected);
    }
  };

  return (
    <div className="sh-onboarding" onKeyDown={handleKeyDown}>
      <div className="sh-onboarding-content">
        <div className="sh-onboarding-card sh-onb-fade-in">
          <div className="sh-onboarding-title">How would you like to use SHUNYA?</div>
          <div className="sh-onboarding-subtitle">
            Choose the path that fits you best. You can always change this later.
          </div>

          <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {OPTIONS.map(opt => (
              <button
                key={opt.value}
                className={`sh-identity-option ${selected === opt.value ? 'selected' : ''}`}
                onClick={() => setSelected(opt.value)}
                tabIndex={0}
                role="radio"
                aria-checked={selected === opt.value}
              >
                <span className="sh-identity-icon">{opt.icon}</span>
                <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 2 }}>
                  <span className="sh-identity-title">{opt.title}</span>
                  <span className="sh-identity-desc">{opt.desc}</span>
                </span>
              </button>
            ))}
          </div>

          <button
            className="sh-onboarding-btn"
            onClick={() => selected && onNext(selected)}
            disabled={!selected}
            ref={btnRef}
            tabIndex={0}
          >
            Continue
          </button>
        </div>
      </div>

      <style>{`
        ${onboardingStyles}

        .sh-identity-option {
          display: flex; align-items: center; gap: 14px;
          width: 100%; padding: 14px 16px;
          background: #1a1a24; border: 1px solid #2a2a3a; border-radius: 10px;
          color: #e0e0e0; font-family: inherit; cursor: pointer;
          transition: all 0.2s; text-align: left;
        }
        .sh-identity-option:hover { border-color: #444; background: #1f1f2b; }
        .sh-identity-option.selected {
          border-color: #D4A84B;
          background: rgba(212, 168, 75, 0.1);
          box-shadow: 0 0 0 1px #D4A84B inset;
        }
        .sh-identity-option:focus-visible {
          outline: 2px solid #D4A84B; outline-offset: 2px;
        }
        .sh-identity-icon { font-size: 1.4rem; flex-shrink: 0; }
        .sh-identity-title { font-size: 0.95rem; font-weight: 500; color: #fff; }
        .sh-identity-desc { font-size: 0.8rem; color: #888; line-height: 1.4; }
      `}</style>
    </div>
  );
}