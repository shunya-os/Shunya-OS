/**
 * SHUNYA Public Homepage — Canonical warm-light landing.
 *
 * Visual Design Bible §3, §4, §5:
 *   Warm white background (#fbfaf8)
 *   Playfair Display for headings (42px, 400 weight)
 *   Gold accent for identity marks only
 *   Buttons use dark text colour (#1A1C1D), NOT gold
 *   Hero artwork (SVG ribbons/halos — placeholder)
 *   "Infinite Intelligence. Zero Noise." tagline
 *
 * Directive §17: Public → authenticated continuity.
 * The transition must preserve visual language, tone, motion,
 * typography, SHUNYA presence, calmness, identity.
 */

interface Props {
 onEnterApp: () => void;
}

export function HomePage({ onEnterApp }: Props) {
  return (
    <div className="sh-public-root">
      <div className="sh-public" role="main" aria-label="SHUNYA homepage">
        {/* Hero Artwork Layer (placeholder — match design bible spec) */}
        <div className="sh-public-artwork" aria-hidden="true">
          <div className="sh-public-artwork-ambient" />
          <div className="sh-public-artwork-warmth" />
          <div className="sh-public-artwork-toplight" />
          {/*
            TODO: Import actual SVG hero artwork from static/img/artwork-hero.svg
            The canonical artwork has:
            - Ribbons (7px, 3.5px, 2px) with gentle undulation animation
            - Halos (190px, 150px, 100px) rotating at 80s/60s/45s
            - Devanagari text at centre
            - "INFINITE INTELLIGENCE. ZERO NOISE."
          */}
        </div>

        {/* Identity Content */}
        <div className="sh-public-hero">
          <div className="sh-public-gold-dot" aria-hidden="true" />
          <h1 className="sh-public-zero">शून्य</h1>
          <h2 className="sh-public-sub">SHUNYA</h2>
          <p className="sh-public-tagline">Infinite Intelligence. Zero Noise.</p>
          <p className="sh-public-description">
            An intelligent operating system that understands your business
            as a living system, not a database.
          </p>
          <div className="sh-public-actions">
            <button className="sh-public-btn sh-public-btn-primary" onClick={onEnterApp}>
              Get Started
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="sh-public-footer" role="contentinfo">
        <span className="sh-public-footer-dot" aria-hidden="true" />
        <span>AI Operating System</span>
      </div>

      <style>{`
/* ── SHUNYA Public Homepage — Canonical Warm Light ─────────── */

.sh-public-root {
  position: fixed; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  background: var(--shunya-bg, #FBF8F5);
  color: var(--shunya-text, #1A1C1D);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.sh-public {
  position: fixed; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  overflow: hidden;
}

.sh-public-inner {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  min-height: 100vh;
  width: 100%;
  padding: 40px 24px;
}

/* ── Hero Artwork (placeholder) ───────────────────────────── */

.sh-public-artwork {
  position: fixed; inset: 0;
  pointer-events: none;
  z-index: 0;
}

.sh-public-artwork-ambient {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 40%, #FAF8F5 0%, #F5F2ED 50%, transparent 70%);
}

.sh-public-artwork-warmth {
  position: absolute;
  width: 500px; height: 500px;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(212,192,168,0.15) 0%, rgba(164,134,95,0.06) 40%, transparent 70%);
}

.sh-public-artwork-toplight {
  position: absolute;
  width: 800px; height: 400px;
  top: 10%; left: 50%;
  transform: translateX(-50%);
  background: radial-gradient(ellipse, rgba(255,255,255,0.5) 0%, transparent 70%);
}

/* ── Gold Dot ──────────────────────────────────────────────── */

.sh-public-gold-dot {
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--shunya-gold, #A4865F);
  margin-bottom: 16px;
}

/* ── Hero Content ──────────────────────────────────────────── */

.sh-public-hero {
  position: relative;
  z-index: 1;
  display: flex; flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 680px;
  padding: 40px 24px;
  gap: 8px;
}

.sh-public-zero {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 3rem;
  font-weight: 400;
  letter-spacing: var(--shunya-tracking-wider, 0.06em);
  line-height: 1.1;
  color: var(--shunya-text, #1A1C1D);
  margin: 0;
}

.sh-public-sub {
  font-family: var(--shunya-font-display, 'Playfair Display', serif);
  font-size: 2.5rem;
  font-weight: 400;
  letter-spacing: var(--shunya-tracking-tight, -0.025em);
  line-height: 1.08;
  color: var(--shunya-text, #1A1C1D);
  margin: 0;
}

.sh-public-tagline {
  font-family: var(--shunya-font-display, 'Playfair Display', serif);
  font-size: 1.1rem;
  font-weight: 400;
  font-style: italic;
  letter-spacing: var(--shunya-tracking-ultra, 0.2em);
  text-transform: uppercase;
  color: var(--shunya-gold-accessible, #7A6848);
  margin: 12px 0 0;
  line-height: 1.5;
}

.sh-public-description {
  font-size: var(--shunya-text-md, 16px);
  line-height: 1.6;
  color: var(--shunya-text-secondary, #636363);
  max-width: 440px;
  margin: 8px 0 0;
}

/* ── Buttons ──────────────────────────────────────────────── */

.sh-public-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.sh-public-btn {
  padding: 10px 24px;
  border-radius: var(--shunya-radius-sm, 10px);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  font-size: var(--shunya-text-sm, 12px);
  font-weight: 500;
  letter-spacing: var(--shunya-tracking-wide, 0.02em);
  cursor: pointer;
  transition: opacity var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
  outline: none;
}

.sh-public-btn-primary {
  background: var(--shunya-text, #1A1C1D);
  color: var(--shunya-surface, #FFFFFF);
  border: none;
}
.sh-public-btn-primary:hover { opacity: 0.85; }
.sh-public-btn-primary:focus-visible {
  outline: 2px solid var(--shunya-gold, #A4865F);
  outline-offset: 2px;
}

.sh-public-btn-secondary {
  background: transparent;
  color: var(--shunya-text, #1A1C1D);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.sh-public-btn-secondary:hover {
  border-color: var(--shunya-border-hover, rgba(26,28,29,0.14));
}
.sh-public-btn-secondary:focus-visible {
  outline: 2px solid var(--shunya-gold, #A4865F);
  outline-offset: 2px;
}

/* ── Footer ────────────────────────────────────────────────── */

.sh-public-footer {
  position: fixed;
  bottom: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  letter-spacing: var(--shunya-tracking-wide, 0.02em);
}

.sh-public-footer-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--shunya-gold, #A4865F);
}

/* ── Back button (pricing) ─────────────────────────────────── */

.sh-public-header {
  position: fixed; top: 16px; left: 16px; z-index: 10;
}

.sh-public-back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: transparent;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-sm, 10px);
  font-size: var(--shunya-text-sm, 12px);
  font-weight: 500;
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  cursor: pointer;
  transition: color var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-public-back:hover { color: var(--shunya-text, #1A1C1D); }

/* ── Reduced motion ────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .sh-public-artwork-warmth { animation: none; }
  .sh-public-artwork-ambient { animation: none; }
}

/* ── Responsive ────────────────────────────────────────────── */
@media (max-width: 480px) {
  .sh-public-zero { font-size: 2.2rem; }
  .sh-public-sub { font-size: 1.8rem; }
  .sh-public-tagline { font-size: 0.85rem; letter-spacing: 0.15em; }
  .sh-public-description { font-size: var(--shunya-text-base, 14px); }
  .sh-public-actions { flex-direction: column; width: 100%; }
  .sh-public-btn { width: 100%; text-align: center; }
}
      `}</style>
    </div>
  );
}