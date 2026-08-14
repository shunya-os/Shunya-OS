/**
 * Executive Home — The first production-quality founder experience of SHUNYA.
 *
 * Milestone E1 — Executive Home v1
 *
 * This is not a dashboard.
 * This is the first screen a founder sees immediately after authentication.
 *
 * Purpose: Answer:
 *   What requires my attention?
 *   What changed since my last visit?
 *   What commitments are active?
 *   What should I do next?
 *   What is SHUNYA already doing for me?
 *
 * Design principles:
 *   calm interface
 *   object-first
 *   AI continuously available
 *   whitespace prioritized
 *   no dashboard clutter
 *   no card explosion
 *   no excessive colours
 */

import { useEffect, useState, useCallback } from 'react';
import { useCommandPalette } from '../../hooks/workspace-hooks';
import { CommandSurface } from './command-surface';

// ── Types ───────────────────────────────────────────────────────

interface Priority {
  id: string;
  title: string;
  reason: string;
  affected_objects: number;
  urgency: 'high' | 'medium' | 'low';
  recommended_action: string;
}

interface ActivityEvent {
  type: string;
  title: string;
  description: string;
  object_type: string;
  object_id: string;
  timestamp: string;
  actor: string;
}

interface Commitment {
  id: string;
  title: string;
  type: string;
  status: string;
  owner: string;
  due_date: string | null;
  progress: number;
  related_objects: string[];
}

interface ObjectSummary {
  total: number;
  by_type: Record<string, number>;
  at_risk: number;
}

interface ExecutiveHomeData {
  health: { status: string; bootstrapped: boolean; runtime_count: number };
  priorities: Priority[];
  recent_activity: ActivityEvent[];
  active_commitments: Commitment[];
  object_summary: ObjectSummary;
  generated_at: string;
}

// ── Helpers ──────────────────────────────────────────────────────

function formatTimestamp(ts: string): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

function urgencyLabel(u: string): string {
  switch (u) {
    case 'high': return 'High';
    case 'medium': return 'Medium';
    case 'low': return 'Low';
    default: return u;
  }
}

function urgencyClass(u: string): string {
  switch (u) {
    case 'high': return 'eh-urgency-high';
    case 'medium': return 'eh-urgency-medium';
    case 'low': return 'eh-urgency-low';
    default: return '';
  }
}

function typeLabel(t: string): string {
  return t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ── Section Components ──────────────────────────────────────────

function Section({ title, children, empty }: { title: string; children: React.ReactNode; empty?: string }) {
  return (
    <div className="eh-section">
      <h2 className="eh-section-title">{title}</h2>
      {children}
      {empty && <p className="eh-empty">{empty}</p>}
    </div>
  );
}

function PriorityCard({ priority }: { priority: Priority }) {
  return (
    <div className={`eh-priority ${urgencyClass(priority.urgency)}`}>
      <div className="eh-priority-header">
        <span className={`eh-priority-dot eh-dot-${priority.urgency}`} />
        <span className="eh-priority-urgency">{urgencyLabel(priority.urgency)}</span>
      </div>
      <h3 className="eh-priority-title">{priority.title}</h3>
      <p className="eh-priority-reason">{priority.reason}</p>
      <div className="eh-priority-footer">
        {priority.affected_objects > 0 && (
          <span className="eh-priority-count">{priority.affected_objects} object(s) affected</span>
        )}
        <span className="eh-priority-action">{priority.recommended_action}</span>
      </div>
    </div>
  );
}

function ActivityItem({ event, onOpenObject }: { event: ActivityEvent; onOpenObject: (t: string, id: string, name: string) => void }) {
  const typeIcon: Record<string, string> = {
    object_updated: '📝',
    conversation: '💬',
    object_created: '✨',
  };

  return (
    <div className="eh-activity-item">
      <span className="eh-activity-icon">{typeIcon[event.type] || '📌'}</span>
      <div className="eh-activity-body">
        <div className="eh-activity-title">{event.title}</div>
        <div className="eh-activity-meta">
          {formatTimestamp(event.timestamp)} · {event.actor}
        </div>
      </div>
      {event.object_id && (
        <button
          className="eh-activity-open"
          onClick={() => onOpenObject(event.object_type, event.object_id, event.title)}
          title="Open in workspace"
        >
          → Open
        </button>
      )}
    </div>
  );
}

function CommitmentCard({ commitment, onOpen }: { commitment: Commitment; onOpen: (t: string, id: string, name: string) => void }) {
  const statusClass = commitment.status === 'active' ? 'eh-cmt-active' : 'eh-cmt-idle';
  const progressPct = Math.round(commitment.progress * 100);

  return (
    <button className={`eh-commitment ${statusClass}`} onClick={() => onOpen(commitment.type, commitment.id, commitment.title)}>
      <div className="eh-cmt-header">
        <span className="eh-cmt-type">{typeLabel(commitment.type)}</span>
        <span className="eh-cmt-status">{commitment.status}</span>
      </div>
      <div className="eh-cmt-title">{commitment.title}</div>
      <div className="eh-cmt-meta">
        {commitment.owner && <span>Owner: {commitment.owner}</span>}
        {commitment.due_date && <span>Due: {formatTimestamp(commitment.due_date)}</span>}
      </div>
      <div className="eh-cmt-progress">
        <div className="eh-cmt-progress-track">
          <div className="eh-cmt-progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
        <span className="eh-cmt-progress-label">{progressPct}%</span>
      </div>
    </button>
  );
}

// ── Loading State ───────────────────────────────────────────────

function ExecutiveHomeSkeleton() {
  return (
    <div className="eh-workspace" aria-busy="true">
      <div className="eh-header">
        <div className="eh-header-top">
          <div className="sh-skel-line w-40" />
          <div className="sh-skel-line w-24" />
        </div>
        <div className="sh-skel-line w-64" style={{ marginTop: 8 }} />
      </div>
      <div className="eh-body">
        <div className="eh-main">
          <div className="eh-section">
            <div className="sh-skel-line w-32" />
            <div className="eh-priority-grid">
              {[1, 2, 3].map(i => (
                <div key={i} className="eh-priority eh-priority-skeleton">
                  <div className="sh-skel-line w-16" />
                  <div className="sh-skel-line w-48" style={{ marginTop: 8 }} />
                  <div className="sh-skel-line w-40" style={{ marginTop: 4 }} />
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="eh-sidebar">
          <div className="sh-skel-line w-24" />
          <div className="sh-skel-line w-48" style={{ marginTop: 8 }} />
          <div className="sh-skel-line w-40" style={{ marginTop: 4 }} />
        </div>
      </div>
    </div>
  );
}

// ── Empty State ─────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="eh-empty-state">
      <div className="eh-empty-zero">शून्य</div>
      <h2 className="eh-empty-title">Welcome to SHUNYA</h2>
      <p className="eh-empty-text">
        Your organization is ready. SHUNYA is observing your business.
        Begin by creating your first business object or exploring what SHUNYA can do.
      </p>
      <div className="eh-empty-actions">
        <button
          className="eh-empty-action eh-empty-action-primary"
          onClick={() => {
            const ws = useWorkspaceStore.getState();
            ws.open('Create Object', 'object', { objectType: 'Document', objectId: 'new' });
          }}
        >
          Create First Object
        </button>
        <button
          className="eh-empty-action"
          onClick={() => {
            const ws = useWorkspaceStore.getState();
            ws.open('Conversation', 'conversation', { objectType: 'conversation', objectId: 'new' });
          }}
        >
          Start a Conversation
        </button>
      </div>
      <div className="eh-empty-capabilities">
        <h3>Available Capabilities</h3>
        <ul>
          <li>Create and manage business objects</li>
          <li>Track commitments and execution</li>
          <li>Search across all your objects</li>
          <li>Ask SHUNYA about your business</li>
          <li>Navigate between workspaces</li>
        </ul>
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────

export function ExecutiveHome({ loading: parentLoading }: { loading?: boolean }) {
  const [data, setData] = useState<ExecutiveHomeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { openObject } = useCommandPalette();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch('/api/v1/founder/executive-home', { credentials: 'include' });
      if (!r.ok) {
        if (r.status === 401) throw new Error('Session expired. Please sign in again.');
        throw new Error(`Server error (${r.status})`);
      }
      const json = await r.json();
      if (json.success && json.data) {
        setData(json.data as ExecutiveHomeData);
      } else {
        throw new Error(json.error || 'Failed to load executive home');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load executive home');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ── Loading ──
  if (loading || parentLoading) return <ExecutiveHomeSkeleton />;

  // ── Error ──
  if (error) {
    return (
      <div className="eh-workspace" role="alert">
        <div className="eh-error">
          <div className="eh-error-icon">⚠</div>
          <div className="eh-error-title">Executive Home Unavailable</div>
          <div className="eh-error-message">{error}</div>
          <button className="eh-error-retry" onClick={fetchData}>
            Retry
          </button>
        </div>
        <CommandSurface />
      </div>
    );
  }

  // ── Empty State ──
  const isEmpty = data && data.object_summary.total === 0 && data.active_commitments.length === 0;
  if (isEmpty) {
    return (
      <div className="eh-workspace">
        <EmptyState />
        <CommandSurface />
      </div>
    );
  }

  // ── Data State ──
  const priorities = data?.priorities || [];
  const recentActivity = data?.recent_activity || [];
  const activeCommitments = data?.active_commitments || [];
  const objectSummary = data?.object_summary || { total: 0, by_type: {}, at_risk: 0 };
  const generatedAt = data?.generated_at || '';

  return (
    <div className="eh-workspace">
      {/* Header */}
      <div className="eh-header">
        <div className="eh-header-top">
          <h1 className="eh-title">Executive Home</h1>
          <span className="eh-timestamp">{formatTimestamp(generatedAt)}</span>
        </div>
        <p className="eh-subtitle">
          {objectSummary.total > 0
            ? `${objectSummary.total} object(s) · ${priorities.length} priorit${priorities.length === 1 ? 'y' : 'ies'} · ${activeCommitments.length} commitment${activeCommitments.length === 1 ? '' : 's'}`
            : 'Your organization at a glance'}
        </p>
      </div>

      {/* Body */}
      <div className="eh-body">
        {/* Main content */}
        <div className="eh-main">
          {/* Priorities */}
          {priorities.length > 0 && (
            <Section title="Priorities">
              <div className="eh-priority-grid">
                {priorities.map(p => (
                  <PriorityCard key={p.id} priority={p} />
                ))}
              </div>
            </Section>
          )}

          {/* Recent Activity */}
          {recentActivity.length > 0 && (
            <Section title="Recent Activity">
              <div className="eh-activity-list">
                {recentActivity.slice(0, 10).map((event, i) => (
                  <ActivityItem key={`${event.object_id}-${i}`} event={event} onOpenObject={openObject} />
                ))}
              </div>
            </Section>
          )}

          {recentActivity.length === 0 && priorities.length === 0 && (
            <Section title="" empty="SHUNYA is observing. Activity will appear here as your organization grows.">
              <div />
            </Section>
          )}
        </div>

        {/* Sidebar */}
        <div className="eh-sidebar">
          {/* Active Commitments */}
          {activeCommitments.length > 0 && (
            <Section title="Active Commitments">
              <div className="eh-commitments-list">
                {activeCommitments.map(c => (
                  <CommitmentCard key={c.id} commitment={c} onOpen={openObject} />
                ))}
              </div>
            </Section>
          )}

          {/* Summary */}
          {objectSummary.total > 0 && (
            <Section title="Summary">
              <div className="eh-summary">
                <div className="eh-summary-row">
                  <span className="eh-summary-label">Total</span>
                  <span className="eh-summary-value">{objectSummary.total}</span>
                </div>
                {Object.entries(objectSummary.by_type).slice(0, 5).map(([type, count]) => (
                  <div key={type} className="eh-summary-row">
                    <span className="eh-summary-label">{typeLabel(type)}</span>
                    <span className="eh-summary-value">{count}</span>
                  </div>
                ))}
                {objectSummary.at_risk > 0 && (
                  <div className="eh-summary-row eh-summary-at-risk">
                    <span className="eh-summary-label">At Risk</span>
                    <span className="eh-summary-value">{objectSummary.at_risk}</span>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* System Status */}
          <Section title="System Status">
            <div className="eh-summary">
              <div className="eh-summary-row">
                <span className="eh-summary-label">Pipeline</span>
                <span className={`eh-summary-value eh-status-${data?.health?.status || 'unknown'}`}>
                  {data?.health?.status || 'Unknown'}
                </span>
              </div>
              <div className="eh-summary-row">
                <span className="eh-summary-label">Runtimes</span>
                <span className="eh-summary-value">{data?.health?.runtime_count || 0}</span>
              </div>
            </div>
          </Section>
        </div>
      </div>

      {/* Command Surface */}
      <CommandSurface />

      <style>{`
/* ── Layout ──────────────────────────────────────────────────── */
.eh-workspace {
  display: flex; flex-direction: column;
  height: 100%; overflow-y: auto;
  padding: var(--shunya-spacing-lg);
  padding-bottom: 80px; /* space for command surface */
}
.eh-header {
  padding-bottom: var(--shunya-spacing-md);
  border-bottom: 1px solid var(--shunya-surface-1, #22222e);
  margin-bottom: var(--shunya-spacing-lg);
}
.eh-header-top {
  display: flex; align-items: center; justify-content: space-between;
}
.eh-title {
  font-size: var(--shunya-font-size-xl);
  font-weight: 500;
  color: var(--shunya-text, #e0e0e0);
  margin: 0;
}
.eh-timestamp {
  font-size: var(--shunya-font-size-xs);
  color: var(--shunya-text-secondary, #666);
}
.eh-subtitle {
  font-size: var(--shunya-font-size-sm);
  color: var(--shunya-text-secondary, #888);
  margin: 4px 0 0;
}
.eh-body {
  display: flex; gap: var(--shunya-spacing-lg);
  flex: 1;
}
.eh-main {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column; gap: var(--shunya-spacing-xl);
}
.eh-sidebar {
  width: 320px; flex-shrink: 0;
  display: flex; flex-direction: column; gap: var(--shunya-spacing-lg);
}

/* ── Sections ────────────────────────────────────────────────── */
.eh-section { }
.eh-section-title {
  font-size: var(--shunya-font-size-sm);
  font-weight: 500;
  color: var(--shunya-text, #e0e0e0);
  margin: 0 0 var(--shunya-spacing-sm);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.eh-empty {
  font-size: var(--shunya-font-size-sm);
  color: var(--shunya-text-secondary, #666);
  font-style: italic;
  padding: var(--shunya-spacing-sm) 0;
}

/* ── Priority Cards ──────────────────────────────────────────── */
.eh-priority-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--shunya-spacing-sm);
}
.eh-priority {
  padding: var(--shunya-spacing-md);
  background: var(--shunya-surface-2, #1a1a26);
  border: 1px solid var(--shunya-surface-1, #2a2a3a);
  border-radius: var(--shunya-radius-md, 8px);
  transition: border-color 0.15s;
}
.eh-priority:hover { border-color: var(--shunya-color-secondary, #D4A84B); }
.eh-priority-skeleton { min-height: 80px; }
.eh-priority-header {
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 4px;
}
.eh-priority-dot {
  width: 8px; height: 8px; border-radius: 50%;
}
.eh-dot-high { background: var(--shunya-color-danger, #9B2226); }
.eh-dot-medium { background: var(--shunya-color-warning, #E09F3E); }
.eh-dot-low { background: var(--shunya-color-success, #2D6A4F); }
.eh-priority-urgency {
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em;
  font-weight: 600;
}
.eh-urgency-high .eh-priority-urgency { color: var(--shunya-color-danger, #9B2226); }
.eh-urgency-medium .eh-priority-urgency { color: var(--shunya-color-warning, #E09F3E); }
.eh-urgency-low .eh-priority-urgency { color: var(--shunya-color-success, #2D6A4F); }
.eh-priority-title {
  font-size: var(--shunya-font-size-sm);
  font-weight: 500;
  color: var(--shunya-text, #e0e0e0);
  margin: 0 0 2px;
}
.eh-priority-reason {
  font-size: var(--shunya-font-size-xs);
  color: var(--shunya-text-secondary, #888);
  margin: 0;
  line-height: 1.4;
}
.eh-priority-footer {
  display: flex; align-items: center; gap: 8px;
  margin-top: 8px; flex-wrap: wrap;
}
.eh-priority-count {
  font-size: 10px; color: var(--shunya-text-secondary, #666);
  background: var(--shunya-surface-0, #141416);
  padding: 2px 6px; border-radius: 4px;
}
.eh-priority-action {
  font-size: 10px; color: var(--shunya-color-ai, #D4A84B);
  font-style: italic;
}

/* ── Activity List ───────────────────────────────────────────── */
.eh-activity-list {
  display: flex; flex-direction: column;
  gap: 2px;
}
.eh-activity-item {
  display: flex; align-items: center; gap: var(--shunya-spacing-sm);
  padding: var(--shunya-spacing-sm) var(--shunya-spacing-md);
  border-radius: var(--shunya-radius-sm, 4px);
  transition: background 0.15s;
}
.eh-activity-item:hover { background: var(--shunya-surface-1, #22222e); }
.eh-activity-icon { font-size: 14px; flex-shrink: 0; }
.eh-activity-body { flex: 1; min-width: 0; }
.eh-activity-title {
  font-size: var(--shunya-font-size-sm);
  color: var(--shunya-text, #e0e0e0);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.eh-activity-meta {
  font-size: 10px; color: var(--shunya-text-secondary, #666);
}
.eh-activity-open {
  font-size: 10px; color: var(--shunya-color-ai, #D4A84B);
  background: transparent; border: 1px solid transparent;
  padding: 2px 8px; border-radius: 4px; cursor: pointer;
  white-space: nowrap; flex-shrink: 0;
}
.eh-activity-open:hover { border-color: var(--shunya-color-ai, #D4A84B); }

/* ── Commitments ─────────────────────────────────────────────── */
.eh-commitments-list {
  display: flex; flex-direction: column; gap: 4px;
}
.eh-commitment {
  display: flex; flex-direction: column; gap: 4px;
  width: 100%; padding: var(--shunya-spacing-sm) var(--shunya-spacing-md);
  background: var(--shunya-surface-2, #1a1a26);
  border: 1px solid var(--shunya-surface-1, #2a2a3a);
  border-radius: var(--shunya-radius-sm, 4px);
  cursor: pointer; text-align: left; color: inherit; font: inherit;
  transition: border-color 0.15s;
}
.eh-commitment:hover { border-color: var(--shunya-color-secondary, #D4A84B); }
.eh-commitment.eh-cmt-active { border-left: 3px solid var(--shunya-color-success, #2D6A4F); }
.eh-commitment.eh-cmt-idle { border-left: 3px solid var(--shunya-text-secondary, #555); }
.eh-cmt-header {
  display: flex; justify-content: space-between; align-items: center;
}
.eh-cmt-type {
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--shunya-text-secondary, #888);
}
.eh-cmt-status {
  font-size: 10px; color: var(--shunya-text-secondary, #666);
  text-transform: capitalize;
}
.eh-cmt-title {
  font-size: var(--shunya-font-size-sm);
  font-weight: 500;
  color: var(--shunya-text, #e0e0e0);
}
.eh-cmt-meta {
  font-size: 10px; color: var(--shunya-text-secondary, #666);
  display: flex; gap: 8px;
}
.eh-cmt-progress {
  display: flex; align-items: center; gap: 6px;
}
.eh-cmt-progress-track {
  flex: 1; height: 4px;
  background: var(--shunya-surface-1, #22222e);
  border-radius: 2px; overflow: hidden;
}
.eh-cmt-progress-fill {
  height: 100%; border-radius: 2px;
  background: var(--shunya-color-success, #2D6A4F);
  transition: width 0.3s;
}
.eh-cmt-progress-label {
  font-size: 10px; color: var(--shunya-text-secondary, #888);
  min-width: 28px; text-align: right;
}

/* ── Summary ─────────────────────────────────────────────────── */
.eh-summary {
  display: flex; flex-direction: column; gap: 4px;
}
.eh-summary-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 0;
  font-size: var(--shunya-font-size-sm);
}
.eh-summary-label { color: var(--shunya-text-secondary, #888); }
.eh-summary-value { color: var(--shunya-text, #e0e0e0); font-weight: 500; }
.eh-summary-at-risk .eh-summary-value { color: var(--shunya-color-danger, #9B2226); }
.eh-status-ok { color: var(--shunya-color-success, #2D6A4F); }
.eh-status-degraded { color: var(--shunya-color-warning, #E09F3E); }
.eh-status-error { color: var(--shunya-color-danger, #9B2226); }
.eh-status-unknown { color: var(--shunya-text-secondary, #888); }

/* ── Error State ─────────────────────────────────────────────── */
.eh-error {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: var(--shunya-spacing-md);
  padding: var(--shunya-spacing-xl); text-align: center;
  flex: 1;
}
.eh-error-icon { font-size: 2rem; }
.eh-error-title { font-size: var(--shunya-font-size-lg); font-weight: 500; color: var(--shunya-text, #e0e0e0); }
.eh-error-message { font-size: var(--shunya-font-size-sm); color: var(--shunya-text-secondary, #888); max-width: 400px; }
.eh-error-retry {
  padding: var(--shunya-spacing-sm) var(--shunya-spacing-lg);
  background: var(--shunya-color-primary, #555); color: #fff;
  border: none; border-radius: var(--shunya-radius-sm, 4px);
  cursor: pointer; font-size: var(--shunya-font-size-sm);
}
.eh-error-retry:hover { opacity: 0.85; }

/* ── Empty State ─────────────────────────────────────────────── */
.eh-empty-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: var(--shunya-spacing-lg);
  padding: var(--shunya-spacing-xl); text-align: center;
  flex: 1; max-width: 560px; margin: 0 auto;
}
.eh-empty-zero {
  font-size: 3rem; color: var(--shunya-text, #e0e0e0);
  font-weight: 300; opacity: 0.4;
}
.eh-empty-title {
  font-size: var(--shunya-font-size-xl);
  font-weight: 500; color: var(--shunya-text, #e0e0e0);
  margin: 0;
}
.eh-empty-text {
  font-size: var(--shunya-font-size-sm);
  color: var(--shunya-text-secondary, #888);
  line-height: 1.6; margin: 0;
}
.eh-empty-actions {
  display: flex; gap: var(--shunya-spacing-sm);
}
.eh-empty-action {
  padding: var(--shunya-spacing-sm) var(--shunya-spacing-lg);
  background: transparent; border: 1px solid var(--shunya-surface-1, #333);
  border-radius: var(--shunya-radius-sm, 4px);
  color: var(--shunya-text, #e0e0e0);
  font-size: var(--shunya-font-size-sm); cursor: pointer;
  transition: all 0.15s;
}
.eh-empty-action:hover { border-color: var(--shunya-color-secondary, #D4A84B); }
.eh-empty-action-primary { background: var(--shunya-color-ai, #D4A84B); color: #0a0a0f; border-color: var(--shunya-color-ai, #D4A84B); }
.eh-empty-action-primary:hover { opacity: 0.85; }
.eh-empty-capabilities {
  text-align: left; width: 100%;
  padding: var(--shunya-spacing-md);
  background: var(--shunya-surface-2, #1a1a26);
  border: 1px solid var(--shunya-surface-1, #2a2a3a);
  border-radius: var(--shunya-radius-md, 8px);
}
.eh-empty-capabilities h3 {
  font-size: var(--shunya-font-size-sm);
  font-weight: 500; color: var(--shunya-text, #e0e0e0);
  margin: 0 0 var(--shunya-spacing-sm);
}
.eh-empty-capabilities ul {
  margin: 0; padding: 0 0 0 var(--shunya-spacing-lg);
  display: flex; flex-direction: column; gap: 4px;
}
.eh-empty-capabilities li {
  font-size: var(--shunya-font-size-sm);
  color: var(--shunya-text-secondary, #888);
}

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 768px) {
  .eh-body { flex-direction: column; }
  .eh-sidebar { width: 100%; }
  .eh-priority-grid { grid-template-columns: 1fr; }
}
`}</style>
    </div>
  );
}

// Import the workspace store for empty state actions
import { useWorkspaceStore } from '../../runtimes/workspace/store';