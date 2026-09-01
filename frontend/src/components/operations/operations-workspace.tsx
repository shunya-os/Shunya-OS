/**
 * Operations Workspace — Real operational data from execution engine endpoints.
 *
 * Shows: commitments, tasks, executions, outcomes — the full operations
 * lifecycle from commitment through execution to outcome.
 *
 * This is NOT a placeholder. It renders real data from the existing
 * execution engine API.
 */

import { useState, useEffect, useCallback, type FC } from 'react';

// ── Data Types ──────────────────────────────────────────────────────────

interface WorkItem {
  id: string;
  type: 'commitment' | 'task' | 'execution' | 'outcome';
  title: string;
  status: string;
  progress: number;
  context?: string;
  owner?: string;
  source?: string;
  priority?: string;
  due_date?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  completed_at?: string | null;
  result?: string;
  error?: string;
  drilldown?: string;
}

interface WorkSummary {
  total_outcomes: number;
  total_tasks: number;
  total_commitments: number;
}

interface WorkResponse {
  success: boolean;
  data: {
    items: WorkItem[];
    summary: WorkSummary;
  };
}

// ── API Helper ──────────────────────────────────────────────────────────

async function api<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    if (r.status >= 500) return null;
    return (await r.json()) as T;
  } catch {
    return null;
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return '—';
  }
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: '#c0392b',
  high: '#e67e22',
  medium: '#a4865f',
  low: 'rgba(26,28,29,0.45)',
  normal: 'rgba(26,28,29,0.55)',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'rgba(26,28,29,0.4)',
  in_progress: '#2980b9',
  active: '#6a9f6a',
  completed: '#6a9f6a',
  done: '#6a9f6a',
  failed: '#c0392b',
  cancelled: 'rgba(26,28,29,0.25)',
  accepted: '#6a9f6a',
  reviewing: '#e67e22',
  blocked: '#c0392b',
};

const TYPE_ICONS: Record<string, string> = {
  commitment: '◎',
  task: '◉',
  execution: '⟳',
  outcome: '✓',
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || 'rgba(26,28,29,0.55)';
  return (
    <span
      className="pw-commercial-tag"
      style={{
        background: `${color}18`,
        color,
        border: `1px solid ${color}30`,
        fontWeight: 500,
        textTransform: 'capitalize',
      }}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div
      className="pw-work-track"
      style={{ display: 'inline-block', verticalAlign: 'middle' }}
    >
      <span
        className="pw-work-fill"
        style={{
          width: `${Math.round(value * 100)}%`,
          background:
            value >= 1
              ? '#6a9f6a'
              : value > 0.5
                ? '#a4865f'
                : value > 0
                  ? '#2980b9'
                  : 'transparent',
        }}
      />
    </div>
  );
}

function MetricCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div
      style={{
        background: '#fff',
        border: '1px solid rgba(26,28,29,0.07)',
        borderRadius: 10,
        padding: '16px 20px',
        flex: 1,
        minWidth: 120,
      }}
    >
      <div
        style={{
          fontSize: 24,
          fontWeight: 700,
          color: color || 'var(--shunya-text, #1A1C1D)',
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: 12,
          color: 'rgba(26,28,29,0.55)',
          marginTop: 4,
        }}
      >
        {label}
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────

type TabKey = 'all' | 'outcomes' | 'tasks' | 'commitments';

export const OperationsWorkspace: FC = () => {
  const [tab, setTab] = useState<TabKey>('all');
  const [items, setItems] = useState<WorkItem[]>([]);
  const [, setSummary] = useState<WorkSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api<WorkResponse>('/api/v1/execution/work');
      if (res?.success && res.data) {
        setItems(res.data.items || []);
        setSummary(res.data.summary);
      } else {
        // Try individually per endpoint
        setItems([]);
      }
    } catch {
      setError('Could not load operational data. The service may be unavailable.');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Filter items by type for tab views
  const outcomes = items.filter((i) => i.type === 'outcome');
  const tasks = items.filter((i) => i.type === 'task');
  const commitments = items.filter((i) => i.type === 'commitment');

  const filteredItems =
    tab === 'all'
      ? items
      : tab === 'outcomes'
        ? outcomes
        : tab === 'tasks'
          ? tasks
          : commitments;

  // Stats
  const activeCount = items.filter(
    (i) => i.status === 'active' || i.status === 'in_progress',
  ).length;
  const completedCount = items.filter(
    (i) => i.status === 'completed' || i.status === 'done',
  ).length;
  const failedCount = items.filter(
    (i) => i.status === 'failed' || i.status === 'cancelled',
  ).length;

  return (
    <div className="pw-panel-container" style={{ padding: '24px 32px', maxWidth: 960 }}>
      <div className="pw-domain-header">
        <span className="pw-domain-icon">△</span>
        <h2 className="pw-domain-title">Operations</h2>
      </div>
      <p
        style={{
          fontSize: 14,
          color: 'rgba(26,28,29,0.55)',
          margin: '0 0 20px',
        }}
      >
        Commitments → Tasks → Executions → Outcomes
      </p>

      {/* Metrics */}
      {!loading && !error && items.length > 0 && (
        <div
          style={{
            display: 'flex',
            gap: 12,
            marginBottom: 20,
            flexWrap: 'wrap',
          }}
        >
          <MetricCard label="Active" value={String(activeCount)} color="#2980b9" />
          <MetricCard
            label="Completed"
            value={String(completedCount)}
            color="#6a9f6a"
          />
          <MetricCard
            label="Failed / Cancelled"
            value={String(failedCount)}
            color={failedCount > 0 ? '#c0392b' : 'rgba(26,28,29,0.45)'}
          />
          <MetricCard label="Total Items" value={String(items.length)} />
        </div>
      )}

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, flexWrap: 'wrap' }}>
        {(
          [
            { key: 'all', label: `All (${items.length})` },
            { key: 'outcomes', label: `Outcomes (${outcomes.length})` },
            { key: 'tasks', label: `Tasks (${tasks.length})` },
            { key: 'commitments', label: `Commitments (${commitments.length})` },
          ] as const
        ).map((t) => (
          <button
            key={t.key}
            className={`pw-tab-btn ${tab === t.key ? 'pw-tab-active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && <div className="pw-domain-loading">Loading operational data…</div>}

      {/* Error */}
      {error && (
        <div
          className="pw-error-msg"
          style={{ color: '#c0392b', fontSize: 13, marginBottom: 16 }}
        >
          {error}
          <button
            className="pw-tab-btn"
            style={{ marginLeft: 12 }}
            onClick={loadData}
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredItems.length === 0 && (
        <div className="pw-domain-empty">
          <p>
            {tab === 'all'
              ? 'No operational data found.'
              : tab === 'outcomes'
                ? 'No outcomes recorded yet.'
                : tab === 'tasks'
                  ? 'No tasks created yet.'
                  : 'No commitments made yet.'}
          </p>
          <p className="pw-domain-empty-hint">
            {tab === 'all' &&
              'Commitments, tasks, and execution outcomes will appear here as SHUNYA processes your requests.'}
            {tab === 'outcomes' &&
              'Outcomes are produced when SHUNYA completes work. Ask SHUNYA to do something to see outcomes.'}
            {tab === 'tasks' &&
              'Tasks appear when work is broken down into steps. These can be created automatically or manually.'}
            {tab === 'commitments' &&
              'Commitments are promises SHUNYA makes to take action. They appear when you ask SHUNYA to do something.'}
          </p>
        </div>
      )}

      {/* Work Item List */}
      {!loading && !error && filteredItems.length > 0 && (
        <div className="pw-commercial-list">
          {filteredItems.map((item) => {
            const icon = TYPE_ICONS[item.type] || '◇';
            const priorityColor =
              PRIORITY_COLORS[item.priority || 'normal'] || 'rgba(26,28,29,0.55)';

            return (
              <div key={item.id} className="pw-commercial-item">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span
                    style={{
                      fontSize: 14,
                      opacity: 0.6,
                      flexShrink: 0,
                    }}
                    title={item.type}
                  >
                    {icon}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div className="pw-commercial-item-title">
                      {item.title}
                    </div>
                    <div className="pw-commercial-item-meta">
                      <StatusBadge status={item.status} />
                      <span
                        className="pw-commercial-tag"
                        style={{
                          color: priorityColor,
                          border: `1px solid ${priorityColor}25`,
                          background: `${priorityColor}12`,
                        }}
                      >
                        {item.priority || 'normal'}
                      </span>
                      <span className="pw-commercial-tag">
                        {item.type}
                      </span>
                      {item.owner && (
                        <span className="pw-commercial-tag">
                          {item.owner}
                        </span>
                      )}
                    </div>
                    {item.context && (
                      <div
                        style={{
                          fontSize: 12,
                          color: 'rgba(26,28,29,0.55)',
                          marginTop: 4,
                        }}
                      >
                        {item.context}
                      </div>
                    )}
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-end',
                      gap: 4,
                      flexShrink: 0,
                    }}
                  >
                    <ProgressBar value={item.progress} />
                    <span
                      style={{
                        fontSize: 11,
                        color: 'rgba(26,28,29,0.35)',
                      }}
                    >
                      {formatDate(item.created_at)}
                    </span>
                    {item.due_date && (
                      <span
                        style={{
                          fontSize: 11,
                          color: '#e67e22',
                        }}
                      >
                        Due {formatDate(item.due_date)}
                      </span>
                    )}
                  </div>
                </div>
                {item.result && (
                  <div
                    style={{
                      fontSize: 12,
                      color: '#6a9f6a',
                      marginTop: 6,
                      padding: '6px 10px',
                      background: 'rgba(106,159,106,0.06)',
                      borderRadius: 4,
                    }}
                  >
                    {item.result}
                  </div>
                )}
                {item.error && (
                  <div
                    style={{
                      fontSize: 12,
                      color: '#c0392b',
                      marginTop: 6,
                      padding: '6px 10px',
                      background: 'rgba(192,57,43,0.06)',
                      borderRadius: 4,
                    }}
                  >
                    {item.error}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};