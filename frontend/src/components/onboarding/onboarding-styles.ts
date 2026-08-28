/**
 * Shared Onboarding Styles — Consistent dark-theme CSS for all onboarding steps.
 *
 * Reuses the .sh-auth-* design tokens so onboarding feels continuous with auth.
 */

export const onboardingStyles = `
/* ── Onboarding Root ──────────────────────────────────────── */
.sh-onboarding {
  position: fixed; inset: 0;
  display: flex; flex-direction: column;
  background: #0a0a0f;
  color: #e0e0e0;
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
  overflow-y: auto;
}

/* ── Step Indicator Bar ───────────────────────────────────── */
.sh-onboarding-steps {
  display: flex; align-items: center; justify-content: center;
  gap: 10px; padding: 24px 16px 12px;
  flex-shrink: 0;
}
.sh-onboarding-step-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #2a2a3a; transition: all 0.3s ease;
}
.sh-onboarding-step-dot.active {
  background: #D4A84B; width: 24px; border-radius: 4px;
}
.sh-onboarding-step-dot.completed {
  background: #4ade80; opacity: 0.6;
}
.sh-onboarding-step-label {
  font-size: 0.7rem; color: #555; text-align: center;
  letter-spacing: 0.05em; margin-top: 4px;
}

/* ── Step Content ─────────────────────────────────────────── */
.sh-onboarding-content {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 24px 20px 32px;
  max-width: 500px; width: 100%; margin: 0 auto;
  gap: 24px; animation: sh-onb-fade-in 0.4s ease-out both;
}
.sh-onboarding-card {
  width: 100%; display: flex; flex-direction: column; align-items: center;
  gap: 20px;
}

/* ── Header ───────────────────────────────────────────────── */
.sh-onboarding-zero {
  font-size: clamp(2rem, 8vw, 3rem); color: #fff; font-weight: 300;
  font-family: 'Noto Sans Devanagari', 'Segoe UI', sans-serif;
}
.sh-onboarding-title {
  font-size: clamp(1.3rem, 4vw, 1.6rem); font-weight: 500; color: #fff;
  text-align: center; letter-spacing: -0.01em;
}
.sh-onboarding-subtitle {
  font-size: 0.9rem; color: #888; text-align: center; line-height: 1.6;
  max-width: 380px;
}

/* ── Form ─────────────────────────────────────────────────── */
.sh-onboarding-form {
  width: 100%; display: flex; flex-direction: column; gap: 16px;
}
.sh-onboarding-field label {
  display: block; font-size: 0.75rem; color: #888; margin-bottom: 4px; letter-spacing: 0.05em;
}
.sh-onboarding-field input,
.sh-onboarding-field select {
  width: 100%; padding: 10px 14px;
  background: #1a1a24; border: 1px solid #2a2a3a; border-radius: 6px;
  color: #e0e0e0; font-size: 0.95rem; outline: none; transition: border-color 0.2s;
  font-family: inherit;
}
.sh-onboarding-field input:focus,
.sh-onboarding-field select:focus { border-color: #D4A84B; }
.sh-onboarding-field input:disabled,
.sh-onboarding-field select:disabled { opacity: 0.5; cursor: not-allowed; }
.sh-onboarding-field input::placeholder { color: #555; }
.sh-onboarding-field select option { background: #1a1a24; color: #e0e0e0; }

/* ── Textarea for AI demo ─────────────────────────────────── */
.sh-onboarding-textarea {
  width: 100%; padding: 10px 14px; min-height: 80px; resize: vertical;
  background: #1a1a24; border: 1px solid #2a2a3a; border-radius: 6px;
  color: #e0e0e0; font-size: 0.95rem; outline: none; transition: border-color 0.2s;
  font-family: inherit; line-height: 1.5;
}
.sh-onboarding-textarea:focus { border-color: #D4A84B; }
.sh-onboarding-textarea:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Buttons ──────────────────────────────────────────────── */
.sh-onboarding-btn {
  width: 100%; padding: 10px 14px;
  background: #D4A84B; color: #0a0a0f;
  border: none; border-radius: 6px; font-size: 0.95rem; font-weight: 500;
  cursor: pointer; transition: opacity 0.2s; font-family: inherit;
}
.sh-onboarding-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-onboarding-btn:hover:not(:disabled) { opacity: 0.85; }
.sh-onboarding-btn:focus-visible {
  outline: 2px solid #D4A84B; outline-offset: 2px;
}

.sh-onboarding-btn-secondary {
  padding: 10px 14px;
  background: transparent; color: #D4A84B;
  border: 1px solid #2a2a3a; border-radius: 6px; font-size: 0.9rem; font-weight: 400;
  cursor: pointer; transition: all 0.2s; font-family: inherit;
}
.sh-onboarding-btn-secondary:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-onboarding-btn-secondary:hover:not(:disabled) { border-color: #D4A84B; }
.sh-onboarding-btn-secondary:focus-visible {
  outline: 2px solid #D4A84B; outline-offset: 2px;
}

.sh-onboarding-btn-row {
  display: flex; gap: 10px; width: 100%;
}
.sh-onboarding-btn-row .sh-onboarding-btn,
.sh-onboarding-btn-row .sh-onboarding-btn-secondary {
  flex: 1;
}

/* ── Status messages ──────────────────────────────────────── */
.sh-onboarding-error {
  font-size: 0.8rem; color: #f55; text-align: center;
  background: rgba(255, 85, 85, 0.08); border: 1px solid rgba(255, 85, 85, 0.2);
  border-radius: 6px; padding: 8px 12px; width: 100%;
}
.sh-onboarding-success {
  font-size: 0.85rem; color: #4ade80; text-align: center;
  background: rgba(74, 222, 128, 0.08); border: 1px solid rgba(74, 222, 128, 0.2);
  border-radius: 6px; padding: 10px 14px; width: 100%;
  line-height: 1.5;
}
.sh-onboarding-info {
  font-size: 0.8rem; color: #888; text-align: center;
  padding: 8px 12px;
}

/* ── Spinner ──────────────────────────────────────────────── */
.sh-onboarding-spinner {
  display: inline-block; width: 16px; height: 16px;
  border: 2px solid rgba(212, 168, 75, 0.3);
  border-top-color: #D4A84B;
  border-radius: 50%; animation: sh-onb-spin 0.6s linear infinite;
  vertical-align: middle; margin-right: 6px;
}
@keyframes sh-onb-spin { to { transform: rotate(360deg); } }

/* ── AI message bubbles ───────────────────────────────────── */
.sh-onboarding-ai-message {
  width: 100%; padding: 12px 16px;
  background: #1a1a24; border: 1px solid #2a2a3a;
  border-radius: 10px; line-height: 1.6; font-size: 0.9rem;
  white-space: pre-wrap;
}
.sh-onboarding-ai-message .sh-onboarding-ai-label {
  font-size: 0.7rem; color: #D4A84B; letter-spacing: 0.05em;
  text-transform: uppercase; margin-bottom: 6px; font-weight: 500;
}

/* ── Summary section ──────────────────────────────────────── */
.sh-onboarding-summary {
  width: 100%;
}
.sh-onboarding-summary-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  background: #1a1a24; border: 1px solid #2a2a3a;
  border-radius: 6px; margin-bottom: 8px;
}
.sh-onboarding-summary-icon {
  width: 28px; height: 28px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem; flex-shrink: 0;
}
.sh-onboarding-summary-icon.gold { background: rgba(212, 168, 75, 0.15); color: #D4A84B; }
.sh-onboarding-summary-icon.green { background: rgba(74, 222, 128, 0.15); color: #4ade80; }
.sh-onboarding-summary-text { font-size: 0.85rem; color: #ccc; }
.sh-onboarding-summary-text strong { color: #fff; }

/* ── Purpose Choices ──────────────────────────────────────── */
.sh-purpose-choices {
  width: 100%; display: flex; flex-direction: column; gap: 8px;
}
.sh-purpose-choice {
  display: flex; align-items: center; gap: 12px;
  width: 100%; padding: 12px 16px;
  background: #1a1a24; border: 1px solid #2a2a3a; border-radius: 8px;
  color: #e0e0e0; font-size: 0.9rem; cursor: pointer;
  transition: border-color 0.2s, background 0.2s; font-family: inherit;
  text-align: left;
}
.sh-purpose-choice:hover { border-color: #D4A84B; background: #1e1e2a; }
.sh-purpose-choice:focus-visible { outline: 2px solid #D4A84B; outline-offset: 2px; }
.sh-purpose-choice-icon {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; flex-shrink: 0;
  background: rgba(212, 168, 75, 0.1);
}
.sh-purpose-choice-text {
  display: flex; flex-direction: column; gap: 2px;
}
.sh-purpose-choice-title {
  font-weight: 500; color: #fff; font-size: 0.9rem;
}
.sh-purpose-choice-desc {
  font-size: 0.78rem; color: #888;
}

/* ── Feature list (welcome step) ──────────────────────────── */
.sh-onboarding-features {
  width: 100%; display: flex; flex-direction: column; gap: 8px;
}
.sh-onboarding-feature {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px;
  background: rgba(255,255,255,0.03); border-radius: 6px;
  font-size: 0.85rem; color: #ccc;
}
.sh-onboarding-feature-icon {
  font-size: 1rem; width: 24px; text-align: center; flex-shrink: 0;
}
.sh-onboarding-note {
  font-size: 0.8rem; color: #777; text-align: center; line-height: 1.5;
  padding: 8px 12px;
  background: rgba(212, 168, 75, 0.05); border-radius: 6px;
  width: 100%;
}
.sh-onboarding-desc {
  font-size: 0.78rem; color: #888; margin-top: 4px;
}
.sh-onboarding-field textarea {
  width: 100%; padding: 10px 14px; min-height: 80px; resize: vertical;
  background: #1a1a24; border: 1px solid #2a2a3a; border-radius: 6px;
  color: #e0e0e0; font-size: 0.95rem; outline: none; transition: border-color 0.2s;
  font-family: inherit; line-height: 1.5;
}
.sh-onboarding-field textarea:focus { border-color: #D4A84B; }

/* ── Animations ────────────────────────────────────────────── */
.sh-onb-fade-in { animation: sh-onb-fade-in 0.5s ease-out both; }
@keyframes sh-onb-fade-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ────────────────────────────────────────────── */
@media (max-width: 480px) {
  .sh-onboarding-content { padding: 20px 16px 24px; gap: 18px; }
  .sh-onboarding-steps { padding: 16px 12px 8px; }
  .sh-onboarding-field input,
  .sh-onboarding-field select,
  .sh-onboarding-textarea { padding: 12px 14px; font-size: 16px; }
  .sh-onboarding-btn { padding: 12px 14px; }
  .sh-onboarding-btn-secondary { padding: 12px 14px; }
}

/* ── Reduced motion ────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .sh-onboarding-content { animation: none; opacity: 1; }
  .sh-onb-fade-in { animation: none; opacity: 1; }
  @keyframes sh-onb-spin { to { transform: rotate(360deg); } }
}
`;
