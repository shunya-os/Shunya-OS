/**
 * Shared Auth Styles — Single source of CSS for all auth pages.
 *
 * Per Z-12 Article VI: Authentication feels like entering an existing workspace.
 * Same visual language as homepage and workspace — warm white, purple primary,
 * gold secondary. No visual discontinuity.
 *
 * Per Constitution §7:
 * - Card: white surface with soft shadow on warm white background
 * - Background identical to homepage (var(--sh-bg))
 * - Purple focus ring on inputs
 * - Purple primary button
 * - Gold secondary actions
 */

export const authStyles = `
/* ── Root Container ─────────────────────────────────────────── */
.sh-auth {
  position: fixed; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--sh-bg, #FDFCF9);
  color: var(--sh-text, #1A1C1D);
  font-family: var(--sh-font-body);
  overflow: hidden;
}

/* ── Card ──────────────────────────────────────────────────── */
.sh-auth-card {
  display: flex; flex-direction: column; align-items: center;
  gap: 28px; width: 100%; max-width: 400px; padding: 28px 24px;
}

/* ── Header ────────────────────────────────────────────────── */
.sh-auth-header { text-align: center; }
.sh-auth-zero {
  font-family: var(--sh-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 2.5rem; color: var(--sh-text, #1A1C1D); font-weight: 300;
}
.sh-auth-sub {
  font-size: 0.85rem; color: var(--sh-text-secondary, rgba(26,28,29,0.55));
  letter-spacing: 0.2em; text-transform: uppercase; margin-top: 4px;
}

/* ── Form ──────────────────────────────────────────────────── */
.sh-auth-form { width: 100%; display: flex; flex-direction: column; gap: 16px; }

.sh-auth-field label {
  display: block; font-size: 0.75rem;
  color: var(--sh-text-secondary, rgba(26,28,29,0.55));
  margin-bottom: 4px; letter-spacing: 0.05em;
}
.sh-auth-field input {
  width: 100%; padding: 10px 14px;
  background: var(--sh-surface, #FFFFFF);
  border: 1px solid var(--sh-border, rgba(26,28,29,0.08));
  border-radius: var(--sh-radius-md, 8px);
  color: var(--sh-text, #1A1C1D); font-size: 0.95rem;
  outline: none; transition: border-color 0.2s;
  font-family: var(--sh-font-body);
}
.sh-auth-field input:focus {
  border-color: var(--sh-purple, #6C4AE2);
  box-shadow: 0 0 0 3px var(--sh-purple-glow, rgba(108,74,226,0.15));
}
.sh-auth-field input:disabled { opacity: 0.5; cursor: not-allowed; }
.sh-auth-field input::placeholder { color: var(--sh-text-tertiary, rgba(26,28,29,0.35)); }

/* ── Footer / links ────────────────────────────────────────── */
.sh-auth-footer {
  width: 100%; text-align: center;
  font-size: 0.75rem; color: var(--sh-text-tertiary, rgba(26,28,29,0.35));
}
.sh-auth-link {
  color: var(--sh-gold, #A4865F); text-decoration: none; cursor: pointer;
  transition: opacity 0.2s;
}
.sh-auth-link:hover { opacity: 0.8; text-decoration: underline; }
.sh-auth-link:focus-visible {
  outline: 2px solid var(--sh-purple, #6C4AE2);
  outline-offset: 2px; border-radius: 2px;
}
.sh-auth-link:disabled { opacity: 0.3; cursor: not-allowed; }

/* ── Primary Button ────────────────────────────────────────── */
.sh-auth-btn {
  width: 100%; padding: 10px 14px;
  background: var(--sh-purple, #6C4AE2); color: #FFFFFF;
  border: none; border-radius: var(--sh-radius-md, 8px);
  font-size: 0.95rem; font-weight: 500;
  cursor: pointer; transition: opacity 0.2s;
  font-family: var(--sh-font-body);
}
.sh-auth-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-auth-btn:hover:not(:disabled) { opacity: 0.85; }
.sh-auth-btn:focus-visible {
  outline: 2px solid var(--sh-purple, #6C4AE2);
  outline-offset: 2px;
}

/* ── Secondary button (ghost) ──────────────────────────────── */
.sh-auth-btn-secondary {
  width: 100%; padding: 10px 14px;
  background: transparent; color: var(--sh-purple, #6C4AE2);
  border: 1px solid var(--sh-border, rgba(26,28,29,0.08));
  border-radius: var(--sh-radius-md, 8px);
  font-size: 0.95rem; font-weight: 400;
  cursor: pointer; transition: all 0.2s;
  font-family: var(--sh-font-body);
}
.sh-auth-btn-secondary:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-auth-btn-secondary:hover:not(:disabled) {
  border-color: var(--sh-purple, #6C4AE2);
  background: var(--sh-purple-subtle, rgba(108,74,226,0.08));
}
.sh-auth-btn-secondary:focus-visible {
  outline: 2px solid var(--sh-purple, #6C4AE2);
  outline-offset: 2px;
}

/* ── Status messages ───────────────────────────────────────── */
.sh-auth-error {
  font-size: 0.8rem; color: var(--sh-danger, #B91C1C); text-align: center;
  background: rgba(185, 28, 28, 0.06);
  border: 1px solid rgba(185, 28, 28, 0.12);
  border-radius: var(--sh-radius-md, 8px); padding: 8px 12px;
}
.sh-auth-success {
  font-size: 0.8rem; color: var(--sh-success, #2D6A4F); text-align: center;
  background: rgba(45, 106, 79, 0.06);
  border: 1px solid rgba(45, 106, 79, 0.12);
  border-radius: var(--sh-radius-md, 8px); padding: 8px 12px;
}
.sh-auth-info {
  font-size: 0.8rem;
  color: var(--sh-text-secondary, rgba(26,28,29,0.55));
  text-align: center; padding: 8px 12px;
}

/* ── Divider ────────────────────────────────────────────────── */
.sh-auth-divider {
  width: 100%; display: flex; align-items: center; gap: 12px;
  color: var(--sh-text-tertiary, rgba(26,28,29,0.35));
  font-size: 0.7rem; letter-spacing: 0.1em;
}
.sh-auth-divider::before,
.sh-auth-divider::after { content: ''; flex: 1; height: 1px; background: var(--sh-border, rgba(26,28,29,0.08)); }

/* ── Tab Toggle ────────────────────────────────────────────── */
.sh-auth-tabs {
  display: flex; width: 100%;
  border: 1px solid var(--sh-border, rgba(26,28,29,0.08));
  border-radius: var(--sh-radius-md, 8px); overflow: hidden;
}
.sh-auth-tab {
  flex: 1; padding: 10px 14px;
  background: transparent;
  color: var(--sh-text-secondary, rgba(26,28,29,0.55));
  border: none; font-size: 0.85rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
  font-family: var(--sh-font-body);
}
.sh-auth-tab.active {
  background: var(--sh-purple, #6C4AE2);
  color: #FFFFFF;
}
.sh-auth-tab:hover:not(.active):not(:disabled) {
  color: var(--sh-purple, #6C4AE2);
  background: var(--sh-purple-subtle, rgba(108,74,226,0.08));
}
.sh-auth-tab:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-auth-tab:focus-visible {
  outline: 2px solid var(--sh-purple, #6C4AE2);
  outline-offset: -2px;
}

/* ── Animations ────────────────────────────────────────────── */
.sh-auth-fade-in { animation: sh-auth-fade-in 0.4s ease-out both; }
@keyframes sh-auth-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ────────────────────────────────────────────── */
@media (max-width: 480px) {
  .sh-auth-card { padding: 20px 16px; gap: 20px; }
  .sh-auth-zero { font-size: 2rem; }
  .sh-auth-field input { padding: 12px 14px; font-size: 16px; }
  .sh-auth-btn { padding: 12px 14px; }
}

/* ── Reduced motion ────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .sh-auth-fade-in { animation: none; opacity: 1; }
}

/* ── Loading spinner ───────────────────────────────────────── */
.sh-auth-spinner {
  display: inline-block; width: 16px; height: 16px;
  border: 2px solid rgba(108, 74, 226, 0.2);
  border-top-color: var(--sh-purple, #6C4AE2);
  border-radius: 50%; animation: sh-auth-spin 0.6s linear infinite;
  vertical-align: middle; margin-right: 6px;
}
@keyframes sh-auth-spin { to { transform: rotate(360deg); } }
`;
