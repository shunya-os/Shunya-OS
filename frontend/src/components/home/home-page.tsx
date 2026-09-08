/**
 * SHUNYA Home — the authenticated landing surface.
 *
 * Four truthful sections, all backed by the execution API:
 *   SHUNYA NOW        — live work in progress (GET /execution/tasks/active)
 *   RECENTLY COMPLETED— finished work (GET /execution/tasks)
 *   NEEDS YOUR ATTENTION — items requiring a human (GET /execution/tasks/attention)
 *   SHUNYA CAN HELP   — contextual capabilities (opens real workspaces)
 *
 * Every row is clickable → opens the TaskDetail panel. The pulse indicator is
 * truthful: it reflects real connectivity and workload, never fake progress.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useHomeStore } from '../../runtimes/home-store';
import { useWorkspaceStore } from '../../runtimes/workspace/store';
import { SessionManager } from '../../api/session';
import type { TaskLifecycle } from '../../api/execution-api';
import { TaskDetail } from './task-detail';

// ── Helpers ────────────────────────────────────────────────────────────

function _timeAgo(ts?: string | null): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    if (isNaN(d.getTime())) return '';
    const diff = Date.now() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch { return ''; }
}

/** Active-phase label used in SHUNYA NOW rows. */
const PHASE_LABELS: Record<string, string> = {
  pending: 'Pending',
  queued: 'Queued',
  in_progress: 'Working',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
  blocked: 'Needs your input',
  interpreting: 'Understanding your request',
  context_loading: 'Loading context',
  company_data: 'Checking company data',
  internet_data: 'Checking internet information',
  analysing: 'Analysing information',
  planning: 'Forming a plan',
  processing: 'Processing',
  executing: 'Executing',
  verifying: 'Verifying result',
  completing: 'Completing',
};

function humanPhase(raw?: string | null): string {
  if (!raw) return '';
  const key = raw.toLowerCase();
  if (PHASE_LABELS[key]) return PHASE_LABELS[key];
  return raw.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function phaseLabel(t: TaskLifecycle): string {
  if (t.current_phase) return humanPhase(t.current_phase);
  return t.status === 'in_progress' ? 'Working' : humanPhase(t.status);
}

function statusTone(t: TaskLifecycle): 'active' | 'done' | 'attention' {
  if (t.status === 'in_progress' || t.status === 'pending' || t.status === 'queued') return 'active';
  if (t.status === 'completed' || t.outcome === 'completed') return 'done';
  return 'attention';
}

// ── Pulse Indicator — truthful heartbeat ───────────────────────────────
// Green: observed & idle. Teal: working. Gold: needs attention. Red: offline.

type PulseMode = 'observing' | 'working' | 'attentive' | 'offline';

function PulseIndicator({ mode, lastUpdated }: { mode: PulseMode; lastUpdated: number | null }) {
  const label = mode === 'observing' ? 'Observing'
    : mode === 'working' ? 'Working'
    : mode === 'attentive' ? 'Needs attention'
    : 'Reconnecting';

  const color = mode === 'observing' ? 'var(--shunya-success, #6a9f6a)'
    : mode === 'working' ? 'var(--shunya-info, #4a9e9e)'
    : mode === 'attentive' ? 'var(--shunya-gold, #a4865f)'
    : '#c0392b';

  return (
    <div className="hp-pulse" title={lastUpdated ? `Updated ${_timeAgo(new Date(lastUpdated).toISOString())}` : 'Waiting for first update'}>
      <motion.span
        className="hp-pulse-dot"
        style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
        animate={mode === 'offline' ? { opacity: [0.4, 0.7, 0.4] } : { opacity: [0.45, 1, 0.45], scale: [1, 1.15, 1] }}
        transition={{ duration: mode === 'offline' ? 2.5 : 2.2, repeat: Infinity, ease: 'easeInOut' }}
      />
      <span className="hp-pulse-label">{label}</span>
    </div>
  );
}

// ── Task Row ───────────────────────────────────────────────────────────

function TaskRow({ task, onOpen }: { task: TaskLifecycle; onOpen: (t: TaskLifecycle) => void }) {
  const tone = statusTone(task);
  const icon = tone === 'active' ? '⟳' : tone === 'done' ? '✓' : '⚠';
  const iconClass = tone === 'active' ? 'hp-row-icon-active'
    : tone === 'done' ? 'hp-row-icon-done' : 'hp-row-icon-attention';

  return (
    <motion.button
      className="hp-task-row"
      onClick={() => onOpen(task)}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ backgroundColor: 'rgba(26,28,29,0.03)' }}
    >
      <span className={`hp-row-icon ${iconClass}`}>{icon}</span>
      <span className="hp-row-body">
        <span className="hp-row-title">{task.title}</span>
        <span className="hp-row-sub">
          {phaseLabel(task)}
          {task.completed_at ? ` · completed ${_timeAgo(task.completed_at)}` : task.started_at ? ` · started ${_timeAgo(task.started_at)}` : ''}
        </span>
      </span>
      <span className="hp-row-arrow">→</span>
    </motion.button>
  );
}

// ── Section Shell ──────────────────────────────────────────────────────

function HomeSection({ title, hint, children, count }: {
  title: string;
  hint?: string;
  count?: number;
  children: React.ReactNode;
}) {
  return (
    <section className="hp-section">
      <div className="hp-section-header">
        <h2 className="hp-section-title">{title}</h2>
        {hint && <span className="hp-section-hint">{hint}</span>}
        {typeof count === 'number' && count > 0 && <span className="hp-section-count">{count}</span>}
      </div>
      <div className="hp-section-body">{children}</div>
    </section>
  );
}

function EmptyState({ message }: { message: string }) {
  return <p className="hp-empty">{message}</p>;
}

// ── SHUNYA CAN HELP — contextual capabilities ──────────────────────────
// These are real navigation affordances — each opens an actual workspace.

interface Capability {
  label: string;
  description: string;
  open: () => void;
}

function buildCapabilities(hasActive: boolean, hasAttention: boolean, hasCompleted: boolean): Capability[] {
  const openDomain = (label: string, objectId: string) => () => {
    useWorkspaceStore.getState().open(label, 'object', { objectType: objectId, objectId });
  };
  const caps: Capability[] = [];
  if (hasActive) {
    caps.push({ label: 'Follow live work', description: 'Open the Work area and watch executions as they progress.', open: openDomain('Work', 'work') });
  }
  if (hasAttention) {
    caps.push({ label: 'Resolve what needs you', description: 'Review blocked and failed tasks that require your input.', open: openDomain('Tasks', 'tasks') });
  }
  if (hasCompleted) {
    caps.push({ label: 'Review completed work', description: 'Browse finished tasks, results, and outputs.', open: openDomain('Outputs', 'outputs') });
  }
  caps.push({ label: 'Ask SHUNYA anything', description: 'Direct SHUNYA to investigate, draft, or execute.', open: () => useWorkspaceStore.getState().open('Ask SHUNYA', 'home') });
  caps.push({ label: 'Explore your organization', description: 'People, finance, sales, marketing, knowledge — everything is one click away.', open: () => useWorkspaceStore.getState().open('Organization', 'object', { objectType: 'people', objectId: 'people' }) });
  return caps.slice(0, 4);
}

// ── Main Component ─────────────────────────────────────────────────────

export function HomePage() {
  const {
    activeTasks, completedTasks, attentionTasks,
    isLoading, error, lastUpdated, startPolling, refreshActive,
  } = useHomeStore();
  const [selected, setSelected] = useState<TaskLifecycle | null>(null);

  // Live polling — active every 5s, lists every 30s (store-owned timers)
  useEffect(() => {
    const stop = startPolling();
    return stop;
  }, [startPolling]);

  const session = SessionManager.load();
  const name = session?.name || session?.email?.split('@')[0] || '';

  const pulseMode: PulseMode = error ? 'offline'
    : attentionTasks.length > 0 ? 'attentive'
    : activeTasks.length > 0 ? 'working'
    : 'observing';

  const capabilities = buildCapabilities(
    activeTasks.length > 0,
    attentionTasks.length > 0,
    completedTasks.length > 0,
  );

  const handleOpenDetail = useCallback((t: TaskLifecycle) => setSelected(t), []);
  const handleCloseDetail = useCallback(() => setSelected(null), []);

  // Show at most 5 rows per section — calm, not overwhelming
  const visibleActive = activeTasks.slice(0, 5);
  const visibleRecent = completedTasks.slice(0, 5);
  const visibleAttention = attentionTasks.slice(0, 5);

  return (
    <motion.div
      className="hp-home"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div className="hp-wrap">
        {/* ── Header ─────────────────────────────────────────── */}
        <header className="hp-header">
          <div className="hp-brand">
            <span className="hp-brand-zero">शून्य</span>
            <span className="hp-brand-label">SHUNYA</span>
          </div>
          <div className="hp-header-right">
            {name && <span className="hp-hello">{name}</span>}
            <PulseIndicator mode={pulseMode} lastUpdated={lastUpdated} />
          </div>
        </header>

        {/* ── Greeting line ──────────────────────────────────── */}
        <div className="hp-greeting">
          <h1 className="hp-greeting-title">
            {activeTasks.length > 0
              ? `SHUNYA is working on ${activeTasks.length} thing${activeTasks.length > 1 ? 's' : ''} right now.`
              : attentionTasks.length > 0
              ? 'A few things need you.'
              : 'Everything is calm.'}
          </h1>
          {completedTasks.length > 0 && (
            <p className="hp-greeting-sub">
              {completedTasks.length} completed since your last visit.
            </p>
          )}
        </div>

        {/* Offline / error banner — truthful, retryable */}
        <AnimatePresence>
          {error && (
            <motion.div
              className="hp-error-banner"
              role="alert"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <span className="hp-error-icon">●</span>
              <span className="hp-error-text">{error}</span>
              <button className="hp-retry" onClick={() => { useHomeStore.getState().clearError(); useHomeStore.getState().loadAll(); }}>
                Retry
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── SHUNYA NOW ─────────────────────────────────────── */}
        <HomeSection
          title="SHUNYA NOW"
          hint="Live work being performed"
          count={activeTasks.length}
        >
          {isLoading && activeTasks.length === 0 ? (
            <EmptyState message="Checking for live work…" />
          ) : visibleActive.length > 0 ? (
            <div className="hp-task-list">
              <AnimatePresence mode="popLayout">
                {visibleActive.map((t) => (
                  <TaskRow key={t.task_id} task={t} onOpen={handleOpenDetail} />
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <EmptyState message="Nothing in motion right now — SHUNYA is observing your organization." />
          )}
        </HomeSection>

        {/* ── NEEDS YOUR ATTENTION ───────────────────────────── */}
        <HomeSection
          title="NEEDS YOUR ATTENTION"
          hint="Human input required"
          count={attentionTasks.length}
        >
          {visibleAttention.length > 0 ? (
            <div className="hp-task-list">
              <AnimatePresence mode="popLayout">
                {visibleAttention.map((t) => (
                  <TaskRow key={t.task_id} task={t} onOpen={handleOpenDetail} />
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <EmptyState message="Nothing needs you. SHUNYA is handling what it can." />
          )}
        </HomeSection>

        {/* ── RECENTLY COMPLETED ─────────────────────────────── */}
        <HomeSection
          title="RECENTLY COMPLETED"
          hint="Finished work"
          count={completedTasks.length}
        >
          {visibleRecent.length > 0 ? (
            <div className="hp-task-list hp-task-list-done">
              <AnimatePresence mode="popLayout">
                {visibleRecent.map((t) => (
                  <TaskRow key={t.task_id} task={t} onOpen={handleOpenDetail} />
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <EmptyState message="No completed work yet. When SHUNYA finishes something, it will appear here." />
          )}
        </HomeSection>

        {/* ── SHUNYA CAN HELP ────────────────────────────────── */}
        <HomeSection title="SHUNYA CAN HELP" hint="Contextual capabilities">
          <div className="hp-caps">
            {capabilities.map((cap, i) => (
              <motion.button
                key={cap.label}
                className="hp-cap"
                onClick={cap.open}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                whileHover={{ y: -2 }}
              >
                <span className="hp-cap-label">{cap.label}</span>
                <span className="hp-cap-desc">{cap.description}</span>
              </motion.button>
            ))}
          </div>
        </HomeSection>

        <footer className="hp-footer">
          <button className="hp-footer-btn" onClick={() => refreshActive()} title="Refresh now">
            Refresh
          </button>
          {lastUpdated && <span className="hp-footer-updated">Live · updated {_timeAgo(new Date(lastUpdated).toISOString())}</span>}
        </footer>
      </div>

      {/* ── Task Detail overlay ──────────────────────────────── */}
      <AnimatePresence>
        {selected && (
          <TaskDetail task={selected} onClose={handleCloseDetail} />
        )}
      </AnimatePresence>

      <style>{homeStyles}</style>
    </motion.div>
  );
}

// ── Styles — calm whitespace, restrained controls ──────────────────────

const homeStyles = `
/* ── Root ─────────────────────────────────────────────────── */
.hp-home {
  min-height: 100vh;
  background: var(--shunya-bg, #FBF8F5);
  color: var(--shunya-text, #1A1C1D);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
}
.hp-wrap {
  max-width: 760px;
  margin: 0 auto;
  padding: 64px 40px 96px;
  display: flex;
  flex-direction: column;
  gap: 44px;
}

/* ── Header ───────────────────────────────────────────────── */
.hp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hp-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.hp-brand-zero {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 22px;
  font-weight: 400;
  letter-spacing: 0.06em;
  color: var(--shunya-text, #1A1C1D);
}
.hp-brand-label {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--shunya-text, #1A1C1D);
}
.hp-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.hp-hello {
  font-size: 13px;
  color: rgba(26,28,29,0.5);
}

/* ── Pulse ────────────────────────────────────────────────── */
.hp-pulse {
  display: flex;
  align-items: center;
  gap: 8px;
}
.hp-pulse-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.hp-pulse-label {
  font-size: 12px;
  color: rgba(26,28,29,0.55);
  letter-spacing: 0.02em;
}

/* ── Greeting ─────────────────────────────────────────────── */
.hp-greeting {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.hp-greeting-title {
  font-size: clamp(1.4rem, 3vw, 1.9rem);
  font-weight: 400;
  line-height: 1.25;
  margin: 0;
  color: var(--shunya-text, #1A1C1D);
  letter-spacing: -0.01em;
}
.hp-greeting-sub {
  font-size: 14px;
  color: rgba(26,28,29,0.55);
  margin: 0;
}

/* ── Error banner ─────────────────────────────────────────── */
.hp-error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 8px;
  background: rgba(192,57,43,0.05);
  border: 1px solid rgba(192,57,43,0.15);
  overflow: hidden;
}
.hp-error-icon {
  color: #c0392b;
  font-size: 10px;
  animation: hp-blink 1.2s infinite;
}
.hp-error-text {
  flex: 1;
  font-size: 13px;
  color: #b03a2e;
}
.hp-retry {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid rgba(192,57,43,0.25);
  background: transparent;
  color: #b03a2e;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}
.hp-retry:hover { background: rgba(192,57,43,0.08); }
@keyframes hp-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ── Sections ─────────────────────────────────────────────── */
.hp-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.hp-section-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.hp-section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(26,28,29,0.45);
  margin: 0;
}
.hp-section-hint {
  font-size: 12px;
  color: rgba(26,28,29,0.3);
}
.hp-section-count {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 10px;
  background: rgba(26,28,29,0.05);
  color: rgba(26,28,29,0.5);
}
.hp-section-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* ── Task list & rows ─────────────────────────────────────── */
.hp-task-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.hp-task-row {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: 10px;
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.06));
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: border-color 0.15s;
}
.hp-task-row:hover {
  border-color: var(--shunya-gold, #a4865f);
}
.hp-row-icon {
  width: 24px;
  font-size: 13px;
  text-align: center;
  flex-shrink: 0;
}
.hp-row-icon-active {
  color: var(--shunya-info, #4a9e9e);
  animation: hp-spin 2.4s linear infinite;
  display: inline-block;
}
.hp-row-icon-done { color: var(--shunya-success, #6a9f6a); }
.hp-row-icon-attention { color: var(--shunya-gold, #a4865f); }
@keyframes hp-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.hp-row-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.hp-row-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.hp-row-sub {
  font-size: 12px;
  color: rgba(26,28,29,0.45);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.hp-row-arrow {
  font-size: 14px;
  color: rgba(26,28,29,0.25);
  flex-shrink: 0;
  transition: transform 0.15s;
}
.hp-task-row:hover .hp-row-arrow {
  transform: translateX(3px);
  color: var(--shunya-gold, #a4865f);
}

/* ── Empty states ─────────────────────────────────────────── */
.hp-empty {
  font-size: 13px;
  color: rgba(26,28,29,0.4);
  font-style: italic;
  padding: 10px 14px;
  margin: 0;
}

/* ── Capabilities ─────────────────────────────────────────── */
.hp-caps {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.hp-cap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 18px 20px;
  border-radius: 12px;
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.06));
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: border-color 0.15s;
}
.hp-cap:hover {
  border-color: var(--shunya-gold, #a4865f);
}
.hp-cap-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
}
.hp-cap-desc {
  font-size: 12px;
  color: rgba(26,28,29,0.5);
  line-height: 1.45;
}

/* ── Footer ───────────────────────────────────────────────── */
.hp-footer {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-top: 8px;
  border-top: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.hp-footer-btn {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.12));
  background: transparent;
  color: rgba(26,28,29,0.6);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s;
}
.hp-footer-btn:hover {
  border-color: var(--shunya-gold, #a4865f);
  color: var(--shunya-text, #1A1C1D);
}
.hp-footer-updated {
  font-size: 12px;
  color: rgba(26,28,29,0.35);
}

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 640px) {
  .hp-wrap { padding: 40px 20px 72px; gap: 36px; }
  .hp-caps { grid-template-columns: 1fr; }
  .hp-hello { display: none; }
  .hp-greeting-title { font-size: 1.3rem; }
}
`;