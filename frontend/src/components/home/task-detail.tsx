/**
 * Task Detail — Full lifecycle view for a single task or execution run.
 *
 * Shows what SHUNYA understood, what it did, what sources it used, the result
 * and outcome, and provides a next-action button that navigates somewhere real.
 *
 * All data is from the backend — never fabricated phases, timers, or progress.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { fetchTaskDetail, type TaskLifecycle, type TaskDetail } from '../../api/execution-api';
import { useWorkspaceStore } from '../../runtimes/workspace/store';

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

function _formatDuration(seconds?: number | null): string {
  if (!seconds || seconds <= 0) return '';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (mins < 60) return `${mins}m ${secs}s`;
  const hours = Math.floor(mins / 60);
  const remMins = mins % 60;
  return `${hours}h ${remMins}m`;
}

function _formatTimestamp(ts?: string | null): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
}

/** Chips for source-of-truth indicators. */
function SourceChip({ label, active }: { label: string; active?: boolean | null }) {
  return (
    <span className={`td-source-chip ${active ? 'td-source-active' : 'td-source-inactive'}`}>
      {active ? '✓' : '○'} {label}
    </span>
  );
}

/**
 * Natural-language mapping for execution statuses and phases.
 * Living Experience Constitution §6: technical terminology shall never
 * leak into the user experience.
 */
const STATUS_LABELS: Record<string, string> = {
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

function humanLabel(raw: string | null | undefined, fallback = ''): string {
  if (!raw) return fallback;
  const key = raw.toLowerCase();
  if (STATUS_LABELS[key]) return STATUS_LABELS[key];
  // snake_case → Title Case
  return raw
    .split('_')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

/** Phase timeline item. */
function PhaseRow({ phase, started_at, duration, isCurrent }: {
  phase: string;
  started_at?: string | null;
  duration?: number | null;
  isCurrent?: boolean;
}) {
  return (
    <div className={`td-phase-row ${isCurrent ? 'td-phase-current' : ''}`}>
      <div className="td-phase-marker">
        <div className={`td-phase-dot ${isCurrent ? 'td-phase-dot-active' : ''}`} />
        {!isCurrent && <div className="td-phase-line" />}
      </div>
      <div className="td-phase-body">
        <span className="td-phase-name">{humanLabel(phase)}</span>
        <span className="td-phase-meta">
          {started_at ? _formatTimestamp(started_at) : ''}
          {duration && duration > 0 ? ` · ${_formatDuration(duration)}` : ''}
        </span>
      </div>
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────

interface TaskDetailProps {
  task: TaskLifecycle;
  onClose: () => void;
}

export function TaskDetail({ task, onClose }: TaskDetailProps) {
  const [detail, setDetail] = useState<TaskDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const run = detail?.run;
  const transitions = detail?.transitions;

  // ── Fetch run detail on mount ──────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const id = task.execution_run_id || task.task_id;
    fetchTaskDetail(id).then((res) => {
      if (cancelled) return;
      if (res.success && res.data) {
        setDetail(res.data);
      } else {
        setError(res.error || 'Could not load full detail.');
      }
      setLoading(false);
    }).catch(() => {
      if (!cancelled) { setError('Could not load detail.'); setLoading(false); }
    });

    return () => { cancelled = true; };
  }, [task.execution_run_id, task.task_id]);

  // ── Next action ────────────────────────────────────────────────────────
  const handleNextAction = useCallback(() => {
    const url = task.next_action_url;
    if (url) {
      // Internal workspace navigation
      if (url.startsWith('/workspace/')) {
        const match = url.match(/^\/workspace\/([^/]+)/);
        if (match) {
          const id = match[1];
          useWorkspaceStore.getState().open(
            id.charAt(0).toUpperCase() + id.slice(1),
            'object',
            { objectType: id, objectId: id },
          );
          return;
        }
      }
      // Fallback: navigate
      window.location.href = url;
      return;
    }
    // No URL — open the Work area as a fallback
    useWorkspaceStore.getState().open('Work', 'object', { objectType: 'work', objectId: 'work' });
    onClose();
  }, [task, onClose]);

  // ── Status colour ──────────────────────────────────────────────────────
  const statusColor = task.status === 'completed' || task.outcome === 'completed'
    ? 'var(--shunya-success, #6a9f6a)'
    : task.status === 'failed' || task.outcome === 'failed'
    ? '#c0392b'
    : task.status === 'blocked'
    ? 'var(--shunya-gold, #a4865f)'
    : 'var(--shunya-info, #4a9e9e)';

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <motion.div
      className="td-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <motion.div
        className="td-panel"
        initial={{ x: 320, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 320, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        {/* ── Header ──────────────────────────────────────────── */}
        <div className="td-header">
          <div className="td-header-left">
            <div className="td-status-badge" style={{ backgroundColor: statusColor }} />
            <span className="td-status-label">{humanLabel(task.status)}</span>
          </div>
          <button className="td-close" onClick={onClose} aria-label="Close detail">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <line x1="3" y1="3" x2="13" y2="13" />
              <line x1="13" y1="3" x2="3" y2="13" />
            </svg>
          </button>
        </div>

        {/* ── Title ────────────────────────────────────────────── */}
        <h2 className="td-title">{task.title || 'Untitled'}</h2>
        {task.description && <p className="td-desc">{task.description}</p>}

        {task.current_phase && (
          <p className="td-phase-current-label">
            Current phase: <strong>{humanLabel(task.current_phase)}</strong>
          </p>
        )}

        {/* ── Loading state ────────────────────────────────────── */}
        {loading && (
          <div className="td-loading">
            <div className="td-loading-shimmer" />
            <p>Loading full detail…</p>
          </div>
        )}

        {error && !loading && (
          <div className="td-error-banner" role="alert">
            <span className="td-error-icon">⚠</span> {error}
          </div>
        )}

        {/* ── What SHUNYA understood ───────────────────────────── */}
        <div className="td-section">
          <h3 className="td-section-title">What SHUNYA understood</h3>
          <p className="td-section-body">
            {run?.intent || task.description || task.title}
          </p>
        </div>

        {/* ── What SHUNYA did — Phase Timeline ─────────────────── */}
        <div className="td-section">
          <h3 className="td-section-title">What SHUNYA did</h3>
          {task.phase_history && task.phase_history.length > 0 ? (
            <div className="td-phases">
              {task.phase_history.map((p, i) => (
                <PhaseRow
                  key={`${p.phase}-${i}`}
                  phase={p.phase}
                  started_at={p.started_at}
                  duration={p.duration}
                  isCurrent={i === task.phase_history!.length - 1 && task.status === 'in_progress'}
                />
              ))}
            </div>
          ) : transitions && transitions.length > 0 ? (
            <div className="td-phases">
              {transitions.map((t, i) => (
                <PhaseRow
                  key={`t-${t.id ?? i}`}
                  phase={`${humanLabel(t.state_before)} → ${humanLabel(t.state_after)}`}
                  started_at={t.transitioned_at}
                  duration={0}
                  isCurrent={i === transitions.length - 1 && task.status === 'in_progress'}
                />
              ))}
            </div>
          ) : (
            <p className="td-empty-hint">No phase data recorded yet.</p>
          )}
        </div>

        {/* ── Sources used ─────────────────────────────────────── */}
        <div className="td-section">
          <h3 className="td-section-title">Sources used</h3>
          <div className="td-sources">
            <SourceChip label="Company data" active={run?.used_company_data} />
            <SourceChip label="Internet" active={run?.used_internet_data} />
            <SourceChip label="AI" active={run?.used_ai} />
          </div>
        </div>

        {/* ── Result & Outcome ─────────────────────────────────── */}
        <div className="td-section">
          <h3 className="td-section-title">Result & Outcome</h3>
          {task.outcome ? (
            <p className="td-outcome">
              Outcome: <strong>{humanLabel(task.outcome)}</strong>
            </p>
          ) : null}
          {task.result_summary ? (
            <p className="td-section-body">{task.result_summary}</p>
          ) : run?.result_summary ? (
            <p className="td-section-body">{run.result_summary}</p>
          ) : task.status === 'completed' ? (
            <p className="td-empty-hint">Completed without a summary record.</p>
          ) : task.status === 'failed' ? (
            <p className="td-error-text">{run?.error || task.description || 'Unknown error.'}</p>
          ) : (
            <p className="td-empty-hint">SHUNYA is still working on this.</p>
          )}
        </div>

        {/* ── Duration ─────────────────────────────────────────── */}
        <div className="td-section td-section-row">
          <div className="td-metric">
            <span className="td-metric-label">Duration</span>
            <span className="td-metric-value">
              {_formatDuration(task.duration_seconds || run?.duration_seconds) || 'In progress'}
            </span>
          </div>
          <div className="td-metric">
            <span className="td-metric-label">Started</span>
            <span className="td-metric-value">{_timeAgo(task.started_at || run?.started_at) || '—'}</span>
          </div>
          {task.completed_at && (
            <div className="td-metric">
              <span className="td-metric-label">Completed</span>
              <span className="td-metric-value">{_timeAgo(task.completed_at)}</span>
            </div>
          )}
        </div>

        {/* ── Next Action ──────────────────────────────────────── */}
        <div className="td-actions">
          {task.next_action ? (
            <button className="td-next-btn" onClick={handleNextAction}>
              {task.next_action} →
            </button>
          ) : task.status === 'completed' || task.status === 'failed' ? (
            <button className="td-next-btn td-next-btn-secondary" onClick={handleNextAction}>
              View in Work area →
            </button>
          ) : (
            <button className="td-next-btn td-next-btn-secondary" onClick={handleNextAction}>
              Open Work area →
            </button>
          )}
        </div>

        <style>{detailStyles}</style>
      </motion.div>
    </motion.div>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────

const detailStyles = `
/* ── Overlay ───────────────────────────────────────────────── */
.td-overlay {
  position: fixed; inset: 0;
  z-index: 50;
  display: flex;
  justify-content: flex-end;
  background: rgba(26,28,29,0.15);
  backdrop-filter: blur(2px);
}
.td-panel {
  width: 480px;
  max-width: 100vw;
  height: 100vh;
  overflow-y: auto;
  background: var(--shunya-bg, #FBF8F5);
  border-left: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  padding: 32px 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  color: var(--shunya-text, #1A1C1D);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
}

/* ── Header ────────────────────────────────────────────────── */
.td-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.td-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.td-status-badge {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.td-status-label {
  font-size: 11px; font-weight: 500; text-transform: uppercase;
  letter-spacing: 0.05em; color: rgba(26,28,29,0.5);
}
.td-close {
  background: none; border: none; cursor: pointer;
  color: rgba(26,28,29,0.35); padding: 4px; border-radius: 4px;
  transition: color 0.15s;
}
.td-close:hover { color: var(--shunya-text, #1A1C1D); }

/* ── Title ─────────────────────────────────────────────────── */
.td-title {
  font-size: 20px; font-weight: 500; line-height: 1.3; margin: 0;
  color: var(--shunya-text, #1A1C1D);
}
.td-desc {
  font-size: 14px; color: rgba(26,28,29,0.6); margin: 0; line-height: 1.5;
}
.td-phase-current-label {
  font-size: 13px; color: rgba(26,28,29,0.55); margin: 0;
}

/* ── Loading ───────────────────────────────────────────────── */
.td-loading {
  display: flex; flex-direction: column; align-items: center;
  gap: 12px; padding: 24px; color: rgba(26,28,29,0.45);
  font-size: 13px;
}
.td-loading-shimmer {
  width: 40px; height: 4px; border-radius: 2px;
  background: linear-gradient(90deg, var(--shunya-border, rgba(26,28,29,0.07)) 0%, var(--shunya-gold, #a4865f) 50%, var(--shunya-border, rgba(26,28,29,0.07)) 100%);
  background-size: 200% 100%;
  animation: td-shimmer 1.2s infinite;
}
@keyframes td-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Error ─────────────────────────────────────────────────── */
.td-error-banner {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; border-radius: 8px;
  background: rgba(192,57,43,0.06); border: 1px solid rgba(192,57,43,0.15);
  font-size: 13px; color: #c0392b;
}
.td-error-icon { font-size: 14px; }

/* ── Sections ──────────────────────────────────────────────── */
.td-section {
  display: flex; flex-direction: column; gap: 8px;
}
.td-section-title {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.06em; color: rgba(26,28,29,0.4); margin: 0;
}
.td-section-body {
  font-size: 14px; color: rgba(26,28,29,0.75); margin: 0; line-height: 1.5;
}
.td-empty-hint {
  font-size: 13px; color: rgba(26,28,29,0.4); font-style: italic; margin: 0;
}
.td-error-text {
  font-size: 13px; color: #c0392b; margin: 0;
}

/* ── Phase Timeline ────────────────────────────────────────── */
.td-phases {
  display: flex; flex-direction: column; gap: 0;
}
.td-phase-row {
  display: flex; gap: 12px; padding: 6px 0;
}
.td-phase-marker {
  display: flex; flex-direction: column; align-items: center;
  width: 12px; flex-shrink: 0;
}
.td-phase-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: rgba(26,28,29,0.15); flex-shrink: 0;
}
.td-phase-dot-active {
  background: var(--shunya-gold, #a4865f);
  box-shadow: 0 0 4px var(--shunya-gold, #a4865f);
}
.td-phase-line {
  width: 1px; flex: 1; background: rgba(26,28,29,0.08);
  margin: 2px 0;
}
.td-phase-body {
  display: flex; flex-direction: column; gap: 2px;
}
.td-phase-name {
  font-size: 13px; color: var(--shunya-text, #1A1C1D); line-height: 1.4;
}
.td-phase-meta {
  font-size: 11px; color: rgba(26,28,29,0.35);
}
.td-phase-current .td-phase-name {
  color: var(--shunya-gold, #a4865f);
  font-weight: 500;
}

/* ── Sources ───────────────────────────────────────────────── */
.td-sources {
  display: flex; gap: 8px; flex-wrap: wrap;
}
.td-source-chip {
  font-size: 11px; padding: 3px 10px; border-radius: 12px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  transition: all 0.15s;
}
.td-source-active {
  background: rgba(106,159,106,0.08); border-color: rgba(106,159,106,0.3);
  color: var(--shunya-success, #6a9f6a);
}
.td-source-inactive {
  background: transparent; color: rgba(26,28,29,0.3);
}

/* ── Metrics ───────────────────────────────────────────────── */
.td-section-row {
  flex-direction: row; gap: 24px; flex-wrap: wrap;
}
.td-metric {
  display: flex; flex-direction: column; gap: 2px;
}
.td-metric-label {
  font-size: 11px; color: rgba(26,28,29,0.35);
}
.td-metric-value {
  font-size: 14px; font-weight: 500; color: var(--shunya-text, #1A1C1D);
}
.td-outcome {
  font-size: 14px; color: rgba(26,28,29,0.7); margin: 0;
}

/* ── Next Action ───────────────────────────────────────────── */
.td-actions {
  margin-top: auto; padding-top: 16px;
  border-top: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.td-next-btn {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 500; font-family: inherit;
  padding: 10px 24px; border-radius: 8px;
  border: none; cursor: pointer;
  background: var(--shunya-gold, #a4865f); color: #fff;
  transition: opacity 0.15s;
}
.td-next-btn:hover { opacity: 0.85; }
.td-next-btn-secondary {
  background: transparent; color: var(--shunya-text, #1A1C1D);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.12));
}
.td-next-btn-secondary:hover { border-color: var(--shunya-gold, #a4865f); }
`;