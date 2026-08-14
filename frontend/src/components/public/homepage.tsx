/**
 * SHUNYA Public Homepage — Landing page for unauthenticated visitors.
 *
 * Dark theme matching the auth pages (sh-auth). Shows the SHUNYA brand
 * और शून्य (zero) identity with a call to action to enter the app.
 */
import { useState } from 'react';
import { PricingSection } from './pricing';

interface Props {
  onEnterApp: () => void;
}

export function HomePage({ onEnterApp }: Props) {
  const [showPricing, setShowPricing] = useState(false);

  if (showPricing) {
    return (
      <div className="sh-auth">
        <div className="sh-public">
          <div className="sh-public-header">
            <button className="sh-public-back-btn" onClick={() => setShowPricing(false)}>
              ← Back
            </button>
          </div>
          <PricingSection />
        </div>
        <style>{homepageStyles}</style>
      </div>
    );
  }

  return (
    <div className="sh-auth">
      <div className="sh-public">
        <div className="sh-public-hero">
          <h1 className="sh-public-zero" style={{fontSize:'inherit',fontWeight:'inherit',margin:0,padding:0}}>शून्य</h1>
          <h2 className="sh-public-sub" style={{fontSize:'inherit',fontWeight:'inherit',margin:0,padding:0}}>SHUNYA</h2>
          <h3 className="sh-public-tagline" style={{fontSize:'inherit',fontWeight:'inherit',margin:0,padding:0}}>
            One Operating System for Your Business
          </h3>
          <div className="sh-public-description">
            An intelligent operating system that understands your business
            as a living system, not a database.
          </div>
          <div className="sh-public-actions">
            <button className="sh-auth-btn" onClick={onEnterApp}>
              Get Started
            </button>
            <button
              className="sh-auth-btn-secondary"
              onClick={() => setShowPricing(true)}
            >
              View Pricing
            </button>
          </div>
        </div>
        <div className="sh-public-footer">
          <a href="https://shunyaos.com" className="sh-public-link" target="_blank" rel="noopener noreferrer">
            shunyaos.com
          </a>
          <span className="sh-public-dot">·</span>
          <span>AI Operating System</span>
        </div>
      </div>
      <style>{homepageStyles}</style>
    </div>
  );
}

export const homepageStyles = `
/* ── Public Homepage Layout ─────────────────────────────────── */
.sh-public {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 40px;
  min-height: 100vh;
  padding: 40px 24px;
  text-align: center;
}

.sh-public-header {
  width: 100%;
  text-align: left;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 10;
}

.sh-public-back-btn {
  padding: 8px 16px;
  background: transparent;
  color: #D4A84B;
  border: 1px solid #2a2a3a;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.sh-public-back-btn:hover {
  border-color: #D4A84B;
}
.sh-public-back-btn:focus-visible {
  outline: 2px solid #D4A84B;
  outline-offset: 2px;
}

/* ── Hero Section ───────────────────────────────────────────── */
.sh-public-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  max-width: 600px;
}

.sh-public-zero {
  font-size: clamp(3rem, 10vw, 6rem);
  color: #fff;
  font-weight: 300;
  opacity: 0.8;
}

.sh-public-sub {
  font-size: clamp(0.85rem, 2vw, 1.1rem);
  color: #666;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  margin-top: -8px;
}

.sh-public-tagline {
  font-size: clamp(1.2rem, 3vw, 1.8rem);
  font-weight: 500;
  color: #e0e0e0;
  margin-top: 8px;
}

.sh-public-description {
  font-size: clamp(0.85rem, 1.5vw, 1rem);
  color: #888;
  line-height: 1.6;
  max-width: 480px;
}

.sh-public-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.sh-public-actions .sh-auth-btn {
  width: auto;
  min-width: 160px;
  padding: 12px 24px;
}

.sh-public-actions .sh-auth-btn-secondary {
  width: auto;
  min-width: 160px;
  padding: 12px 24px;
}

/* ── Footer ─────────────────────────────────────────────────── */
.sh-public-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  color: #555;
}

.sh-public-link {
  color: #D4A84B;
  text-decoration: none;
  transition: opacity 0.2s;
}
.sh-public-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}
.sh-public-link:focus-visible {
  outline: 2px solid #D4A84B;
  outline-offset: 2px;
  border-radius: 2px;
}

.sh-public-dot {
  color: #444;
}

/* ── Responsive ─────────────────────────────────────────────── */
@media (max-width: 480px) {
  .sh-public { gap: 32px; padding: 24px 16px; }
  .sh-public-actions .sh-auth-btn,
  .sh-public-actions .sh-auth-btn-secondary {
    width: 100%;
    min-width: auto;
  }
  .sh-public-back-btn { font-size: 0.8rem; padding: 8px 12px; }
}

/* ── Reduced motion ─────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .sh-public-hero { animation: none; }
}
`;