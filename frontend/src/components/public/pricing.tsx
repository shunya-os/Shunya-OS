/**
 * SHUNYA Public Homepage — Pricing Section.
 *
 * Three tiers: Starter, Business, Enterprise.
 * Same design language as the cinematic homepage.
 */

import { useRef, useState, useEffect } from 'react';

const TIERS = [
  {
    id: 'starter',
    name: 'Starter',
    subtitle: 'For small teams getting started',
    price: 'Free',
    period: 'forever',
    features: [
      'Up to 3 active projects',
      '5 contacts per project',
      'Basic memory & context',
      'Email support',
      'Community access',
    ],
    cta: 'Get Started',
    href: '#',
    highlighted: false,
  },
  {
    id: 'business',
    name: 'Business',
    subtitle: 'For growing organisations',
    price: '₹5,999',
    period: '/month',
    features: [
      'Unlimited active projects',
      'Unlimited relationships',
      'Full memory & context retention',
      'AI proposal generation',
      'Priority email & chat support',
      'Custom integrations',
      'Team collaboration',
    ],
    cta: 'Start Free Trial',
    href: '#',
    highlighted: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    subtitle: 'For businesses with unique needs',
    price: 'Custom',
    period: '',
    features: [
      'Everything in Business',
      'Dedicated account manager',
      'On-premise deployment option',
      'Custom AI model training',
      'SLA guarantees',
      'Advanced security & compliance',
      'Unlimited API access',
      'White-label option',
    ],
    cta: 'Contact Sales',
    href: '#',
    highlighted: false,
  },
];

function useInView(ref: React.RefObject<HTMLElement | null>) {
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setInView(true);
      },
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);
  return inView;
}

function FadeInSection({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref);
  return (
    <div ref={ref} className={`hp-scene ${inView ? 'hp-visible' : 'hp-hidden'} ${className}`}>
      {children}
    </div>
  );
}

function PricingCard({ tier, index }: { tier: typeof TIERS[number]; index: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref);
  return (
    <div
      ref={ref}
      className={`hp-pricing-card ${tier.highlighted ? 'hp-pricing-highlighted' : ''} ${inView ? 'hp-pricing-card-visible' : 'hp-pricing-card-hidden'}`}
      style={{ transitionDelay: `${index * 0.15}s` }}
    >
      {tier.highlighted && <div className="hp-pricing-badge">Most Popular</div>}
      <div className="hp-pricing-card-header">
        <div className="hp-pricing-name">{tier.name}</div>
        <div className="hp-pricing-subtitle">{tier.subtitle}</div>
      </div>
      <div className="hp-pricing-price-row">
        <span className="hp-pricing-price">{tier.price}</span>
        {tier.period && <span className="hp-pricing-period">{tier.period}</span>}
      </div>
      <ul className="hp-pricing-features">
        {tier.features.map((f, i) => (
          <li key={i} className="hp-pricing-feature">
            <span className="hp-pricing-check">✓</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <a href={tier.href} className={`hp-pricing-cta ${tier.highlighted ? 'hp-pricing-cta-primary' : 'hp-pricing-cta-secondary'}`}>
        {tier.cta}
      </a>
    </div>
  );
}

export function PricingSection() {
  return (
    <section className="hp-pricing-section" id="pricing" aria-label="Pricing">
      <FadeInSection className="hp-pricing-intro-scene">
        <div className="hp-pricing-intro">
          <h2 className="hp-pricing-heading">Plans that fit your business</h2>
          <p className="hp-pricing-sub">
            Every business is different. Start where you are, scale when you're ready.
          </p>
        </div>
      </FadeInSection>

      <div className="hp-pricing-grid">
        {TIERS.map((tier, i) => (
          <PricingCard key={tier.id} tier={tier} index={i} />
        ))}
      </div>

      <style>{pricingStyles}</style>
    </section>
  );
}

const pricingStyles = `
/* ── Pricing Section ── */
.hp-pricing-section { padding: 4rem 2rem 6rem; max-width: 1200px; margin: 0 auto; container-type: inline-size; }
.hp-pricing-intro { text-align: center; margin-bottom: 3rem; }
.hp-pricing-heading { font-size: var(--fluid-2xl, 3rem); color: #fff; font-weight: 300; margin-bottom: 0.75rem; }
.hp-pricing-sub { font-size: var(--fluid-md, 1rem); color: var(--hp-text-secondary); max-width: 500px; margin: 0 auto; line-height: 1.6; }
.hp-pricing-intro-scene { min-height: auto !important; padding-top: 4rem !important; padding-bottom: 0 !important; }

/* ── Pricing Grid ── */
.hp-pricing-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; align-items: start; }

/* ── Pricing Card ── */
.hp-pricing-card { display: flex; flex-direction: column; background: var(--hp-surface); border: 1px solid #2a2a3a; border-radius: 16px; padding: 2rem; position: relative; transition: all 0.3s ease; }
.hp-pricing-card:hover { border-color: var(--hp-accent); transform: translateY(-4px); }
.hp-pricing-highlighted { background: linear-gradient(135deg, #1a1a2e 0%, #2a1f0e 100%); border-color: var(--hp-accent); box-shadow: 0 0 30px rgba(212, 168, 75, 0.08); }
.hp-pricing-highlighted:hover { box-shadow: 0 0 40px rgba(212, 168, 75, 0.15); }
.hp-pricing-badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--hp-accent); color: #000; font-size: var(--fluid-xs, 0.75rem); font-weight: 600; padding: 0.25rem 1rem; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.08em; }
.hp-pricing-card-header { margin-bottom: 1.5rem; }
.hp-pricing-name { font-size: var(--fluid-lg, 1.25rem); color: #fff; font-weight: 600; margin-bottom: 0.25rem; }
.hp-pricing-subtitle { font-size: var(--fluid-xs, 0.75rem); color: var(--hp-text-secondary); }
.hp-pricing-price-row { margin-bottom: 1.5rem; display: flex; align-items: baseline; gap: 0.25rem; }
.hp-pricing-price { font-size: var(--fluid-2xl, 2.5rem); font-weight: 300; color: #fff; }
.hp-pricing-period { font-size: var(--fluid-sm, 0.875rem); color: var(--hp-text-secondary); }
.hp-pricing-features { list-style: none; padding: 0; margin: 0 0 2rem; display: flex; flex-direction: column; gap: 0.75rem; flex: 1; }
.hp-pricing-feature { display: flex; align-items: center; gap: 0.5rem; font-size: var(--fluid-sm, 0.875rem); color: var(--hp-text); line-height: 1.4; }
.hp-pricing-check { color: var(--hp-accent); font-weight: 700; flex-shrink: 0; }

/* ── CTA Buttons ── */
.hp-pricing-cta { display: block; text-align: center; padding: 0.75rem 1.5rem; border-radius: 8px; font-size: var(--fluid-sm, 0.875rem); font-weight: 500; text-decoration: none; transition: all 0.3s; letter-spacing: 0.05em; }
.hp-pricing-cta-primary { background: var(--hp-accent); color: #000; }
.hp-pricing-cta-primary:hover { opacity: 0.85; }
.hp-pricing-cta-secondary { background: transparent; border: 1px solid #444; color: var(--hp-text); }
.hp-pricing-cta-secondary:hover { border-color: var(--hp-accent); color: var(--hp-accent); }

/* ── Card Animation ── */
.hp-pricing-card-hidden { opacity: 0; transform: translateY(20px); transition: opacity 0.6s ease-out, transform 0.6s ease-out; }
.hp-pricing-card-visible { opacity: 1; transform: translateY(0); }

/* ── Adaptive ── */
@container (max-width: 800px) {
  .hp-pricing-grid { grid-template-columns: 1fr; max-width: 400px; margin: 0 auto; }
}
@container (min-width: 801px) and (max-width: 1100px) {
  .hp-pricing-grid { grid-template-columns: repeat(2, 1fr); }
  .hp-pricing-card:last-child { grid-column: 1 / -1; max-width: 400px; justify-self: center; }
}
`;