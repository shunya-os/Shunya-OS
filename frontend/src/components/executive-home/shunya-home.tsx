/**
 * SHUNYA Home — ZGC-PR-11E Home Intelligence Surface.
 *
 * The first primary section after workspace entry.
 *
 * ── Principles ──
 * 70% calm whitespace | 20% contextual intelligence | 10% controls
 * Not a dashboard. Not static widgets. Not KPI cards.
 *
 * Answers the 8 Home questions:
 * WHAT IS HAPPENING? WHAT CHANGED? WHAT NEEDS ATTENTION?
 * WHAT IS GOING WELL? WHAT IS AT RISK? WHAT CAN I DO NEXT?
 * WHAT SHOULD I NOT MISS? WHAT CAN SHUNYA DO FOR ME?
 *
 * ── Layers ──
 * A. NOW — immediate present
 * B. SHUNYA SUGGESTIONS — evidence-based suggestions
 * C. WHAT CHANGED — meaningful change since last visit
 * D. ACTIVE COMMITMENTS — living promises
 * E. TASKS AND EXECUTION — operational items
 * F. SHUNYA WORK — running/scheduled background work
 * G. CALM — nothing needs attention
 */

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// ── Types ──────────────────────────────────────────────────────────

interface HomeIntelligence {
  success: boolean;
  data: {
    intelligence: HomeItem[];
    priorities: { critical: number; high: number; normal: number; low: number; total: number };
    now: { time_period: string; immediate_count: number; has_immediate: boolean; summary: string };
    changed: { count: number; items: HomeItem[] };
    commitments: { overdue_count: number; upcoming_count: number; items: HomeItem[] };
    relationships: { count: number; items: HomeItem[] };
    tasks: { count: number; items: HomeItem[] };
    shunya_work: { running: number; completed_recent: number; items: HomeItem[] };
    calm: boolean;
    workspace_type: string | null;
    workspace_id: string | null;
    synthesized_at: string;
    ai_summary?: string;
    ai_focus?: string;
    ai_suggestion?: string;
  };
}

interface HomeItem {
  type: string;
  id?: string | number;
  title?: string;
  name?: string;
  message?: string;
  owner?: string;
  status?: string;
  priority: string;
  priority_score: number;
  due_at?: string;
  overdue_by_hours?: number;
  due_in_hours?: number;
  object_type?: string;
  object_id?: string;
  count?: number;
  severity?: string;
  reason?: string;
  suggested_action?: string;
  label?: string;
  progress?: number;
  completed_at?: string;
  started_at?: string;
  changed_at?: string;
  category?: string;
}

// ── API ────────────────────────────────────────────────────────────

async function fetchHomeIntelligence(since?: string): Promise<HomeIntelligence> {
  const params = new URLSearchParams();
  if (since) params.set('since', since);
  const qs = params.toString();
  const r = await fetch(`/api/v1/home/intelligence${qs ? '?' + qs : ''}`, {
    credentials: 'include',
  });
  return r.json();
}

async function fetchExplain(type: string, id: string | number): Promise<{ success: boolean; data: { evidence: string[]; confidence: string } }> {
  const r = await fetch('/api/v1/home/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ type, id }),
  });
  return r.json();
}

async function sendFeedback(type: string, id: string | number | undefined, feedback: string) {
  await fetch('/api/v1/home/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ type, id: id ?? null, feedback }),
  });
}

// ── Utility ────────────────────────────────────────────────────────

function timeAgo(ts: string | undefined | null): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    const diff = Date.now() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

function itemTitle(item: HomeItem): string {
  return item.title || item.name || item.message || item.reason || '';
}

function itemId(item: HomeItem): string | number | undefined {
  return item.id ?? item.object_id;
}

function itemTypeLabel(item: HomeItem): string {
  const labels: Record<string, string> = {
    commitment_overdue: 'Overdue commitment',
    commitment_upcoming: 'Upcoming commitment',
    object_updated: 'Recent change',
    relationship_quiet: 'Quiet relationship',
    task_pending: 'Pending task',
    shunya_work_running: 'SHUNYA working',
    shunya_work_completed: 'SHUNYA completed',
    awareness: 'Awareness',
  };
  return labels[item.type] || item.type.replace(/_/g, ' ');
}

// ── Priority Icon ──────────────────────────────────────────────────

function PriorityIcon({ priority }: { priority: string }) {
  const icon = priority === 'critical' ? '⬡'
    : priority === 'high' ? '◈'
    : priority === 'normal' ? '◇'
    : '·';
  return <span className="sh-priority-icon" data-priority={priority}>{icon}</span>;
}

// ── Explain Modal ──────────────────────────────────────────────────

function ExplainModal({ item, onClose }: { item: HomeItem; onClose: () => void }) {
  const [evidence, setEvidence] = useState<string[]>([]);
  const [confidence, setConfidence] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = itemId(item);
    if (id) {
      fetchExplain(item.type, id).then(r => {
        if (r.success) {
          setEvidence(r.data.evidence || []);
          setConfidence(r.data.confidence);
        }
        setLoading(false);
      }).catch(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [item]);

  return (
    <motion.div
      className="sh-explain-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="sh-explain-card"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 12 }}
        onClick={e => e.stopPropagation()}
      >
        <div className="sh-explain-header">
          <span className="sh-explain-title">Why am I seeing this?</span>
          <button className="sh-explain-close" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="sh-explain-item">
          <span className="sh-explain-type">{itemTypeLabel(item)}</span>
          <span className="sh-explain-name">{itemTitle(item)}</span>
        </div>
        {loading ? (
          <p className="sh-explain-loading">Loading evidence…</p>
        ) : (
          <>
            <div className="sh-explain-evidence">
              {evidence.length > 0 ? (
                evidence.filter(e => e).map((e, i) => (
                  <div key={i} className="sh-explain-evidence-item">
                    <span className="sh-explain-evidence-bullet">•</span>
                    <span>{e}</span>
                  </div>
                ))
              ) : (
                <p className="sh-explain-no-evidence">This item was surfaced based on current system state. No specific evidence record is available.</p>
              )}
            </div>
            <div className="sh-explain-confidence">
              Confidence: <span className={`sh-explain-confidence-badge ${confidence}`}>{confidence}</span>
            </div>
          </>
        )}
        <button className="sh-explain-btn" onClick={onClose}>Got it</button>
      </motion.div>
    </motion.div>
  );
}

// ── Action Menu ────────────────────────────────────────────────────

function ActionMenu({ item, onClose, onDismiss, onDefer, onOpen }: {
  item: HomeItem;
  onClose: () => void;
  onDismiss: () => void;
  onDefer: () => void;
  onOpen?: () => void;
}) {
  return (
    <motion.div
      className="sh-action-menu-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="sh-action-menu"
        initial={{ opacity: 0, y: 8, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 8, scale: 0.95 }}
        onClick={e => e.stopPropagation()}
      >
        <button className="sh-action-btn" onClick={onOpen ?? onClose}>
          {item.object_id ? 'Open' : 'View details'}
        </button>
        <button className="sh-action-btn" onClick={onDefer}>
          Remind me later
        </button>
        <button className="sh-action-btn" onClick={() => { sendFeedback(item.type, itemId(item), 'not_useful'); onDismiss(); }}>
          Not relevant
        </button>
        <button className="sh-action-btn" onClick={() => { sendFeedback(item.type, itemId(item), 'dont_suggest_again'); onDismiss(); }}>
          Don't suggest this again
        </button>
        <button className="sh-action-btn sh-action-btn-cancel" onClick={onClose}>
          Cancel
        </button>
      </motion.div>
    </motion.div>
  );
}

// ── Home Intelligence Item ─────────────────────────────────────────

function HomeItemRow({ item, onOpenItem }: { item: HomeItem; onOpenItem?: (item: HomeItem) => void }) {
  const [showExplain, setShowExplain] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [deferred, setDeferred] = useState(false);

  if (dismissed || deferred) return null;

  const title = itemTitle(item);
  const typeLabel = itemTypeLabel(item);
  const id = itemId(item);

  const handleDismiss = () => {
    setDismissed(true);
    sendFeedback(item.type, id, 'not_useful');
  };

  const handleDefer = () => {
    setDeferred(true);
    sendFeedback(item.type, id, 'not_now');
  };

  const handleOpen = () => {
    if (onOpenItem) {
      onOpenItem(item);
    }
  };

  return (
    <motion.div
      className={`sh-home-item sh-home-item-${item.priority}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0, marginBottom: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="sh-home-item-row">
        <PriorityIcon priority={item.priority} />
        <div className="sh-home-item-body">
          <div className="sh-home-item-head">
            <span className="sh-home-item-type">{typeLabel}</span>
            {item.due_at && (
              <span className="sh-home-item-time">
                {item.overdue_by_hours ? `${item.overdue_by_hours}h overdue` : timeAgo(item.due_at)}
              </span>
            )}
            {item.changed_at && <span className="sh-home-item-time">{timeAgo(item.changed_at)}</span>}
          </div>
          <p className="sh-home-item-title">{title}</p>
          {item.reason && <p className="sh-home-item-reason">{item.reason}</p>}
          {item.suggested_action && (
            <p className="sh-home-item-action">→ {item.suggested_action}</p>
          )}
          {item.owner && <p className="sh-home-item-owner">Owner: {item.owner}</p>}
        </div>
        <div className="sh-home-item-actions">
          <button
            className="sh-home-item-act"
            onClick={() => setShowExplain(true)}
            title="Why am I seeing this?"
            aria-label="Explain"
          >
            ?
          </button>
          <button
            className="sh-home-item-act"
            onClick={() => setShowActions(true)}
            title="Actions"
            aria-label="Actions"
          >
            ···
          </button>
        </div>
      </div>

      <AnimatePresence>
        {showExplain && (
          <ExplainModal item={item} onClose={() => setShowExplain(false)} />
        )}
        {showActions && (
          <ActionMenu
            item={item}
            onClose={() => setShowActions(false)}
            onDismiss={handleDismiss}
            onDefer={handleDefer}
            onOpen={handleOpen}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Section Component ──────────────────────────────────────────────

function HomeSection({ label, count, items, onOpenItem, defaultExpanded = true }: {
  label: string;
  count?: number;
  items: HomeItem[];
  onOpenItem?: (item: HomeItem) => void;
  defaultExpanded?: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded && items.length > 0);

  if (items.length === 0) return null;

  return (
    <div className="sh-home-section">
      <button className="sh-home-section-header" onClick={() => setExpanded(!expanded)}>
        <span className="sh-home-section-label">
          {label}
          {count !== undefined && count > 0 && (
            <span className="sh-home-section-count">{count}</span>
          )}
        </span>
        <span className="sh-home-section-toggle">{expanded ? '▲' : '▼'}</span>
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            className="sh-home-section-items"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            {items.map((item, i) => (
              <HomeItemRow key={`${item.type}-${itemId(item) || i}`} item={item} onOpenItem={onOpenItem} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── SHUNYA AI Presence ─────────────────────────────────────────────

function ShunyaAIPresence({ summary, focus, suggestion }: {
  summary?: string;
  focus?: string;
  suggestion?: string;
}) {
  if (!summary && !focus && !suggestion) return null;

  return (
    <motion.div
      className="sh-home-ai-presence"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="sh-home-ai-dot" />
      <div className="sh-home-ai-content">
        {summary && <p className="sh-home-ai-summary">{summary}</p>}
        {focus && <p className="sh-home-ai-focus">Focus: {focus}</p>}
        {suggestion && <p className="sh-home-ai-suggestion">{suggestion}</p>}
      </div>
    </motion.div>
  );
}

// ── Now Summary ────────────────────────────────────────────────────

function NowSummary({ hasImmediate, immediateCount, summary, calm }: {
  hasImmediate: boolean;
  immediateCount: number;
  summary: string;
  calm: boolean;
}) {
  if (calm) {
    return (
      <div className="sh-home-calm">
        <div className="sh-home-calm-brand">शून्य</div>
        <p className="sh-home-calm-text">
          Nothing I can currently see requires your attention. Everything is being monitored.
        </p>
        <p className="sh-home-calm-hint">Explore your organization on the left, or ask SHUNYA anything.</p>
      </div>
    );
  }

  return (
    <div className="sh-home-now">
      <div className="sh-home-now-badge">
        {hasImmediate ? (
          <span className="sh-home-now-attention">{immediateCount} thing{immediateCount > 1 ? 's' : ''} need{immediateCount === 1 ? 's' : ''} attention</span>
        ) : (
          <span className="sh-home-now-calm">Everything stable</span>
        )}
      </div>
      <p className="sh-home-now-summary">{summary}</p>
    </div>
  );
}

// –─ Time Greeting ──────────────────────────────────────────────────

function TimeGreeting({ period }: { period: string }) {
  const greetings: Record<string, string> = {
    morning: 'Good morning',
    midday: 'Good afternoon',
    afternoon: 'Good afternoon',
    evening: 'Good evening',
    night: 'Good evening',
  };

  const greeting = greetings[period] || 'Hello';

  return (
    <div className="sh-home-greeting">
      <span className="sh-home-greeting-text">{greeting}</span>
    </div>
  );
}

// ── SHUNYA Work Section ────────────────────────────────────────────

function ShunyaWorkSection({ items }: { items: HomeItem[] }) {
  if (items.length === 0) return null;

  const running = items.filter(i => i.status === 'running');
  const completed = items.filter(i => i.status === 'completed');

  return (
    <div className="sh-home-section">
      <div className="sh-home-section-header">
        <span className="sh-home-section-label">
          SHUNYA IS WORKING ON
          {running.length > 0 && <span className="sh-home-section-count">{running.length}</span>}
        </span>
      </div>
      <div className="sh-home-section-items">
        {running.map((item, i) => (
          <div key={`run-${item.id || i}`} className="sh-home-work-item sh-home-work-running">
            <span className="sh-home-work-status">⟳</span>
            <div className="sh-home-work-body">
              <span className="sh-home-work-label">{item.label || 'Task'}</span>
              {item.progress !== undefined && (
                <div className="sh-home-work-track">
                  <div className="sh-home-work-fill" style={{ width: `${Math.round(item.progress * 100)}%` }} />
                </div>
              )}
            </div>
            <span className="sh-home-work-badge">Running</span>
          </div>
        ))}
        {completed.map((item, i) => (
          <div key={`done-${item.id || i}`} className="sh-home-work-item sh-home-work-done">
            <span className="sh-home-work-status">✓</span>
            <div className="sh-home-work-body">
              <span className="sh-home-work-label">{item.label || 'Task'}</span>
              {item.completed_at && <span className="sh-home-work-time">{timeAgo(item.completed_at)}</span>}
            </div>
            <span className="sh-home-work-badge sh-home-work-badge-done">Done</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Home Component ────────────────────────────────────────────

export function ShunyaHome() {
  const [data, setData] = useState<HomeIntelligence['data'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastVisit, setLastVisit] = useState<string | null>(null);

  // Load home intelligence
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchHomeIntelligence(lastVisit ?? undefined);
      if (resp.success) {
        setData(resp.data);
        // Update last visit timestamp
        setLastVisit(resp.data.synthesized_at);
      } else {
        setError('Could not load home intelligence');
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to connect');
    }
    setLoading(false);
  }, [lastVisit]);

  useEffect(() => {
    load();
  }, []);

  // Poll every 60 seconds
  useEffect(() => {
    const interval = setInterval(load, 60000);
    return () => clearInterval(interval);
  }, [load]);

  // Handle opening an item
  const handleOpenItem = (item: HomeItem) => {
    // If the item has an object_id, we can open it via the workspace store
    if (item.object_id) {
      // Import lazily to avoid circular deps
      import('../../runtimes/workspace/store').then(({ useWorkspaceStore }) => {
        useWorkspaceStore.getState().open(
          itemTitle(item),
          item.object_type as any ?? 'object',
          { objectId: item.object_id, objectType: item.object_type },
        );
      });
    }
  };

  // ── Loading State ──
  if (loading && !data) {
    return (
      <div className="sh-home">
        <div className="sh-home-loading">
          <div className="sh-home-loading-brand">शून्य</div>
          <p className="sh-home-loading-text">SHUNYA is gathering information…</p>
        </div>
      </div>
    );
  }

  // ── Error State ──
  if (error && !data) {
    return (
      <div className="sh-home">
        <div className="sh-home-error">
          <p className="sh-home-error-text">Could not load home intelligence</p>
          <p className="sh-home-error-detail">{error}</p>
          <button className="sh-home-error-retry" onClick={load}>Retry</button>
        </div>
      </div>
    );
  }

  // ── No data state ──
  if (!data) {
    return (
      <div className="sh-home">
        <div className="sh-home-empty">
          <div className="sh-home-empty-brand">शून्य</div>
          <p className="sh-home-empty-text">Welcome to SHUNYA. Your home intelligence will populate as data is created.</p>
        </div>
      </div>
    );
  }

  // ── Derive display items ──
  const criticalItems = data.intelligence.filter(i => i.priority === 'critical');
  const highItems = data.intelligence.filter(i => i.priority === 'high');
  const normalItems = data.intelligence.filter(i => i.priority === 'normal');

  // Split suggestions: items with actionable suggestions
  const suggestions = data.intelligence.filter(i => i.suggested_action || i.reason).slice(0, 5);

  return (
    <div className="sh-home">
      {/* Time greeting */}
      <TimeGreeting period={data.now.time_period} />

      {/* AI Presence */}
      <ShunyaAIPresence
        summary={data.ai_summary}
        focus={data.ai_focus}
        suggestion={data.ai_suggestion}
      />

      {/* A. NOW — immediate present */}
      <NowSummary
        hasImmediate={data.now.has_immediate}
        immediateCount={data.now.immediate_count}
        summary={data.now.summary}
        calm={data.calm}
      />

      {/* Critical items (highest priority) */}
      <HomeSection
        label="Needs attention"
        count={criticalItems.length}
        items={criticalItems}
        onOpenItem={handleOpenItem}
        defaultExpanded={true}
      />

      {/* High priority items */}
      <HomeSection
        label="Should review"
        count={highItems.length}
        items={highItems}
        onOpenItem={handleOpenItem}
        defaultExpanded={true}
      />

      {/* B. SHUNYA Suggestions */}
      {suggestions.length > 0 && (
        <HomeSection
          label="Suggestions"
          items={suggestions}
          onOpenItem={handleOpenItem}
          defaultExpanded={false}
        />
      )}

      {/* C. What Changed */}
      {data.changed.count > 0 && (
        <HomeSection
          label="What changed"
          count={data.changed.count}
          items={data.changed.items}
          onOpenItem={handleOpenItem}
          defaultExpanded={false}
        />
      )}

      {/* D. Active Commitments */}
      {(data.commitments.overdue_count > 0 || data.commitments.upcoming_count > 0) && (
        <HomeSection
          label="Commitments"
          count={data.commitments.overdue_count + data.commitments.upcoming_count}
          items={data.commitments.items}
          onOpenItem={handleOpenItem}
          defaultExpanded={false}
        />
      )}

      {/* E. Tasks */}
      {data.tasks.count > 0 && (
        <HomeSection
          label="Tasks"
          count={data.tasks.count}
          items={data.tasks.items}
          onOpenItem={handleOpenItem}
          defaultExpanded={false}
        />
      )}

      {/* F. SHUNYA Work */}
      <ShunyaWorkSection items={data.shunya_work.items} />

      {/* Normal priority items (progressive disclosure) */}
      {normalItems.length > 0 && (
        <HomeSection
          label="Other updates"
          count={normalItems.length}
          items={normalItems.slice(0, 8)}
          onOpenItem={handleOpenItem}
          defaultExpanded={false}
        />
      )}

      {/* Updated timestamp */}
      <div className="sh-home-updated">
        Updated {timeAgo(data.synthesized_at)}
      </div>

      <style>{shunyaHomeStyles}</style>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────────

const shunyaHomeStyles = `
/* ── Base ── */
.sh-home {
  padding: 48px 56px;
  max-width: 720px;
  min-height: 100%;
}

/* 70% whitespace: generous padding, max-width, light spacing */

/* ── Loading ── */
.sh-home-loading {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 80px 40px; gap: 16px;
}
.sh-home-loading-brand {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 24px; color: var(--shunya-text, #1A1C1D);
  letter-spacing: 0.06em;
}
.sh-home-loading-text {
  color: rgba(26,28,29,0.45); font-size: 14px;
}

/* ── Error ── */
.sh-home-error {
  padding: 60px 40px; text-align: center;
}
.sh-home-error-text { color: #c0392b; font-size: 15px; margin-bottom: 8px; }
.sh-home-error-detail { color: rgba(26,28,29,0.45); font-size: 13px; margin-bottom: 16px; }
.sh-home-error-retry {
  padding: 8px 20px; background: var(--shunya-surface, #fff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.1));
  border-radius: 8px; cursor: pointer; font-size: 13px;
}
.sh-home-error-retry:hover { background: rgba(26,28,29,0.03); }

/* ── Empty ── */
.sh-home-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 80px 40px; gap: 16px;
}
.sh-home-empty-brand {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 28px; color: var(--shunya-text, #1A1C1D);
  letter-spacing: 0.06em;
}
.sh-home-empty-text {
  color: rgba(26,28,29,0.55); font-size: 14px; text-align: center;
  line-height: 1.5;
}

/* ── Greeting ── */
.sh-home-greeting {
  margin-bottom: 24px;
}
.sh-home-greeting-text {
  font-size: 12px; font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  letter-spacing: 0.12em; text-transform: uppercase;
  opacity: 0.6;
}

/* ── AI Presence ── */
.sh-home-ai-presence {
  display: flex; gap: 12px;
  align-items: flex-start;
  margin-bottom: 28px;
  padding: 16px 20px;
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.06));
  border-radius: 12px;
}
.sh-home-ai-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--shunya-gold, #A4865F);
  flex-shrink: 0; margin-top: 6px;
}
.sh-home-ai-content {
  display: flex; flex-direction: column; gap: 6px;
}
.sh-home-ai-summary {
  font-size: 15px; font-weight: 450;
  color: var(--shunya-text, #1A1C1D);
  line-height: 1.5; margin: 0;
}
.sh-home-ai-focus {
  font-size: 13px; color: var(--shunya-gold, #A4865F);
  margin: 0;
}
.sh-home-ai-suggestion {
  font-size: 14px; color: rgba(26,28,29,0.7);
  line-height: 1.5; margin: 0;
}

/* ── Now Summary ── */
.sh-home-now {
  margin-bottom: 32px;
}
.sh-home-now-badge {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 8px;
}
.sh-home-now-attention {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(192, 57, 43, 0.08);
  color: #c0392b;
  font-size: 12px; font-weight: 600;
  border-radius: 20px;
  letter-spacing: 0.03em;
}
.sh-home-now-calm {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(106, 159, 106, 0.1);
  color: #4a7a4a;
  font-size: 12px; font-weight: 600;
  border-radius: 20px;
  letter-spacing: 0.03em;
}
.sh-home-now-summary {
  font-size: 14px; color: rgba(26,28,29,0.6);
  line-height: 1.5; margin: 0;
}

/* ── Calm State ── */
.sh-home-calm {
  padding: 40px 0;
  text-align: center;
  display: flex; flex-direction: column;
  align-items: center; gap: 12px;
}
.sh-home-calm-brand {
  font-family: var(--shunya-font-devanagari, 'Noto Sans Devanagari', serif);
  font-size: 20px; color: var(--shunya-text, #1A1C1D);
  letter-spacing: 0.06em; opacity: 0.5;
}
.sh-home-calm-text {
  color: rgba(26,28,29,0.55); font-size: 15px;
  line-height: 1.6; max-width: 480px; margin: 0;
}
.sh-home-calm-hint {
  color: rgba(26,28,29,0.35); font-size: 13px; margin: 0;
}

/* ── Sections ── */
.sh-home-section {
  margin-bottom: 16px;
}
.sh-home-section-header {
  display: flex; align-items: center; justify-content: space-between;
  width: 100%; padding: 10px 0;
  background: none; border: none; cursor: pointer;
  color: rgba(26,28,29,0.5);
  font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
  font-family: inherit;
}
.sh-home-section-header:hover { color: rgba(26,28,29,0.7); }
.sh-home-section-label { display: flex; align-items: center; gap: 8px; }
.sh-home-section-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px;
  background: rgba(26,28,29,0.06); border-radius: 9px;
  font-size: 10px; font-weight: 600;
}
.sh-home-section-toggle { font-size: 9px; }
.sh-home-section-items {
  display: flex; flex-direction: column; gap: 4px;
  overflow: hidden;
}

/* ── Item Row ── */
.sh-home-item {
  padding: 12px 16px;
  border-radius: 10px;
  transition: background 0.15s;
}
.sh-home-item:hover { background: rgba(26,28,29,0.02); }
.sh-home-item-critical { border-left: 3px solid #c0392b; }
.sh-home-item-high { border-left: 3px solid #e67e22; }
.sh-home-item-normal { border-left: 3px solid transparent; }
.sh-home-item-low { border-left: 3px solid transparent; }
.sh-home-item-row {
  display: flex; gap: 12px;
  align-items: flex-start;
}
.sh-home-item-body { flex: 1; min-width: 0; }
.sh-home-item-head {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 4px;
}
.sh-home-item-type {
  font-size: 10px; font-weight: 600;
  color: rgba(26,28,29,0.4);
  text-transform: uppercase; letter-spacing: 0.05em;
}
.sh-home-item-time {
  font-size: 10px; color: rgba(26,28,29,0.35);
}
.sh-home-item-title {
  font-size: 14px; font-weight: 450;
  color: var(--shunya-text, #1A1C1D);
  margin: 0; line-height: 1.4;
}
.sh-home-item-reason {
  font-size: 13px; color: rgba(26,28,29,0.6);
  margin: 4px 0 0; line-height: 1.4;
}
.sh-home-item-action {
  font-size: 12px; color: var(--shunya-gold, #A4865F);
  margin: 4px 0 0;
}
.sh-home-item-owner {
  font-size: 11px; color: rgba(26,28,29,0.35);
  margin: 4px 0 0;
}
.sh-home-item-actions {
  display: flex; gap: 4px;
  flex-shrink: 0;
}
.sh-home-item-act {
  width: 28px; height: 28px; border-radius: 6px;
  border: none; background: none; cursor: pointer;
  font-size: 12px; color: rgba(26,28,29,0.3);
  display: flex; align-items: center; justify-content: center;
}
.sh-home-item-act:hover { background: rgba(26,28,29,0.05); color: rgba(26,28,29,0.6); }

/* ── Priority Icon ── */
.sh-priority-icon {
  font-size: 10px; line-height: 1;
  margin-top: 4px; flex-shrink: 0;
}
.sh-priority-icon[data-priority="critical"] { color: #c0392b; }
.sh-priority-icon[data-priority="high"] { color: #e67e22; }
.sh-priority-icon[data-priority="normal"] { color: rgba(26,28,29,0.3); }
.sh-priority-icon[data-priority="low"] { color: rgba(26,28,29,0.15); }

/* ── SHUNYA Work ── */
.sh-home-work-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px;
}
.sh-home-work-status { font-size: 12px; flex-shrink: 0; }
.sh-home-work-running .sh-home-work-status { color: var(--shunya-gold, #A4865F); }
.sh-home-work-done .sh-home-work-status { color: #6a9f6a; }
.sh-home-work-body { flex: 1; min-width: 0; }
.sh-home-work-label {
  font-size: 13px; color: var(--shunya-text, #1A1C1D);
  display: block; margin-bottom: 4px;
}
.sh-home-work-time {
  font-size: 11px; color: rgba(26,28,29,0.35);
}
.sh-home-work-track {
  height: 3px; background: rgba(26,28,29,0.06);
  border-radius: 2px; overflow: hidden;
}
.sh-home-work-fill {
  height: 100%; background: var(--shunya-gold, #A4865F);
  border-radius: 2px; transition: width 0.5s ease;
}
.sh-home-work-badge {
  font-size: 10px; font-weight: 600;
  padding: 2px 8px; border-radius: 10px;
  background: rgba(164, 134, 95, 0.1);
  color: var(--shunya-gold, #A4865F);
}
.sh-home-work-badge-done {
  background: rgba(106, 159, 106, 0.1);
  color: #4a7a4a;
}

/* ── Explain Modal ── */
.sh-explain-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.2);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.sh-explain-card {
  background: var(--shunya-surface, #fff);
  border-radius: 16px; padding: 28px;
  max-width: 440px; width: 100%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
}
.sh-explain-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 20px;
}
.sh-explain-title {
  font-size: 16px; font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
}
.sh-explain-close {
  background: none; border: none; cursor: pointer;
  font-size: 16px; color: rgba(26,28,29,0.3);
  padding: 4px;
}
.sh-explain-item {
  margin-bottom: 16px;
}
.sh-explain-type {
  font-size: 10px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: rgba(26,28,29,0.4);
  display: block; margin-bottom: 4px;
}
.sh-explain-name {
  font-size: 14px; font-weight: 450;
  color: var(--shunya-text, #1A1C1D);
}
.sh-explain-loading {
  font-size: 13px; color: rgba(26,28,29,0.45);
  padding: 12px 0;
}
.sh-explain-evidence {
  margin: 16px 0;
  display: flex; flex-direction: column; gap: 8px;
}
.sh-explain-evidence-item {
  display: flex; gap: 8px;
  font-size: 13px; color: rgba(26,28,29,0.65);
  line-height: 1.4;
}
.sh-explain-evidence-bullet { color: var(--shunya-gold, #A4865F); flex-shrink: 0; }
.sh-explain-no-evidence {
  font-size: 13px; color: rgba(26,28,29,0.45);
  font-style: italic;
}
.sh-explain-confidence {
  font-size: 12px; color: rgba(26,28,29,0.45);
  margin-bottom: 16px;
}
.sh-explain-confidence-badge {
  display: inline-block; padding: 1px 8px;
  border-radius: 8px; font-size: 10px; font-weight: 600;
  text-transform: uppercase;
}
.sh-explain-confidence-badge.deterministic {
  background: rgba(106, 159, 106, 0.1); color: #4a7a4a;
}
.sh-explain-confidence-badge.inference {
  background: rgba(230, 126, 34, 0.1); color: #d35400;
}
.sh-explain-btn {
  width: 100%; padding: 10px;
  background: rgba(26,28,29,0.03);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.08));
  border-radius: 8px; cursor: pointer;
  font-size: 13px; font-family: inherit;
  color: var(--shunya-text, #1A1C1D);
}
.sh-explain-btn:hover { background: rgba(26,28,29,0.06); }

/* ── Action Menu ── */
.sh-action-menu-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.15);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.sh-action-menu {
  background: var(--shunya-surface, #fff);
  border-radius: 14px; padding: 8px;
  max-width: 280px; width: 100%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  display: flex; flex-direction: column; gap: 2px;
}
.sh-action-btn {
  width: 100%; padding: 10px 16px;
  background: none; border: none; cursor: pointer;
  text-align: left; font-size: 13px;
  border-radius: 8px; font-family: inherit;
  color: var(--shunya-text, #1A1C1D);
}
.sh-action-btn:hover { background: rgba(26,28,29,0.04); }
.sh-action-btn-cancel {
  border-top: 1px solid var(--shunya-border, rgba(26,28,29,0.06));
  margin-top: 4px; border-radius: 0;
  color: rgba(26,28,29,0.45);
}
.sh-action-btn-cancel:hover { color: var(--shunya-text, #1A1C1D); }

/* ── Updated ── */
.sh-home-updated {
  margin-top: 40px;
  font-size: 10px; color: rgba(26,28,29,0.2);
  text-align: center;
}

/* ── Mobile ── */
@media (max-width: 640px) {
  .sh-home { padding: 28px 20px; }
  .sh-home-section { margin-bottom: 12px; }
  .sh-home-item { padding: 12px; }
  .sh-explain-card { margin: 0 12px; }
}
`;