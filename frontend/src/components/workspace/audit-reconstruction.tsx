/**
 * AuditReconstruction — FDA21 audit reconstruction panel.
 *
 * Integrates into the existing ObjectWorkspaceViewer as a card section.
 * Calls the real authenticated backend endpoint:
 *   GET /api/v1/audit/reconstruct/<type>/<id>
 *
 * Handles all required states: loading, empty, unauthorized, not found,
 * success, partial/missing evidence, server failure, retry.
 */
import { useState, useEffect, useCallback } from 'react';
import type { FC } from 'react';

/* ── Types ───────────────────────────────────────────────────── */

interface AuditDecision {
  main_decision?: { action?: string; reason?: string; confidence?: number };
  final_decision?: { action?: string; approved_by?: string };
  execution_status?: string;
  source?: string;
  confidence?: number;
  created_at?: string;
}

interface AuditEvidence {
  source_type?: string;
  description?: string;
  raw_reference?: Record<string, unknown>;
  created_at?: string;
}

interface AuditExecution {
  intention?: string;
  stage?: string;
  identity_id?: string;
  steps?: Array<{ action: string; type: string; success: boolean }>;
  created_at?: string;
}

interface AuditTimelineEntry {
  event_type?: string;
  event_time?: string;
  title?: string;
  description?: string;
  created_by?: string;
}

interface AuditApproval {
  identity_id?: string;
  action?: string;
  resource_type?: string;
  basis?: string;
  timestamp?: string;
}

interface AuditReconstructionData {
  reconstructed_at: string;
  object_type: string;
  object_id: number;
  what_happened: string | null;
  who_caused_it: string[] | string | null;
  when_it_happened: string | null;
  why_it_happened: string | null;
  what_information_supported_it: Array<Record<string, unknown>> | null;
  who_approved_it: string | null;
  what_shunya_executed: string | null;
  what_actually_succeeded: string | null;
  what_evidence_proves_it: Array<{ source_type: string; description: string }> | null;
  timeline: AuditTimelineEntry[];
  decisions: AuditDecision[];
  approvals: AuditApproval[];
  executions: AuditExecution[];
  evidence_chain: AuditEvidence[];
  provenance: string;
  confidence: string;
}

interface AuditResponse {
  success: boolean;
  data?: AuditReconstructionData;
  error?: string;
}

/* ── Constants ────────────────────────────────────────────────── */

const accentColor = '#6C4AE2';
const bgColor = '#FAF8F5';

/* ── Helpers ─────────────────────────────────────────────────── */

function formatTime(iso: string | undefined | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

function confidenceColor(confidence: string | undefined): string {
  if (!confidence) return '#9CA3AF';
  const c = confidence.toLowerCase();
  if (c === 'high') return '#16A34A';
  if (c === 'medium') return '#F59E0B';
  if (c === 'low') return '#EF4444';
  return '#9CA3AF';
}

/* ── Sub-components ──────────────────────────────────────────── */

function AuditSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="ar-section">
      <div className="ar-section-label">{label}</div>
      <div className="ar-section-value">{children}</div>
    </div>
  );
}

function AuditTimeline({ events }: { events: AuditTimelineEntry[] }) {
  if (events.length === 0) return null;
  return (
    <div className="ar-card">
      <div className="ar-card-title">Timeline ({events.length})</div>
      <div className="ar-timeline">
        {events.map((e, i) => (
          <div key={i} className="ar-timeline-item">
            <div className="ar-timeline-dot" />
            <div className="ar-timeline-content">
              <div className="ar-timeline-title">{e.title || e.event_type || 'Event'}</div>
              {e.description && <div className="ar-timeline-desc">{e.description}</div>}
              <div className="ar-timeline-meta">
                <span>{formatTime(e.event_time)}</span>
                {e.created_by && <span> · {e.created_by}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AuditDecisions({ decisions }: { decisions: AuditDecision[] }) {
  if (decisions.length === 0) return null;
  return (
    <div className="ar-card">
      <div className="ar-card-title">Decisions ({decisions.length})</div>
      {decisions.map((d, i) => (
        <div key={i} className="ar-decision-item">
          <div className="ar-decision-header">
            <span className="ar-decision-action">
              {d.main_decision?.action || d.final_decision?.action || 'Decision'}
            </span>
            <span className={`ar-decision-status ar-status-${d.execution_status || 'unknown'}`}>
              {d.execution_status || 'unknown'}
            </span>
          </div>
          {d.main_decision?.reason && (
            <div className="ar-decision-reason">{d.main_decision.reason}</div>
          )}
          <div className="ar-decision-meta">
            {d.source && <span>Source: {d.source}</span>}
            {d.confidence !== undefined && (
              <span>Confidence: {Math.round(d.confidence * 100)}%</span>
            )}
            {d.created_at && <span>{formatTime(d.created_at)}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

function AuditApprovalsList({ approvals }: { approvals: AuditApproval[] }) {
  if (approvals.length === 0) return null;
  return (
    <div className="ar-card">
      <div className="ar-card-title">Approvals ({approvals.length})</div>
      {approvals.map((a, i) => (
        <div key={i} className="ar-approval-item">
          <div className="ar-approval-header">
            <span className="ar-approval-action">{a.action}</span>
            <span className="ar-approval-actor">{a.identity_id || 'unknown'}</span>
          </div>
          {a.basis && <div className="ar-approval-basis">{a.basis}</div>}
          <div className="ar-approval-meta">{formatTime(a.timestamp)}</div>
        </div>
      ))}
    </div>
  );
}

function AuditExecutions({ executions }: { executions: AuditExecution[] }) {
  if (executions.length === 0) return null;
  return (
    <div className="ar-card">
      <div className="ar-card-title">Executions ({executions.length})</div>
      {executions.map((e, i) => (
        <div key={i} className="ar-execution-item">
          <div className="ar-execution-header">
            <span className="ar-execution-intent">{e.intention || 'Execution'}</span>
            <span className={`ar-execution-stage ar-stage-${e.stage || 'unknown'}`}>
              {e.stage || 'unknown'}
            </span>
          </div>
          {e.identity_id && <div className="ar-execution-actor">By: {e.identity_id}</div>}
          {e.steps && e.steps.length > 0 && (
            <div className="ar-execution-steps">
              {e.steps.map((s, j) => (
                <span key={j} className={`ar-step-badge ar-step-${s.success ? 'ok' : 'fail'}`}>
                  {s.action}
                </span>
              ))}
            </div>
          )}
          {e.created_at && <div className="ar-execution-meta">{formatTime(e.created_at)}</div>}
        </div>
      ))}
    </div>
  );
}

function AuditEvidenceChain({ evidence }: { evidence: AuditEvidence[] }) {
  if (evidence.length === 0) return null;
  return (
    <div className="ar-card">
      <div className="ar-card-title">Evidence Chain ({evidence.length})</div>
      {evidence.map((e, i) => (
        <div key={i} className="ar-evidence-item">
          <div className="ar-evidence-type">{e.source_type || 'evidence'}</div>
          {e.description && <div className="ar-evidence-desc">{e.description}</div>}
          {e.created_at && <div className="ar-evidence-meta">{formatTime(e.created_at)}</div>}
        </div>
      ))}
    </div>
  );
}

/* ── Main Component ──────────────────────────────────────────── */

interface Props {
  objectId: string;
  objectType?: string;
}

export const AuditReconstruction: FC<Props> = ({ objectId, objectType }) => {
  const [data, setData] = useState<AuditReconstructionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusCode, setStatusCode] = useState<number | null>(null);

  const fetchReconstruction = useCallback(async () => {
    setLoading(true);
    setError(null);
    setStatusCode(null);
    const type = objectType || 'lead';
    try {
      const r = await fetch(`/api/v1/audit/reconstruct/${type}/${objectId}`, {
        credentials: 'include',
      });
      setStatusCode(r.status);
      const body: AuditResponse = await r.json().catch(() => ({
        success: false, error: `HTTP ${r.status}`,
      }));
      if (r.status === 401) {
        setError('Authentication required. Please sign in to view audit reconstruction.');
      } else if (r.status === 404) {
        setError('Object not found. The requested object could not be resolved.');
      } else if (!body.success) {
        setError(body.error || `Reconstruction failed (HTTP ${r.status})`);
      } else if (body.data) {
        setData(body.data);
      } else {
        setError('No reconstruction data available.');
      }
    } catch (err: any) {
      setError(err.message || 'Network error — could not reach the server.');
    } finally {
      setLoading(false);
    }
  }, [objectId, objectType]);

  useEffect(() => {
    fetchReconstruction();
  }, [fetchReconstruction]);

  /* ── Loading state ─────────────────────────────────────────── */
  if (loading) {
    return (
      <div className="ar-card" role="region" aria-label="Audit reconstruction loading">
        <div className="ar-card-title">Audit Trail</div>
        <div className="ar-loading" role="status" aria-live="polite">
          <div className="ar-spinner" />
          <span className="ar-loading-text">Reconstructing audit trail…</span>
        </div>
        <style>{arStyles}</style>
      </div>
    );
  }

  /* ── Error state ───────────────────────────────────────────── */
  if (error) {
    const isUnauthorized = statusCode === 401 || error.includes('Authentication');
    const isNotFound = statusCode === 404 || error.includes('not found');
    const isServerError = statusCode && statusCode >= 500;
    return (
      <div className="ar-card" role="alert" aria-label="Audit reconstruction error">
        <div className="ar-card-title">Audit Trail</div>
        <div className={`ar-error ar-error-${isUnauthorized ? 'auth' : isNotFound ? 'notfound' : 'server'}`}>
          <div className="ar-error-icon">
            {isUnauthorized ? '🔒' : isNotFound ? '🔍' : '⚠️'}
          </div>
          <div className="ar-error-title">
            {isUnauthorized ? 'Authentication Required' :
             isNotFound ? 'Object Not Found' :
             isServerError ? 'Server Error' : 'Reconstruction Failed'}
          </div>
          <div className="ar-error-message">{error}</div>
          <button className="ar-retry-btn" onClick={fetchReconstruction}>
            Retry
          </button>
        </div>
        <style>{arStyles}</style>
      </div>
    );
  }

  /* ── Empty state ───────────────────────────────────────────── */
  if (!data) {
    return (
      <div className="ar-card" role="region" aria-label="Audit reconstruction empty">
        <div className="ar-card-title">Audit Trail</div>
        <div className="ar-empty">
          <div className="ar-empty-text">No audit data available for this object.</div>
        </div>
        <style>{arStyles}</style>
      </div>
    );
  }

  /* ── Reconstruction success ───────────────────────────────── */
  const hasDecisions = data.decisions && data.decisions.length > 0;
  const hasApprovals = data.approvals && data.approvals.length > 0;
  const hasExecutions = data.executions && data.executions.length > 0;
  const hasEvidence = data.evidence_chain && data.evidence_chain.length > 0;
  const hasTimeline = data.timeline && data.timeline.length > 0;
  const isPartial = !hasDecisions || !hasApprovals || !hasExecutions || !hasEvidence;

  return (
    <div className="ar-card" role="region" aria-label="Audit reconstruction">
      <div className="ar-card-header">
        <div className="ar-card-title">Audit Trail</div>
        <div className="ar-card-meta">
          <span className="ar-confidence" style={{ color: confidenceColor(data.confidence) }}>
            {data.confidence} confidence
          </span>
          <span className="ar-timestamp">{formatTime(data.reconstructed_at)}</span>
        </div>
      </div>

      {isPartial && (
        <div className="ar-partial-banner" role="status">
          Partial reconstruction — some data sources have no records for this object.
        </div>
      )}

      {/* WHAT / WHO / WHEN / WHY */}
      <div className="ar-summary-grid">
        {data.what_happened && (
          <AuditSection label="What happened">
            <span className="ar-what-text">{data.what_happened}</span>
          </AuditSection>
        )}
        {data.who_caused_it && (
          <AuditSection label="Who initiated">
            <span>{Array.isArray(data.who_caused_it) ? data.who_caused_it.join(', ') : data.who_caused_it}</span>
          </AuditSection>
        )}
        {data.when_it_happened && (
          <AuditSection label="When">
            <span>{formatTime(data.when_it_happened)}</span>
          </AuditSection>
        )}
        {data.why_it_happened && (
          <AuditSection label="Why">
            <span>{data.why_it_happened}</span>
          </AuditSection>
        )}
        {data.who_approved_it && (
          <AuditSection label="Approved by">
            <span>{data.who_approved_it}</span>
          </AuditSection>
        )}
        {data.what_shunya_executed && (
          <AuditSection label="Execution">
            <span>{data.what_shunya_executed}</span>
            <span className={`ar-status-badge ar-status-${data.what_actually_succeeded || 'unknown'}`}>
              {data.what_actually_succeeded || 'unknown'}
            </span>
          </AuditSection>
        )}
      </div>

      {/* Evidence summary */}
      {data.what_evidence_proves_it && data.what_evidence_proves_it.length > 0 && (
        <div className="ar-card">
          <div className="ar-card-title">Evidence Summary</div>
          {data.what_evidence_proves_it.map((e, i) => (
            <div key={i} className="ar-evidence-summary-item">
              <span className="ar-evidence-summary-type">{e.source_type}</span>
              <span className="ar-evidence-summary-desc">{e.description}</span>
            </div>
          ))}
        </div>
      )}

      {/* Detailed sections */}
      {hasTimeline && <AuditTimeline events={data.timeline!} />}
      {hasDecisions && <AuditDecisions decisions={data.decisions!} />}
      {hasApprovals && <AuditApprovalsList approvals={data.approvals!} />}
      {hasExecutions && <AuditExecutions executions={data.executions!} />}
      {hasEvidence && <AuditEvidenceChain evidence={data.evidence_chain!} />}

      {/* Provenance */}
      <div className="ar-provenance">
        <span className="ar-provenance-label">Provenance:</span>
        <span className="ar-provenance-value">{data.provenance}</span>
      </div>

      <style>{arStyles}</style>
    </div>
  );
};

/* ── Styles ──────────────────────────────────────────────────── */

const arStyles = `
.ar-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(255,255,255,0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.8);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 8px 32px rgba(108,74,226,0.06);
  transition: box-shadow 0.2s;
}
.ar-card:hover {
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 8px 40px rgba(108,74,226,0.1);
}
.ar-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}
.ar-card-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6B7280;
}
.ar-card-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 10px;
  color: #9CA3AF;
}
.ar-confidence {
  font-weight: 600;
  text-transform: capitalize;
}
.ar-timestamp {
  color: #9CA3AF;
}
.ar-partial-banner {
  font-size: 12px;
  color: #B45309;
  background: rgba(245,158,11,0.08);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: 8px;
  padding: 8px 12px;
}
.ar-summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
@media (max-width: 640px) {
  .ar-summary-grid { grid-template-columns: 1fr; }
}
.ar-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 8px;
  background: ${bgColor};
  border-radius: 8px;
}
.ar-section-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #9CA3AF;
}
.ar-section-value {
  font-size: 13px;
  color: #1A1C1D;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.ar-what-text {
  font-weight: 600;
  font-size: 14px;
}
.ar-status-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: capitalize;
}
.ar-status-completed { background: rgba(22,163,74,0.1); color: #16A34A; }
.ar-status-incomplete, .ar-status-unknown { background: rgba(239,68,68,0.1); color: #EF4444; }

/* Loading */
.ar-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 24px 0;
  justify-content: center;
}
.ar-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(108,74,226,0.2);
  border-top-color: ${accentColor};
  border-radius: 50%;
  animation: ar-spin 0.6s linear infinite;
}
@keyframes ar-spin { to { transform: rotate(360deg); } }
.ar-loading-text {
  font-size: 13px;
  color: #6B7280;
}

/* Error */
.ar-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  text-align: center;
}
.ar-error-icon { font-size: 24px; }
.ar-error-title {
  font-size: 14px;
  font-weight: 600;
  color: #1A1C1D;
}
.ar-error-message {
  font-size: 12px;
  color: #6B7280;
  max-width: 300px;
}
.ar-retry-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border: 1px solid rgba(108,74,226,0.2);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  background: ${accentColor};
  color: white;
  font-family: inherit;
  transition: all 0.2s;
}
.ar-retry-btn:hover {
  background: #5B3DD4;
}
.ar-retry-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Empty */
.ar-empty {
  padding: 24px 0;
  text-align: center;
}
.ar-empty-text {
  font-size: 13px;
  color: #9CA3AF;
}

/* Timeline */
.ar-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
  padding-left: 20px;
}
.ar-timeline::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: rgba(108,74,226,0.15);
  border-radius: 1px;
}
.ar-timeline-item {
  position: relative;
  padding: 6px 0 6px 12px;
}
.ar-timeline-dot {
  position: absolute;
  left: -16px;
  top: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${accentColor};
  border: 2px solid ${bgColor};
}
.ar-timeline-title {
  font-size: 13px;
  font-weight: 500;
  color: #1A1C1D;
}
.ar-timeline-desc {
  font-size: 12px;
  color: #6B7280;
  margin-top: 2px;
}
.ar-timeline-meta {
  font-size: 10px;
  color: #9CA3AF;
  margin-top: 2px;
}

/* Decisions */
.ar-decision-item {
  padding: 8px;
  background: ${bgColor};
  border-radius: 8px;
}
.ar-decision-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.ar-decision-action {
  font-size: 13px;
  font-weight: 500;
  color: #1A1C1D;
}
.ar-decision-status {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: capitalize;
}
.ar-status-completed { background: rgba(22,163,74,0.1); color: #16A34A; }
.ar-status-rejected { background: rgba(239,68,68,0.1); color: #EF4444; }
.ar-status-unknown { background: rgba(156,163,175,0.1); color: #6B7280; }
.ar-decision-reason {
  font-size: 12px;
  color: #6B7280;
  margin-top: 4px;
}
.ar-decision-meta {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: #9CA3AF;
  margin-top: 4px;
}

/* Approvals */
.ar-approval-item {
  padding: 8px;
  background: ${bgColor};
  border-radius: 8px;
}
.ar-approval-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.ar-approval-action {
  font-size: 13px;
  font-weight: 500;
  text-transform: capitalize;
  color: #1A1C1D;
}
.ar-approval-actor {
  font-size: 11px;
  color: ${accentColor};
}
.ar-approval-basis {
  font-size: 12px;
  color: #6B7280;
  margin-top: 4px;
}
.ar-approval-meta {
  font-size: 10px;
  color: #9CA3AF;
  margin-top: 2px;
}

/* Executions */
.ar-execution-item {
  padding: 8px;
  background: ${bgColor};
  border-radius: 8px;
}
.ar-execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.ar-execution-intent {
  font-size: 13px;
  font-weight: 500;
  color: #1A1C1D;
}
.ar-execution-stage {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  text-transform: capitalize;
}
.ar-stage-completed { background: rgba(22,163,74,0.1); color: #16A34A; }
.ar-stage-in_progress { background: rgba(59,130,246,0.1); color: #3B82F6; }
.ar-stage-failed { background: rgba(239,68,68,0.1); color: #EF4444; }
.ar-stage-unknown { background: rgba(156,163,175,0.1); color: #6B7280; }
.ar-execution-actor {
  font-size: 11px;
  color: #6B7280;
  margin-top: 4px;
}
.ar-execution-steps {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.ar-step-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}
.ar-step-ok { background: rgba(22,163,74,0.08); color: #16A34A; }
.ar-step-fail { background: rgba(239,68,68,0.08); color: #EF4444; }
.ar-execution-meta {
  font-size: 10px;
  color: #9CA3AF;
  margin-top: 4px;
}

/* Evidence */
.ar-evidence-item {
  padding: 8px;
  background: ${bgColor};
  border-radius: 8px;
}
.ar-evidence-type {
  font-size: 12px;
  font-weight: 600;
  color: ${accentColor};
  text-transform: capitalize;
}
.ar-evidence-desc {
  font-size: 12px;
  color: #6B7280;
  margin-top: 2px;
}
.ar-evidence-meta {
  font-size: 10px;
  color: #9CA3AF;
  margin-top: 2px;
}

/* Evidence summary */
.ar-evidence-summary-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 4px 0;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}
.ar-evidence-summary-item:last-child {
  border-bottom: none;
}
.ar-evidence-summary-type {
  font-size: 11px;
  font-weight: 600;
  color: ${accentColor};
  text-transform: capitalize;
  flex-shrink: 0;
}
.ar-evidence-summary-desc {
  font-size: 11px;
  color: #6B7280;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Provenance */
.ar-provenance {
  display: flex;
  gap: 4px;
  font-size: 10px;
  color: #9CA3AF;
  padding-top: 8px;
  border-top: 1px solid rgba(0,0,0,0.04);
}
.ar-provenance-label {
  font-weight: 600;
}
.ar-provenance-value {
  color: #9CA3AF;
}
`;