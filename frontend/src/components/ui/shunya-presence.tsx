/**
 * SHUNYA Presence — Gold dot indicator.
 *
 * Presence Canon §3: Four presence modes
 *   Ambient (gold dot only) — default
 *   Attentive (glow) — AI has relevant information
 *   Suggestive (1-3 suggestions) — AI has actionable suggestions
 *   Conversational (full panel) — User engaged
 *
 * Visual Design Bible §12: Identity elements
 *   Gold dot is the primary SHUNYA presence indicator.
 *   10px diameter, subtle gold glow.
 */

import { useState } from 'react';

type PresenceMode = 'ambient' | 'attentive' | 'suggestive' | 'conversational';

interface PresenceProps {
  mode?: PresenceMode;
  suggestionCount?: number;
  onActivate?: () => void;
}

export function ShunyaPresence({ mode = 'ambient', suggestionCount = 0, onActivate }: PresenceProps) {
  const [hover, setHover] = useState(false);

  const label = {
    ambient: 'SHUNYA is present',
    attentive: 'SHUNYA has information',
    suggestive: `${suggestionCount} suggestion${suggestionCount !== 1 ? 's' : ''} available`,
    conversational: 'SHUNYA conversation active',
  }[mode];

  return (
    <div className={`sh-presence sh-presence--${mode}`}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={onActivate}
      role="status"
      aria-label={label}
      title={label}>
      <div className="sh-presence-dot" aria-hidden="true" />
      {mode === 'suggestive' && suggestionCount > 0 && (
        <span className="sh-presence-count">{suggestionCount}</span>
      )}
      {hover && mode !== 'ambient' && (
        <span className="sh-presence-tooltip">{label}</span>
      )}
      <style>{`
.sh-presence {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  position: relative;
}

.sh-presence-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--shunya-gold, #A4865F);
  transition: box-shadow var(--shunya-duration-normal, 400ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}

/* Ambient — quiet, no glow */
.sh-presence--ambient .sh-presence-dot {
  box-shadow: none;
}

/* Attentive — subtle gold glow */
.sh-presence--attentive .sh-presence-dot {
  box-shadow: 0 0 8px var(--shunya-gold-glow, rgba(164,134,95,0.08));
  animation: sh-presence-breathe 4s ease-in-out infinite;
}

/* Suggestive — stronger glow */
.sh-presence--suggestive .sh-presence-dot {
  box-shadow: 0 0 12px rgba(164,134,95,0.18);
  animation: sh-presence-breathe 3s ease-in-out infinite;
}

/* Conversational — active glow */
.sh-presence--conversational .sh-presence-dot {
  box-shadow: 0 0 16px rgba(164,134,95,0.25);
}

.sh-presence-count {
  font-size: var(--shunya-text-xs, 10px);
  font-weight: 600;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  letter-spacing: var(--shunya-tracking-wider, 0.06em);
  line-height: 1;
}

.sh-presence-tooltip {
  position: absolute;
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  white-space: nowrap;
  font-size: var(--shunya-text-xs, 10px);
  font-weight: 500;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  letter-spacing: var(--shunya-tracking-wide, 0.02em);
  pointer-events: none;
}

@keyframes sh-presence-breathe {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@media (prefers-reduced-motion: reduce) {
  .sh-presence--attentive .sh-presence-dot,
  .sh-presence--suggestive .sh-presence-dot {
    animation: none;
  }
}
      `}</style>
    </div>
  );
}