/**
 * Shared Auth Styles — Single source of CSS for all auth pages.
 *
 * Extracted from login-page.tsx patterns. Every auth component
 * imports `authStyles` instead of duplicating CSS.
 */

export const authStyles = `
/* ── Root Container ─────────────────────────────────────────── */
.sh-auth {
  position: fixed; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: #0a0a0f;
  color: #e0e0e0;
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
  overflow: hidden;
}

/* ── Card ──────────────────────────────────────────────────── */
.sh-auth-card {
  display: flex; flex-direction: column; align-items: center;
  gap: 28px; width: 100%; max-width: 400px; padding: 28px 24px;
}

/* ── Header ────────────────────────────────────────────────── */
.sh-auth-header { text-align: center; }
.sh-auth-zero { font-size: 2.5rem; color: #fff; font-weight: 300; }
.sh-auth-sub { font-size: 0.85rem; color: #666; letter-spacing: 0.2em; text-transform: uppercase; margin-top: 4px; }

/* ── Form ──────────────────────────────────────────────────── */
.sh-auth-form { width: 100%; display: flex; flex-direction: column; gap: 16px; }

.sh-auth-field label {
  display: block; font-size: 0.75rem; color: #888; margin-bottom: 4px; letter-spacing: 0.05em;
}
.sh-auth-field input {
  width: 100%; padding: 10px 14px;
  background: #1a1a24; border: 1px solid #2a2a3a; border-radius: 6px;
  color: #e0e0e0; font-size: 0.95rem; outline: none; transition: border-color 0.2s;
}
.sh-auth-field input:focus { border-color: #D4A84B; }
.sh-auth-field input:disabled { opacity: 0.5; cursor: not-allowed; }
.sh-auth-field input::placeholder { color: #555; }

/* ── Footer / links ────────────────────────────────────────── */
.sh-auth-footer {
  width: 100%; text-align: center;
  font-size: 0.75rem; color: #555;
}
.sh-auth-link {
  color: #D4A84B; text-decoration: none; cursor: pointer;
  transition: opacity 0.2s;
}
.sh-auth-link:hover { opacity: 0.8; text-decoration: underline; }
.sh-auth-link:focus-visible {
  outline: 2px solid #D4A84B; outline-offset: 2px; border-radius: 2px;
}
.sh-auth-link:disabled { opacity: 0.3; cursor: not-allowed; }

/* ── Button ────────────────────────────────────────────────── */
.sh-auth-btn {
  width: 100%; padding: 10px 14px;
  background: #D4A84B; color: #0a0a0f;
  border: none; border-radius: 6px; font-size: 0.95rem; font-weight: 500;
  cursor: pointer; transition: opacity 0.2s;
}
.sh-auth-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-auth-btn:hover:not(:disabled) { opacity: 0.85; }
.sh-auth-btn:focus-visible {
  outline: 2px solid #D4A84B; outline-offset: 2px;
}

/* ── Secondary button (ghost) ──────────────────────────────── */
.sh-auth-btn-secondary {
  width: 100%; padding: 10px 14px;
  background: transparent; color: #D4A84B;
  border: 1px solid #2a2a3a; border-radius: 6px; font-size: 0.95rem; font-weight: 400;
  cursor: pointer; transition: all 0.2s;
}
.sh-auth-btn-secondary:disabled { opacity: 0.3; cursor: not-allowed; }
.sh-auth-btn-secondary:hover:not(:disabled) { border-color: #D4A84B; }
.sh-auth-btn-secondary:focus-visible {
  outline: 2px solid #D4A84B; outline-offset: 2px;
}

/* ── Status messages ───────────────────────────────────────── */
.sh-auth-error {
  font-size: 0.8rem; color: #f55; text-align: center;
  background: rgba(255, 85, 85, 0.08); border: 1px solid rgba(255, 85, 85, 0.2);
  border-radius: 6px; padding: 8px 12px;
}
.sh-auth-success {
  font-size: 0.8rem; color: #4ade80; text-align: center;
  background: rgba(74, 222, 128, 0.08); border: 1px solid rgba(74, 222, 128, 0.2);
  border-radius: 6px; padding: 8px 12px;
}
.sh-auth-info {
  font-size: 0.8rem; color: #888; text-align: center;
  padding: 8px 12px;
}

/* ── Divider ────────────────────────────────────────────────── */
.sh-auth-divider {
  width: 100%; display: flex; align-items: center; gap: 12px;
  color: #444; font-size: 0.7rem; letter-spacing: 0.1em;
}
.sh-auth-divider::before,
.sh-auth-divider::after { content: ''; flex: 1; height: 1px; background: #2a2a3a; }

/* ── Animations ────────────────────────────────────────────── */
.sh-auth-fade-in { animation: sh-auth-fade-in 0.6s ease-out both; }
@keyframes sh-auth-fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ────────────────────────────────────────────── */
@media (max-width: 480px) {
  .sh-auth-card { padding: 20px 16px; gap: 20px; }
  .sh-auth-zero { font-size: 2rem; }
  .sh-auth-field input { padding: 12px 14px; font-size: 16px; } /* prevent iOS zoom */
  .sh-auth-btn { padding: 12px 14px; }
}

/* ── Reduced motion ────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .sh-auth-fade-in { animation: none; opacity: 1; }
}

/* ── Loading spinner ───────────────────────────────────────── */
.sh-auth-spinner {
  display: inline-block; width: 16px; height: 16px;
  border: 2px solid rgba(212, 168, 75, 0.3);
  border-top-color: #D4A84B;
  border-radius: 50%; animation: sh-auth-spin 0.6s linear infinite;
  vertical-align: middle; margin-right: 6px;
}
@keyframes sh-auth-spin { to { transform: rotate(360deg); } }
`;