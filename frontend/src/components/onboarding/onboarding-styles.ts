/**
 * Shared Onboarding Styles — Continuous with auth and workspace.
 *
 * Per Z-12 Article I: One visual language across all surfaces.
 * Per Constitution §8: Onboarding shares the same warm white, purple,
 * gold system as auth and workspace. No visual discontinuity.
 */

export const onboardingStyles = `
/* ── Onboarding Root ──────────────────────────────────────── */
.sh-onboarding {
  position: fixed; inset: 0;
  display: flex; flex-direction: column;
  background: var(--sh-bg, #FDFCF9);
  color: var(--sh-text, #1A1C1D);
  font-family: var(--sh-font-body);
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
  background: var(--sh-border, rgba(26,28,29,0.08));
  transition: all 0.3s ease;
}
.sh-onboarding-step-dot.active {
  background: var(--sh-purple, #6C4AE2);
  width: 24px; border-radius: 4px;
}
.sh-onboarding-step-dot.completed {
  background: var(--sh-success, #2D6A4F);
  opacity: 0.6;
}
.sh-onboarding-step-label {
  font-size: 0.7rem;
  color: var(--sh-text-tertiary, rgba(26,28,29,0.35));
  text-align: center; letter-spacing: 0.05em; margin-top: 4px;
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
  font-family: var(--sh-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: clamp(2rem, 8vw, 3rem);
  color: var(--sh-text, #1A1C1D); font-weight: 300;
}
.sh-onboarding-title {
  font-size: clamp(1.3rem, 4vw, 1.6rem);
  font-weight: 500; color: var(--sh-text, #1A1C1D);
  text-align: center; letter-spacing: -0.01em;
}
.sh-onboarding-subtitle {
  font-size: 0.9rem;
  color: var(--sh-text-secondary, rgba(26,28,29,0.55));
  text-align: center; line-height: 1.6;
  max-width: 380px;
}

/* ── Form ─────────────────────────────────────────────────── */
.sh-onboarding-form {
  width: 100%; display: flex; flex-direction: column; gap: 16px;
}
.sh-onboarding-field label {
  display: block; font-size: 0.75rem;
  color: var(--sh-text-secondary, rgba(26,28,29,0.55));
  margin-bottom: 4px; letter-spacing: 0.05em;
}
.sh-onboarding-field input,
.sh-onboarding-field select {
  width: 100%; padding: 10px 14px;
  background: var(--sh-surface, #FFFFFF);
  border: 1px solid var(--sh-border, rgba(26,28,29,0.08));
  border-radius: var(--sh-radius-md, 8px);
  color: var(--sh-text, #1A1C1D);
  font-size: 0.95rem; outline: none; transition: border-color 0.2s;
  font-family: var(--sh-font-body);
}
.sh-onboarding-field input:focus,
.sh-onboarding-field select:focus {
  border-color: var(--sh-purple, #6C4AE2);
  box-shadow: 0 0 0 3px var(--sh-purple-glow, rgba(108,74,226,0.15));
}
.sh-onboarding-field input:disabled,
.sh-onboarding-field select:disabled { opacity: 0.5; cursor: not-allowed; }
.sh-onboarding-field input::placeholder { color: var(--sh-text-tertiary, rgba(26,28,29,0.35)); }
.sh-onboarding-field select option { background: var(--sh-surface, #FFFFFF); color: var(--sh-text, #1A1C1D); }

/* ── Textarea for AI demo ─────────────────────────────────── */
.sh-onboarding-textarea {
  width: 100%; padding: 10px 14px; min-height: 80px; resize: vertical;
  background: var(--sh-surface, #FFFFFF);
  border: 1px solid var(--sh-border, rgba(26,28,29,0.08));
  border-radius: var(--sh-radius-md, 8px);
  color: var(--sh-text, #1A1C1D);
  font-size: 0.95rem; outline: none; transition: border-color 0.2s;
  font-family: var(--sh-font-body); line-height: 1.5;
}
.sh-onboarding-textarea:focus {
  border-color: var(--sh-purple, #6C4AE2);
  box-shadow: 0 0 0 3px var(--sh-purple-glow, rgba(108,74,226,0.15));
}
.sh-onboarding-textarea:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Buttons ──────────────────────────────────────────────── */
.sh-onboarding-btn {
  width: 100%; padding: 10px 14px;
  background: var(--sh-purple, #6C4AE2); color: #FFFFFF;
  border: none; border-radius: var(--sh-radius-md, 8px);
  font-size: 0.95rem; font-weight: 500;
  cursor: pointer; transition: opacity 0.2s;
  font-family: var(--sh-font-body);
}
.sh-onboarding-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-onboarding-btn:hover:not(:disabled) { opacity: 0.85; }
.sh-onboarding-btn:focus-visible {
  outline: 2px solid var(--sh-purple, #6C4AE2);
  outline-offset: 2px;
}

.sh-onboarding-btn-secondary {
  padding: 10px 14px;
  background: transparent; color: var(--sh-purple, #6C4AE2);
  border: 1px solid var(--sh-border, rgba(26,28,29,0.08));
  border-radius: var(--sh-radius-md, 8px);
  font-size: 0.9rem; font-weight: 400;
  cursor: pointer; transition: all 0.2s;
  font-family: var(--sh-font-body);
}
.sh-onboarding-btn-secondary:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-onboarding-btn-secondary:hover:not(:disabled) {
  border-color: var(--sh-purple, #6C4AE2);
  background: var(--sh-purple-subtle, rgba(108,74,226,0.08));
}
.sh-onboarding-btn-secondary:focus-visible {
  outline: 2px solid var(--sh-purple, #6C4AE2);
  outline-offset: 2px;
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
  font-size: 0.8rem; color: var(--sh-danger, #B91C1C); text-align: center;
  background: rgba(185, 28, 28, 0.06);
  border: 1px solid rgba(185, 28, 28, 0.12);
  border-radius: var(--sh-radius-md, 8px);
  padding: 8px 12px; width: 100%;
}
.sh-onboarding-success {
  font-size: 0.85rem; color: var(--sh-success, #2D6A4F); text-align: center;
  background: rgba(45, 106, 79, 0.06);
  border: 1px solid rgba(45, 106, 79, 0.12);
  border-radius: var(--sh-radius-md, 8px);
  padding: 10px 14px; width: 100%;
  line-height: 1.5;
}
.sh-onboarding-info {
  font-size: 0.8rem;
  color: var(--sh-text-secondary, rgba(26,28,29,0.55));
  text-align: center; padding: 8px 12px;
}

/* ── Spinner ──────────────────────────────────────────────── */
.sh-onboarding-spinner {
  display: inline-block; width: 16px; height: 16px;
  border: 2px solid rgba(108, 74, 226, 0.2);
  border-top-color: var(--sh-purple, #6C4AE2);
  border-radius: 50%; animation: sh-onb-spin 0.6s linear infinite;
  vertical-align: middle; margin-right: 6px;
}
@keyframes sh-onb-spin { to { transform: rotate(360deg); } }

/* ── AI message bubbles ───────────────────────────────────── */
.sh-onboarding-ai-message {
  width: 100%; padding: 12px 16px;
  background: var(--sh-surface-subtle, #F8F7F4);
  border: 1px solid var(--sh-border, rgba(26,28,29,0.08));
  border-radius: 10px; line-height: 1.6; font-size: 0.9rem;
  white-space: pre-wrap;
  color: var(--sh-text, #1A1C1D);
}
.sh-onboarding-ai-message .sh-onboarding-ai-label {
  font-size: 0.7rem;
  color: var(--sh-gold, #A4865F);
  letter-spacing: 0.05em;
  text-transform: uppercase; margin-bottom: 6px; font-weight: 500;
}

/* ── Summary section ──────────────────────────────────────── */
.sh-onboarding-summary { width: 100%; }
.sh-onboarding-summary-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  background: var(--sh-surface-subtle, #F8F7F4);
  border: 1px solid var(--sh-border, rgba(26,28,29,0.08));
  border-radius: var(--sh-radius-md, 8px);
  margin-bottom: 8px;
}
.sh-onboarding-summary-icon {
  width: 28px; height: 28px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem; flex-shrink: 0;
}
.sh-onboarding-summary-icon.gold { background: var(--sh-gold-glow, rgba(164,134,95,0.08)); color: var(--sh-gold, #A4865F); }
.sh-onboarding-summary-icon.green { background: rgba(45, 106, 79, 0.08); color: var(--sh-success, #2D6A4F); }
.sh-onboarding-summary-text { font-size: 0.85rem; color: var(--sh-text-secondary, rgba(26,28,29,0.55)); }
.sh-onboarding-summary-text strong { color: var(--sh-text, #1A1C1D); }

/* ── Animations ────────────────────────────────────────────── */
.sh-onb-fade-in { animation: sh-onb-fade-in 0.4s ease-out both; }
@keyframes sh-onb-fade-in {
  from { opacity: 0; transform: translateY(8px); }
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
