/**
 * Live Execution Panel — Real-time AI action execution visibility.
 *
 * Connects to the canonical event bus to show execution lifecycle:
 *   pending → running → completed | failed
 *
 * Each execution run is displayed as a row with its current phase,
 * status badge, and timing. Completed/failed runs fade to a
 * compact summary after a brief active window.
 *
 * Constitutional basis: Article V §5.5 (typed events),
 * Article II §2.4 (timeline primacy).
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { bus, type RuntimeEvent } from '../../runtimes/event-bus';
import { fetchActiveTasks, fetchRecentTasks, type TaskLifecycle } from '../../api/execution-api';

// ── Types ─────────────────────────────────────────────────────

export interface ExecutionPhase {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt?: string;
  completedAt?: string;
  error?: string;
  /** Child sub-phases for hierarchical execution views. */
  subPhases?: ExecutionPhase[];
}

export interface ExecutionRunState {
  runId: string;
  title: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  currentPhase?: string;
  phases: ExecutionPhase[];
  startedAt?: string;
  completedAt?: string;
  error?: string;
  resultSummary?: string;
}

// ── Event-derived status labels ───────────────────────────────

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  queued: 'Queued',
  in_progress: 'Working',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
  blocked: 'Needs input',
};

const PHASE_LABELS: Record<string, string> = {
  interpreting: 'Understanding request',
  context_loading: 'Loading context',
  company_data: 'Checking company data',
  internet_data: 'Checking internet info',
  analysing: 'Analysing',
  planning: 'Planning',
  processing: 'Processing',
  executing: 'Executing',
  verifying: 'Verifying',
  completing: 'Completing',
};

function humanLabel(raw?: string | null): string {
  if (!raw) return '';
  const key = raw.toLowerCase();
  return PHASE_LABELS[key] || STATUS_LABELS[key] || raw.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

// ── Event-bus to Run-State mapper ─────────────────────────────
// Listens on reality:event, realtime:created, realtime:updated
// and translates them into execution run lifecycle rows.

function statusFromTask(task: TaskLifecycle): ExecutionRunState['status'] {
  if (task.status === 'completed' || task.outcome === 'completed') return 'completed';
  if (task.status === 'failed') return 'failed';
  if (task.status === 'in_progress') return 'running';
  return 'pending';
}

function taskToRun(task: TaskLifecycle): ExecutionRunState {
  return {
    runId: task.task_id || task.execution_run_id || task.task_id,
    title: task.title,
    status: statusFromTask(task),
    currentPhase: humanLabel(task.current_phase || task.status),
    phases: [],
    startedAt: task.started_at || undefined,
    completedAt: task.completed_at || undefined,
    error: undefined,
    resultSummary: task.result_summary || undefined,
  };
}

// ── Main Component ────────────────────────────────────────────

interface Props {
  /** Max runs to show. Default 10. */
  maxRuns?: number;
  /** Show only active (pending + running) runs. Default false. */
  activeOnly?: boolean;
  /** CSS class applied to the outer wrapper. */
  className?: string;
}

export function LiveExecutionPanel({ maxRuns = 10, activeOnly = false, className }: Props) {
  const [runs, setRuns] = useState<ExecutionRunState[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const mountedRef = useRef(true);

  // ── Load initial data from API ──
  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const [activeRes, recentRes] = await Promise.allSettled([
        fetchActiveTasks(),
        activeOnly ? Promise.resolve({ success: true, data: [] }) : fetchRecentTasks(),
      ]);
      const tasks: TaskLifecycle[] = [];
      if (activeRes.status === 'fulfilled' && activeRes.value.success) {
        tasks.push(...(activeRes.value.data || []));
      }
      if (recentRes.status === 'fulfilled' && recentRes.value.success) {
        tasks.push(...(recentRes.value.data || []));
      }
      // Dedupe by task_id/execution_id
      const seen = new Set<string>();
      const deduped: TaskLifecycle[] = [];
      for (const t of tasks) {
        const id = t.task_id || t.execution_run_id;
        if (id && !seen.has(id)) { seen.add(id); deduped.push(t); }
      }
      const mapped = deduped.slice(0, maxRuns).map(taskToRun);
      if (mountedRef.current) setRuns(mapped);
    } catch { /* API unavailable — show nothing */ }
    if (mountedRef.current) setLoading(false);
  }, [maxRuns, activeOnly]);

  useEffect(() => {
    mountedRef.current = true;
    loadTasks();
    return () => { mountedRef.current = false; };
  }, [loadTasks]);

  // ── Subscribe to event bus for live updates ──
  useEffect(() => {
    const handleEvent = (event: RuntimeEvent) => {
      if (event.type === 'reality:event' && event.data) {
        const d = event.data as Record<string, unknown>;
        const taskId = String(d.task_id || d.execution_id || '');
        if (!taskId) return;
        setRuns(prev => {
          const existing = prev.find(r => r.runId === taskId);
          if (existing) {
            return prev.map(r =>
              r.runId === taskId
                ? { ...r, status: (d.status === 'completed' ? 'completed' : d.status === 'failed' ? 'failed' : d.status === 'in_progress' ? 'running' : r.status) as ExecutionRunState['status'], currentPhase: humanLabel(String(d.current_phase || d.status || '')), resultSummary: String(d.result_summary || r.resultSummary || '') }
                : r
            );
          }
          // New run from event
          const newRun: ExecutionRunState = {
            runId: taskId,
            title: String(d.title || d.intent || taskId),
            status: 'running',
            currentPhase: humanLabel(String(d.current_phase || d.status || '')),
            phases: [],
            startedAt: String(d.started_at || new Date().toISOString()),
          };
          return [newRun, ...prev].slice(0, maxRuns);
        });
      }
      if (event.type === 'realtime:created' && event.items) {
        for (const item of event.items) {
          const d = item as Record<string, unknown>;
          if (d.task_id || d.execution_run_id) {
            setRuns(prev => {
              const id = String(d.task_id || d.execution_run_id);
              if (prev.find(r => r.runId === id)) return prev;
              const newRun: ExecutionRunState = { runId: id, title: String(d.title || d.intent || id), status: 'pending', phases: [], startedAt: String(d.started_at) };
              return [newRun, ...prev].slice(0, maxRuns);
            });
          }
        }
      }
    };
    const unsub = bus.onAny(handleEvent);
    return unsub;
  }, [maxRuns]);

  const displayRuns = activeOnly ? runs.filter(r => r.status === 'pending' || r.status === 'running') : runs;

  if (loading) {
    return (
      <div className={`lep-panel ${className || ''}`}>
        <div className="lep-loading">Loading executions…</div>
      </div>
    );
  }

  if (displayRuns.length === 0) {
    return (
      <div className={`lep-panel lep-empty ${className || ''}`}>
        <div className="lep-empty-icon">◈</div>
        <p className="lep-empty-text">No active executions</p>
        <p className="lep-empty-hint">AI actions will appear here as SHUNYA processes them.</p>
      </div>
    );
  }

  return (
    <div className={`lep-panel ${className || ''}`}>
      <div className="lep-header">
        <span className="lep-header-label">
          {activeOnly ? 'Active Executions' : 'Execution History'}
        </span>
        <span className="lep-header-count">{displayRuns.length}</span>
      </div>
      <div className="lep-list">
        {displayRuns.map((run) => (
          <div
            key={run.runId}
            className={`lep-run lep-run-${run.status}`}
            onClick={() => setExpandedRun(expandedRun === run.runId ? null : run.runId)}
          >
            <div className="lep-run-header">
              <span className={`lep-run-dot lep-dot-${run.status}`} />
              <span className="lep-run-title">{run.title}</span>
              <span className={`lep-run-badge lep-badge-${run.status}`}>
                {STATUS_LABELS[run.status] || run.status}
              </span>
            </div>

            {run.currentPhase && (
              <div className="lep-run-phase">{run.currentPhase}</div>
            )}

            {expandedRun === run.runId && (
              <div className="lep-run-detail">
                {run.startedAt && (
                  <div className="lep-run-meta">
                    <span className="lep-meta-label">Started</span>
                    <span className="lep-meta-value">{new Date(run.startedAt).toLocaleString()}</span>
                  </div>
                )}
                {run.completedAt && (
                  <div className="lep-run-meta">
                    <span className="lep-meta-label">Completed</span>
                    <span className="lep-meta-value">{new Date(run.completedAt).toLocaleString()}</span>
                  </div>
                )}
                {run.resultSummary && (
                  <div className="lep-run-result">
                    <span className="lep-meta-label">Result</span>
                    <p className="lep-run-result-text">{run.resultSummary}</p>
                  </div>
                )}
                {run.error && (
                  <div className="lep-run-error" role="alert">
                    <span className="lep-meta-label">Error</span>
                    <p className="lep-run-error-text">{run.error}</p>
                  </div>
                )}
                {run.phases.length > 0 && (
                  <div className="lep-run-phases">
                    <span className="lep-meta-label">Phases</span>
                    {run.phases.map((phase) => (
                      <div key={phase.id} className={`lep-phase lep-phase-${phase.status}`}>
                        <span className={`lep-phase-dot lep-dot-${phase.status}`} />
                        <span className="lep-phase-label">{phase.label}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <style>{`
        .lep-panel {
          width: 100%;
          font-family: var(--shunya-font-body, 'Inter', sans-serif);
        }
        .lep-loading {
          padding: 24px 16px;
          text-align: center;
          font-size: var(--shunya-text-sm, 12px);
          color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
        }
        .lep-empty {
          padding: 32px 16px;
          text-align: center;
        }
        .lep-empty-icon {
          font-size: 24px;
          color: var(--shunya-text-tertiary, rgba(26,28,29,0.15));
          margin-bottom: 8px;
        }
        .lep-empty-text {
          font-size: var(--shunya-text-sm, 12px);
          color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
          font-weight: 500;
        }
        .lep-empty-hint {
          font-size: var(--shunya-text-xs, 10px);
          color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
          margin-top: 4px;
        }
        .lep-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 16px;
          border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
        }
        .lep-header-label {
          font-size: var(--shunya-text-xs, 10px);
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
        }
        .lep-header-count {
          font-size: 10px;
          font-weight: 600;
          color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
          background: var(--shunya-bg, #FBF8F5);
          padding: 2px 6px;
          border-radius: 4px;
        }
        .lep-list {
          max-height: 400px;
          overflow-y: auto;
        }
        .lep-run {
          padding: 10px 16px;
          cursor: pointer;
          border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.04));
          transition: background var(--shunya-duration-fast, 200ms) ease;
        }
        .lep-run:hover {
          background: rgba(26,28,29,0.02);
        }
        .lep-run-header {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .lep-run-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          flex-shrink: 0;
        }
        .lep-dot-pending { background: rgba(26,28,29,0.15); }
        .lep-dot-running { background: #6C4AE2; box-shadow: 0 0 6px rgba(108,74,226,0.4); animation: lep-pulse 1.5s ease-in-out infinite; }
        .lep-dot-completed { background: #2D6A4F; }
        .lep-dot-failed { background: #B91C1C; }
        @keyframes lep-pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
        .lep-run-title {
          flex: 1;
          font-size: var(--shunya-text-sm, 12px);
          font-weight: 500;
          color: var(--shunya-text, #1A1C1D);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .lep-run-badge {
          font-size: 9px;
          font-weight: 600;
          padding: 2px 6px;
          border-radius: 4px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          flex-shrink: 0;
        }
        .lep-badge-pending { background: rgba(26,28,29,0.06); color: rgba(26,28,29,0.45); }
        .lep-badge-running { background: rgba(108,74,226,0.1); color: #6C4AE2; }
        .lep-badge-completed { background: rgba(45,106,79,0.1); color: #2D6A4F; }
        .lep-badge-failed { background: rgba(185,28,28,0.08); color: #B91C1C; }
        .lep-run-phase {
          font-size: var(--shunya-text-xs, 10px);
          color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
          margin-left: 16px;
          margin-top: 4px;
        }
        .lep-run-detail {
          margin-top: 8px;
          margin-left: 16px;
          padding: 8px 12px;
          background: var(--shunya-bg, #FBF8F5);
          border-radius: 8px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .lep-run-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .lep-meta-label {
          font-size: 9px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
        }
        .lep-meta-value {
          font-size: var(--shunya-text-xs, 10px);
          color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
        }
        .lep-run-result {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .lep-run-result-text {
          font-size: var(--shunya-text-xs, 10px);
          color: var(--shunya-text, #1A1C1D);
          line-height: 1.5;
        }
        .lep-run-error {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .lep-run-error-text {
          font-size: var(--shunya-text-xs, 10px);
          color: #B91C1C;
          line-height: 1.5;
        }
        .lep-run-phases {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .lep-phase {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .lep-phase-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          flex-shrink: 0;
        }
        .lep-phase-label {
          font-size: var(--shunya-text-xs, 10px);
          color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
        }
      `}</style>
    </div>
  );
}