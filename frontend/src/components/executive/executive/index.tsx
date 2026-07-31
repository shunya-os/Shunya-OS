/**
 * Component Runtime — Core component system.
 *
 * Components are not mini-applications. They are visual projections of runtime state.
 * Every component receives state, renders it, and emits events. No business logic.
 *
 * ── Contract ──────────────────────────────────────────────────
 * - Components never fetch data (they receive it via props)
 * - Components never own state (they project it)
 * - Components never define layout (they are placed by the Layout Engine)
 * - Components never define business logic (they emit events)
 */

import type { ReactNode } from 'react';

// ── Base Props ────────────────────────────────────────────────

export interface ComponentProps<T = Record<string, unknown>> {
  /** The runtime state to project. */
  state: T;
  /** Previous state version (for animation). */
  previousVersion?: number;
  /** Whether the component is in a loading state. */
  loading?: boolean;
  /** Error message if the source runtime failed. */
  error?: string;
  /** Accessible label. */
  label?: string;
  /** Optional className for custom styling. */
  className?: string;
  /** Children (for composite components). */
  children?: ReactNode;
}

// ── Primitive Components ──────────────────────────────────────

export function Metric({ state, loading, error, label }: ComponentProps<{ value: string | number; trend?: number; subtitle?: string }>) {
  if (error) return <div className="sh-comp-metric sh-comp-error" role="alert">{error}</div>;
  if (loading) return <div className="sh-comp-metric sh-comp-skeleton" aria-busy="true"><div className="sh-skel-line w-24" /><div className="sh-skel-line w-16" /></div>;

  const trend = state.trend;
  const trendClass = trend ? (trend > 0 ? 'sh-trend-up' : trend < 0 ? 'sh-trend-down' : 'sh-trend-flat') : '';

  return (
    <div className="sh-comp-metric" role="figure" aria-label={label}>
      <div className="sh-metric-value">{state.value}</div>
      {trend !== undefined && <div className={`sh-metric-trend ${trendClass}`}>{trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend).toFixed(1)}%</div>}
      {state.subtitle && <div className="sh-metric-subtitle">{state.subtitle}</div>}
    </div>
  );
}

export function Badge({ state }: ComponentProps<{ text: string; variant?: 'success' | 'warning' | 'danger' | 'neutral' | 'info' }>) {
  const v = state.variant ?? 'neutral';
  return <span className={`sh-comp-badge sh-badge-${v}`}>{state.text}</span>;
}

export function StatusDot({ state }: ComponentProps<{ status: string; label?: string }>) {
  return <span className={`sh-comp-status-dot sh-status-${state.status}`} title={state.label ?? state.status} />;
}

// ── Object Components ─────────────────────────────────────────

export function ObjectIdentity({ state, loading }: ComponentProps<{ name: string; type: string; status: string; id: string }>) {
  if (loading) return <div className="sh-comp-identity sh-comp-skeleton" aria-busy="true"><div className="sh-skel-line w-40" /><div className="sh-skel-line w-20" /></div>;
  return (
    <div className="sh-comp-identity">
      <StatusDot state={{ status: state.status }} />
      <div className="sh-identity-name">{state.name}</div>
      <div className="sh-identity-type">{state.type}</div>
      <div className="sh-identity-id">{state.id.slice(0, 12)}</div>
    </div>
  );
}

export function TimelineEvent({ state }: ComponentProps<{
  title: string; description?: string; timestamp: number;
  type: string; commitmentImpact?: string;
}>) {
  const impact = state.commitmentImpact;
  const impactClass = impact ? `sh-timeline-impact-${impact}` : '';
  const date = new Date(state.timestamp);
  return (
    <div className={`sh-comp-timeline-event ${impactClass}`}>
      <div className="sh-event-dot" />
      <div className="sh-event-body">
        <div className="sh-event-title">{state.title}</div>
        {state.description && <div className="sh-event-desc">{state.description}</div>}
        <div className="sh-event-meta">{date.toLocaleDateString()} · {state.type}</div>
      </div>
    </div>
  );
}

export function InsightCard({ state }: ComponentProps<{
  title: string; body: string; confidence: 'high' | 'medium' | 'low'; type: string;
}>) {
  return (
    <div className={`sh-comp-insight sh-insight-${state.type}`}>
      <div className="sh-insight-header">
        <Badge state={{ text: state.confidence, variant: state.confidence === 'high' ? 'success' : state.confidence === 'medium' ? 'warning' : 'neutral' }} />
        <span className="sh-insight-type">{state.type}</span>
      </div>
      <div className="sh-insight-title">{state.title}</div>
      <div className="sh-insight-body">{state.body}</div>
    </div>
  );
}

// ── Commitment Components ─────────────────────────────────────

export function ProgressBar({ state }: ComponentProps<{ value: number; max?: number; label?: string }>) {
  const pct = Math.round((state.value / (state.max ?? 1)) * 100);
  const colour = pct >= 80 ? 'var(--shunya-color-success)' : pct >= 40 ? 'var(--shunya-color-warning)' : 'var(--shunya-color-danger)';
  return (
    <div className="sh-comp-progress" role="progressbar" aria-valuenow={pct} aria-label={state.label ?? 'Progress'}>
      <div className="sh-progress-track">
        <div className="sh-progress-fill" style={{ width: `${pct}%`, background: colour }} />
      </div>
      <div className="sh-progress-label">{pct}%</div>
    </div>
  );
}

export function ConfidenceMeter({ state }: ComponentProps<{ score: number; factors?: string[] }>) {
  const pct = Math.round(state.score * 100);
  const colour = pct >= 70 ? 'var(--shunya-color-success)' : pct >= 40 ? 'var(--shunya-color-warning)' : 'var(--shunya-color-danger)';
  return (
    <div className="sh-comp-confidence">
      <div className="sh-confidence-value" style={{ color: colour }}>{pct}%</div>
      <div className="sh-confidence-track">
        <div className="sh-confidence-fill" style={{ width: `${pct}%`, background: colour }} />
      </div>
      {state.factors && state.factors.length > 0 && (
        <div className="sh-confidence-factors">
          {state.factors.map((f, i) => <div key={i} className="sh-confidence-factor">{f}</div>)}
        </div>
      )}
    </div>
  );
}

export function BlockerList({ state }: ComponentProps<{ blockers: { description: string; severity: string; detected: number }[] }>) {
  if (!state.blockers?.length) return <div className="sh-comp-blockers sh-blockers-none">No blockers</div>;
  return (
    <div className="sh-comp-blockers">
      {state.blockers.map((b, i) => (
        <div key={i} className={`sh-blocker sh-blocker-${b.severity}`}>
          <span className="sh-blocker-dot" />
          <span className="sh-blocker-desc">{b.description}</span>
        </div>
      ))}
    </div>
  );
}

export function NextBestAction({ state }: ComponentProps<{ action: string; reason: string; confidence: string }>) {
  return (
    <div className="sh-comp-next-action">
      <div className="sh-next-action-title">Next: {state.action}</div>
      <div className="sh-next-action-reason">{state.reason}</div>
      <Badge state={{ text: `confidence: ${state.confidence}`, variant: 'info' }} />
    </div>
  );
}

// ── Conversation Components ───────────────────────────────────

export function ConversationCard({ state }: ComponentProps<{
  title: string; intent: string; status: string; participants: string[]; objectCount: number;
}>) {
  return (
    <div className="sh-comp-conversation">
      <div className="sh-conv-header">
        <StatusDot state={{ status: state.status }} />
        <div className="sh-conv-title">{state.title}</div>
      </div>
      <div className="sh-conv-intent">{state.intent}</div>
      <div className="sh-conv-meta">
        <span>{state.participants?.length ?? 0} participant(s)</span>
        <span>·</span>
        <span>{state.objectCount} object(s)</span>
      </div>
    </div>
  );
}

// ── Layout Component ──────────────────────────────────────────

export function Panel({ id, name, children, loading, error }: { id: string; name: string; children?: ReactNode; loading?: boolean; error?: string }) {
  if (error) return <div className="sh-comp-panel sh-comp-error" data-panel={id}>{error}</div>;
  return (
    <div className={`sh-comp-panel ${loading ? 'sh-panel-loading' : ''}`} data-panel={id}>
      <div className="sh-panel-header">{name}</div>
      <div className="sh-panel-body">{loading ? <div className="sh-comp-skeleton" aria-busy="true"><div className="sh-skel-line w-full" /><div className="sh-skel-line w-3/4" /></div> : children}</div>
    </div>
  );
}

// ── Component Styles ──────────────────────────────────────────

const styles = `
.sh-comp-metric { padding: var(--shunya-spacing-md); }
.sh-metric-value { font-size: var(--shunya-font-size-2xl); font-weight: 600; line-height: 1.2; }
.sh-metric-trend { font-size: var(--shunya-font-size-sm); margin-top: 2px; }
.sh-trend-up { color: var(--shunya-color-success); }
.sh-trend-down { color: var(--shunya-color-danger); }
.sh-trend-flat { color: var(--shunya-text-secondary); }
.sh-metric-subtitle { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); margin-top: 4px; }
.sh-comp-badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.sh-badge-success { background: #D8EDE3; color: #2D6A4F; }
.sh-badge-warning { background: #FDF0D6; color: #8B5E1A; }
.sh-badge-danger { background: #F5D6D7; color: #9B2226; }
.sh-badge-neutral { background: #F1F5F9; color: #475569; }
.sh-badge-info { background: #DBE8FD; color: #1D4ED8; }
.sh-comp-status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
.sh-status-active, .sh-status-completed { background: var(--shunya-color-success); }
.sh-status-at_risk, .sh-status-waiting { background: var(--shunya-color-warning); }
.sh-status-blocked, .sh-status-danger { background: var(--shunya-color-danger); }
.sh-status-draft, .sh-status-created, .sh-status-archived { background: var(--shunya-text-secondary); }
.sh-comp-identity { display: flex; align-items: center; gap: var(--shunya-spacing-sm); }
.sh-identity-name { font-size: var(--shunya-font-size-lg); font-weight: 500; }
.sh-identity-type { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); text-transform: uppercase; }
.sh-identity-id { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); font-family: monospace; }
.sh-comp-timeline-event { display: flex; gap: var(--shunya-spacing-sm); padding: var(--shunya-spacing-xs) 0; }
.sh-event-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--shunya-text-secondary); margin-top: 6px; flex-shrink: 0; }
.sh-timeline-impact-positive .sh-event-dot { background: var(--shunya-color-success); }
.sh-timeline-impact-negative .sh-event-dot { background: var(--shunya-color-danger); }
.sh-timeline-impact-critical .sh-event-dot { background: var(--shunya-color-danger); box-shadow: 0 0 0 3px rgba(155,34,38,0.3); }
.sh-event-title { font-size: var(--shunya-font-size-sm); font-weight: 500; }
.sh-event-desc { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); }
.sh-event-meta { font-size: 10px; color: var(--shunya-text-secondary); margin-top: 2px; }
.sh-comp-insight { padding: var(--shunya-spacing-sm); border-left: 3px solid var(--shunya-color-ai); }
.sh-insight-header { display: flex; gap: var(--shunya-spacing-sm); align-items: center; margin-bottom: 4px; }
.sh-insight-type { font-size: 10px; text-transform: uppercase; color: var(--shunya-text-secondary); }
.sh-insight-title { font-size: var(--shunya-font-size-sm); font-weight: 500; }
.sh-insight-body { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); margin-top: 2px; }
.sh-comp-progress { display: flex; align-items: center; gap: var(--shunya-spacing-sm); }
.sh-progress-track { flex: 1; height: 8px; background: var(--shunya-surface-2); border-radius: 4px; overflow: hidden; }
.sh-progress-fill { height: 100%; border-radius: 4px; transition: width 0.3s ease; }
.sh-progress-label { font-size: var(--shunya-font-size-sm); font-weight: 500; min-width: 36px; text-align: right; }
.sh-comp-confidence { text-align: center; }
.sh-confidence-value { font-size: var(--shunya-font-size-3xl); font-weight: 700; }
.sh-confidence-track { height: 6px; background: var(--shunya-surface-2); border-radius: 3px; margin: 4px 0; overflow: hidden; }
.sh-confidence-fill { height: 100%; border-radius: 3px; transition: width 0.3s ease; }
.sh-confidence-factors { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; justify-content: center; }
.sh-confidence-factor { font-size: 10px; color: var(--shunya-text-secondary); background: var(--shunya-surface-1); padding: 1px 4px; border-radius: 2px; }
.sh-comp-blockers { display: flex; flex-direction: column; gap: 4px; }
.sh-blockers-none { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); font-style: italic; }
.sh-blocker { display: flex; align-items: center; gap: 6px; font-size: var(--shunya-font-size-sm); padding: 2px 0; }
.sh-blocker-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.sh-blocker-high .sh-blocker-dot { background: var(--shunya-color-danger); }
.sh-blocker-medium .sh-blocker-dot { background: var(--shunya-color-warning); }
.sh-blocker-low .sh-blocker-dot { background: var(--shunya-color-info); }
.sh-comp-next-action { padding: var(--shunya-spacing-sm); border: 1px solid var(--shunya-color-secondary); border-radius: var(--shunya-radius-md); }
.sh-next-action-title { font-size: var(--shunya-font-size-sm); font-weight: 500; }
.sh-next-action-reason { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); margin: 2px 0; }
.sh-comp-conversation { padding: var(--shunya-spacing-sm); border: 1px solid var(--shunya-surface-2); border-radius: var(--shunya-radius-md); }
.sh-conv-header { display: flex; align-items: center; gap: var(--shunya-spacing-sm); }
.sh-conv-title { font-size: var(--shunya-font-size-sm); font-weight: 500; }
.sh-conv-intent { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); margin: 2px 0; }
.sh-conv-meta { font-size: 10px; color: var(--shunya-text-secondary); display: flex; gap: 4px; }
.sh-comp-panel { display: flex; flex-direction: column; padding: var(--shunya-spacing-md); }
.sh-panel-header { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: var(--shunya-spacing-sm); }
.sh-panel-body { flex: 1; }
.sh-comp-skeleton { display: flex; flex-direction: column; gap: 8px; }
.sh-skel-line { height: 12px; background: linear-gradient(90deg, var(--shunya-surface-2) 25%, var(--shunya-surface-1) 50%, var(--shunya-surface-2) 75%); background-size: 200% 100%; animation: sh-shimmer 1.5s infinite; border-radius: 4px; }
.w-16 { width: 64px; }
.w-20 { width: 80px; }
.w-24 { width: 96px; }
.w-40 { width: 160px; }
.w-3\\/4 { width: 75%; }
.w-full { width: 100%; }
@keyframes sh-shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.sh-comp-error { color: var(--shunya-color-danger); font-size: var(--shunya-font-size-sm); padding: var(--shunya-spacing-sm); }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  document.head.appendChild(el);
}