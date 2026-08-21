/**
 * Shared Auth Styles — Canonical warm-light theme.
 *
 * Visual Design Bible §6: Light mode only v1.0
 * Background: #fbfaf8 (warm white)
 * Surface: #ffffff
 * Gold accent: identity marks only (NOT buttons)
 * Buttons use --shunya-text (#1A1C1D) as primary interactive colour
 * Border radius: 10px (canonical sm)
 */

export const authStyles = `
/* ── Root Container ─────────────────────────────────────────── */
.sh-auth {
  position: fixed; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--shunya-bg, #FBF8F5);
  color: var(--shunya-text, #1A1C1D);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  overflow: hidden;
}

/* ── Card ──────────────────────────────────────────────────── */
.sh-auth-card {
  display: flex; flex-direction: column; align-items: center;
  gap: 32px; width: 100%; max-width: 400px; padding: 48px 32px;
  background: var(--shunya-surface, #FFFFFF);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-md, 16px);
  box-shadow: var(--shunya-shadow-md, 0 2px 12px rgba(26,28,29,0.05));
}

/* ── Header ────────────────────────────────────────────────── */
.sh-auth-header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.sh-auth-zero {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 2.5rem;
  color: var(--shunya-text, #1A1C1D);
  font-weight: 400;
  letter-spacing: var(--shunya-tracking-wider, 0.06em);
  line-height: 1.1;
}
.sh-auth-sub {
  font-family: var(--shunya-font-display, 'Playfair Display', serif);
  font-size: 1.1rem;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  letter-spacing: var(--shunya-tracking-wide, 0.02em);
  font-weight: 400;
  margin-top: 2px;
}
.sh-auth-gold-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--shunya-gold, #A4865F);
  margin: 8px auto 0;
}

/* ── Form ──────────────────────────────────────────────────── */
.sh-auth-form {
  width: 100%; display: flex; flex-direction: column; gap: 20px;
}

.sh-auth-field label {
  display: block;
  font-size: var(--shunya-text-xs, 10px);
  font-weight: 600;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  margin-bottom: 6px;
  letter-spacing: var(--shunya-tracking-wider, 0.06em);
  text-transform: uppercase;
}
.sh-auth-field input {
  width: 100%; padding: 10px 14px;
  background: var(--shunya-surface, #FFFFFF);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-sm, 10px);
  color: var(--shunya-text, #1A1C1D);
  font-size: var(--shunya-text-base, 14px);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  outline: none;
  transition: border-color var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-auth-field input:focus {
  border-color: var(--shunya-border-focus, #A4865F);
  box-shadow: 0 0 0 3px var(--shunya-gold-glow, rgba(164,134,95,0.08));
}
.sh-auth-field input:disabled {
  opacity: 0.4; cursor: not-allowed;
}
.sh-auth-field input::placeholder {
  color: var(--shunya-text-faint, rgba(26,28,29,0.15));
}

/* ── Buttons ──────────────────────────────────────────────── */
/* Per Visual Design Bible §6.2: Interactive elements use --shunya-text, NOT gold */

.sh-auth-btn {
  width: 100%; padding: 10px 22px;
  background: var(--shunya-text, #1A1C1D);
  color: var(--shunya-surface, #FFFFFF);
  border: none;
  border-radius: var(--shunya-radius-sm, 10px);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  font-size: var(--shunya-text-sm, 12px);
  font-weight: 500;
  letter-spacing: var(--shunya-tracking-wide, 0.02em);
  cursor: pointer;
  transition: opacity var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-auth-btn:hover:not(:disabled) { opacity: 0.85; }
.sh-auth-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.sh-auth-btn:focus-visible {
  outline: 2px solid var(--shunya-gold, #A4865F);
  outline-offset: 2px;
}

.sh-auth-btn-secondary {
  width: 100%; padding: 10px 22px;
  background: transparent;
  color: var(--shunya-text, #1A1C1D);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-sm, 10px);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  font-size: var(--shunya-text-sm, 12px);
  font-weight: 500;
  letter-spacing: var(--shunya-tracking-wide, 0.02em);
  cursor: pointer;
  transition: border-color var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-auth-btn-secondary:hover:not(:disabled) {
  border-color: var(--shunya-border-hover, rgba(26,28,29,0.14));
}
.sh-auth-btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }
.sh-auth-btn-secondary:focus-visible {
  outline: 2px solid var(--shunya-gold, #A4865F);
  outline-offset: 2px;
}

/* ── OAuth Buttons ──────────────────────────────────────────── */
.sh-auth-oauth {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.sh-auth-btn-oauth {
  width: 100%; padding: 10px 22px;
  background: var(--shunya-surface, #FFFFFF);
  color: var(--shunya-text, #1A1C1D);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-sm, 10px);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  font-size: var(--shunya-text-sm, 12px);
  font-weight: 500;
  letter-spacing: var(--shunya-tracking-wide, 0.02em);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: border-color var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1)),
              box-shadow var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-auth-btn-oauth:hover:not(:disabled) {
  border-color: var(--shunya-border-hover, rgba(26,28,29,0.14));
  box-shadow: 0 1px 4px rgba(26,28,29,0.04);
}
.sh-auth-btn-oauth:disabled { opacity: 0.4; cursor: not-allowed; }
.sh-auth-btn-oauth:focus-visible {
  outline: 2px solid var(--shunya-gold, #A4865F);
  outline-offset: 2px;
}
.sh-auth-oauth-icon {
  flex-shrink: 0;
}

/* ── Links ──────────────────────────────────────────────────── */
.sh-auth-link {
  color: var(--shunya-text, #1A1C1D);
  text-decoration: underline;
  text-decoration-color: var(--shunya-border, rgba(26,28,29,0.07));
  text-underline-offset: 2px;
  cursor: pointer;
  font-size: var(--shunya-text-sm, 12px);
  transition: text-decoration-color var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-auth-link:hover {
  text-decoration-color: var(--shunya-text, #1A1C1D);
}
.sh-auth-link:focus-visible {
  outline: 2px solid var(--shunya-gold, #A4865F);
  outline-offset: 2px;
  border-radius: 2px;
}

/* ── Status messages ───────────────────────────────────────── */
.sh-auth-error {
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-danger, #FF6B6B);
  text-align: center;
  background: rgba(255,107,107,0.06);
  border: 1px solid rgba(255,107,107,0.12);
  border-radius: var(--shunya-radius-sm, 10px);
  padding: 8px 12px;
  width: 100%;
}
.sh-auth-success {
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-success, #51CF66);
  text-align: center;
  background: rgba(81,207,102,0.06);
  border: 1px solid rgba(81,207,102,0.12);
  border-radius: var(--shunya-radius-sm, 10px);
  padding: 8px 12px;
  width: 100%;
}
.sh-auth-info {
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  text-align: center;
  padding: 8px 12px;
}

/* ── Divider ────────────────────────────────────────────────── */
.sh-auth-divider {
  width: 100%; display: flex; align-items: center; gap: 12px;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  font-size: var(--shunya-text-xs, 10px);
  letter-spacing: var(--shunya-tracking-wider, 0.06em);
  text-transform: uppercase;
}
.sh-auth-divider::before,
.sh-auth-divider::after {
  content: ''; flex: 1;
  height: 1px;
  background: var(--shunya-border, rgba(26,28,29,0.07));
}

/* ── Footer ────────────────────────────────────────────────── */
.sh-auth-footer {
  width: 100%; text-align: center;
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
}

/* ── Animations ────────────────────────────────────────────── */
.sh-auth-fade-in {
  animation: sh-auth-fade-in var(--shunya-duration-slow, 600ms) var(--shunya-ease-out, cubic-bezier(0.16,1,0.3,1)) both;
}
@keyframes sh-auth-fade-in {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ────────────────────────────────────────────── */
@media (max-width: 480px) {
  .sh-auth-card { padding: 32px 20px; gap: 24px; }
  .sh-auth-zero { font-size: 2rem; }
  .sh-auth-field input { padding: 12px 14px; font-size: 16px; }
  .sh-auth-btn { padding: 12px 22px; }
}

/* ── Reduced motion ────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .sh-auth-fade-in { animation: none; opacity: 1; }
}
`;