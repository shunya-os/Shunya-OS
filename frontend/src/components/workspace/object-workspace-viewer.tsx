/**
 * FDA16 — Object Workspace Viewer
 *
 * Renders the unified workspace for any object.
 * Object-type-agnostic — driven by data from the backend API.
 */
import { useState, useEffect, type FC } from 'react';
import { getObjectWorkspace } from '../../api/workspace-api';
import { CopilotPanel } from './copilot-panel';
import { TimelineView } from './timeline-view';
import { CommitmentPanel } from './commitment-panel';
import { AuditReconstruction } from './audit-reconstruction';

interface Props {
  objectId: string;
  objectType?: string;
}

function IdentityCard({ data }: { data: any }) {
  return (
    <div className="wksp-card wksp-card-identity">
      <div className="wksp-card-title">Identity</div>
      <div className="wksp-card-body">
        <div className="wksp-identity-row">
          <span className="wksp-id-name">{data.name || 'Unknown'}</span>
          <span className="wksp-id-type">{data.object_type}</span>
          <span className={`wksp-id-status wksp-status-${data.status || 'unknown'}`}>{data.status || 'unknown'}</span>
        </div>
        <div className="wksp-identity-meta">
          {data.created_at && <span>Created: {new Date(data.created_at).toLocaleDateString()}</span>}
        </div>
      </div>
    </div>
  );
}

function ContextCard({ data }: { data: any }) {
  const type = data.type;
  if (!data || !type) return null;

  return (
    <div className="wksp-card wksp-card-context">
      <div className="wksp-card-title">Details</div>
      <div className="wksp-card-body wksp-context-grid">
        {Object.entries(data).filter(([k]) => k !== 'type' && k !== 'relationship_id' && k !== 'campaign_id').map(([key, val]) => {
          if (!val && val !== 0) return null;
          const display = typeof val === 'object' ? JSON.stringify(val).slice(0, 100) : String(val);
          return (
            <div key={key} className="wksp-context-item">
              <span className="wksp-context-label">{key.replace(/_/g, ' ')}</span>
              <span className="wksp-context-value">{display}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ActionsBar({ actions, onAction }: { actions: any[]; onAction: (a: any) => void }) {
  if (!actions || actions.length === 0) return null;
  return (
    <div className="wksp-actions-bar">
      {actions.map((a) => (
        <button key={a.id} className="wksp-action-btn" onClick={() => onAction(a)}>
          <span>{a.icon}</span>
          <span>{a.label}</span>
        </button>
      ))}
    </div>
  );
}

function IntelligenceCard({ data }: { data: any }) {
  if (!data || Object.keys(data).length === 0) return null;
  return (
    <div className="wksp-card wksp-card-intel">
      <div className="wksp-card-title">SHUNYA Intelligence</div>
      <div className="wksp-card-body">
        {data.summary && <p className="wksp-intel-summary">{data.summary}</p>}
        <div className="wksp-intel-scores">
          <div className="wksp-intel-score">
            <span className="wksp-score-label">Health</span>
            <span className="wksp-score-val">{data.health_score ?? '—'}/100</span>
          </div>
          <div className="wksp-intel-score">
            <span className="wksp-score-label">Engagement</span>
            <span className="wksp-score-val">{data.engagement_score ?? '—'}/100</span>
          </div>
          <div className="wksp-intel-score">
            <span className="wksp-score-label">Retention Risk</span>
            <span className="wksp-score-val">{data.retention_risk ?? '—'}/100</span>
          </div>
          {data.lifetime_value > 0 && (
            <div className="wksp-intel-score">
              <span className="wksp-score-label">LTV</span>
              <span className="wksp-score-val">₹{(data.lifetime_value).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EvidenceList({ data }: { data: any[] }) {
  if (!data || data.length === 0) return null;
  return (
    <div className="wksp-card wksp-card-evidence">
      <div className="wksp-card-title">Evidence ({data.length})</div>
      <div className="wksp-card-body">
        {data.map((e, i) => (
          <div key={e.id || i} className="wksp-evidence-item">
            <span className="wksp-evidence-desc">{(e.description || e.evidence_type || '').slice(0, 120)}</span>
            <span className="wksp-evidence-confidence">{Math.round((e.confidence || 0) * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RelationshipList({ data }: { data: any[] }) {
  if (!data || data.length === 0) return null;
  return (
    <div className="wksp-card wksp-card-rels">
      <div className="wksp-card-title">Relationships</div>
      <div className="wksp-card-body">
        {data.map((r, i) => (
          <div key={r.id || i} className="wksp-rel-item">
            <span className="wksp-rel-name">{r.display_name || 'Unknown'}</span>
            <span className="wksp-rel-type">{r.relationship_type}</span>
            {r.email && <span className="wksp-rel-email">{r.email}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

export const ObjectWorkspaceViewer: FC<Props> = ({ objectId, objectType }) => {
  const [workspace, setWorkspace] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getObjectWorkspace(objectId, objectType).then((resp) => {
      if (cancelled) return;
      if (resp.success && resp.data) {
        setWorkspace(resp.data);
      } else {
        setError(resp.error || 'Failed to load workspace');
      }
    }).catch((err) => {
      if (!cancelled) setError(err.message);
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [objectId, objectType]);

  const handleAction = (action: any) => {
    console.log('Action:', action.id, action.label);
  };

  if (loading) {
    return (
      <div className="wksp-object-viewer wksp-loading">
        <div className="wksp-loading-shimmer" />
        <div className="wksp-loading-text">Loading workspace…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="wksp-object-viewer wksp-error" role="alert">
        <div className="wksp-error-icon">⚠</div>
        <div className="wksp-error-title">Could not load workspace</div>
        <div className="wksp-error-message">{error}</div>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="wksp-object-viewer wksp-empty">
        <div className="wksp-empty-text">No workspace data available.</div>
      </div>
    );
  }

  const sections = workspace.sections || [];
  const identity = workspace.identity || {};
  const context = workspace.context || {};
  const timeline = workspace.timeline || [];
  const commitments = workspace.commitments || [];
  const evidence = workspace.evidence || [];
  const relationships = workspace.relationships || [];
  const intelligence = workspace.intelligence || {};
  const actions = workspace.actions || [];
  const relationship_id = context.relationship_id || identity.relationship_id;

  return (
    <div className="wksp-object-viewer">
      <div className="wksp-object-layout">
        {/* Left column: Identity, Context, Intelligence */}
        <div className="wksp-object-left">
          {sections.includes('identity') && <IdentityCard data={identity} />}
          {sections.includes('context') && <ContextCard data={context} />}
          {sections.includes('intelligence') && <IntelligenceCard data={intelligence} />}
          {sections.includes('evidence') && <EvidenceList data={evidence} />}
          {sections.includes('relationships') && <RelationshipList data={relationships} />}
          {/* FDA21 — Audit reconstruction — always visible when object is loaded */}
          <AuditReconstruction objectId={objectId} objectType={objectType} />
        </div>

        {/* Center column: Timeline */}
        <div className="wksp-object-center">
          {sections.includes('actions') && (
            <ActionsBar actions={actions} onAction={handleAction} />
          )}
          {sections.includes('timeline') && (
            <TimelineView events={timeline} relationshipId={relationship_id} />
          )}
          {sections.includes('commitments') && (
            <CommitmentPanel commitments={commitments} relationshipId={relationship_id} />
          )}
        </div>

        {/* Right column: Copilot */}
        <div className="wksp-object-right">
          <CopilotPanel
            objectType={workspace.object_type}
            objectId={objectId}
            relationshipId={relationship_id}
          />
        </div>
      </div>

      <style>{`
.wksp-object-viewer { display: flex; flex-direction: column; flex: 1; padding: var(--shunya-spacing-md); gap: var(--shunya-spacing-md); overflow: auto; }
.wksp-object-layout { display: grid; grid-template-columns: 320px 1fr 320px; gap: var(--shunya-spacing-md); flex: 1; min-height: 0; }
@media (max-width: 1024px) { .wksp-object-layout { grid-template-columns: 1fr; } }
@media (max-width: 768px) {
  .wksp-object-viewer { padding: var(--shunya-spacing-sm); }
  .wksp-context-grid { grid-template-columns: 1fr; }
  .wksp-intel-scores { flex-direction: column; gap: 6px; }
}
@media (max-width: 480px) {
  .wksp-object-viewer { padding: 8px; }
  .wksp-card { padding: var(--shunya-spacing-sm); }
  .wksp-identity-row { flex-direction: column; align-items: flex-start; }
  .wksp-actions-bar { flex-direction: column; }
  .wksp-action-btn { width: 100%; justify-content: center; }
  .wksp-rel-item { flex-wrap: wrap; }
  .wksp-rel-email { margin-left: 0; }
}
.wksp-object-left, .wksp-object-center, .wksp-object-right { display: flex; flex-direction: column; gap: var(--shunya-spacing-sm); min-height: 0; }
.wksp-card { background: var(--shunya-surface-2, #1a1a26); border: 1px solid var(--shunya-surface-1, #22222e); border-radius: var(--shunya-radius-md, 8px); padding: var(--shunya-spacing-md); }
.wksp-card-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--shunya-text-secondary, #888); margin-bottom: var(--shunya-spacing-sm); }
.wksp-card-body { display: flex; flex-direction: column; gap: 6px; }
.wksp-identity-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.wksp-id-name { font-size: 16px; font-weight: 600; color: var(--shunya-text, #e0e0e0); }
.wksp-id-type { font-size: 11px; color: var(--shunya-text-secondary, #888); background: var(--shunya-surface-1, #22222e); padding: 2px 8px; border-radius: 4px; }
.wksp-id-status { font-size: 11px; padding: 2px 8px; border-radius: 4px; text-transform: capitalize; }
.wksp-status-active, .wksp-status-converted, .wksp-status-completed { background: rgba(16,185,129,0.15); color: #34d399; }
.wksp-status-pending, .wksp-status-new, .wksp-status-in_progress { background: rgba(245,166,35,0.15); color: #f5a623; }
.wksp-status-failed, .wksp-status-cancelled, .wksp-status-unknown { background: rgba(239,68,68,0.15); color: #f88; }
.wksp-identity-meta { font-size: 12px; color: var(--shunya-text-secondary, #888); }
.wksp-context-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
.wksp-context-item { display: flex; flex-direction: column; gap: 1px; }
.wksp-context-label { font-size: 10px; color: var(--shunya-text-secondary, #888); text-transform: capitalize; }
.wksp-context-value { font-size: 13px; color: var(--shunya-text, #e0e0e0); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wksp-actions-bar { display: flex; gap: 6px; flex-wrap: wrap; padding: 4px 0; }
.wksp-action-btn { display: flex; align-items: center; gap: 4px; padding: 6px 12px; background: var(--shunya-surface-2, #1a1a26); border: 1px solid var(--shunya-surface-1, #22222e); border-radius: 6px; color: var(--shunya-text, #e0e0e0); cursor: pointer; font-size: 13px; transition: background 0.15s; }
.wksp-action-btn:hover { background: var(--shunya-surface-3, #2a2a3a); }
.wksp-intel-scores { display: flex; gap: 12px; flex-wrap: wrap; }
.wksp-intel-score { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.wksp-score-label { font-size: 10px; color: var(--shunya-text-secondary, #888); }
.wksp-score-val { font-size: 14px; font-weight: 600; color: var(--shunya-text, #e0e0e0); }
.wksp-intel-summary { font-size: 13px; color: var(--shunya-text, #ccc); line-height: 1.5; margin-bottom: 8px; }
.wksp-evidence-item { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px solid var(--shunya-surface-1, #222); }
.wksp-evidence-desc { font-size: 12px; color: var(--shunya-text, #ccc); }
.wksp-evidence-confidence { font-size: 11px; color: var(--shunya-text-secondary, #888); }
.wksp-rel-item { display: flex; gap: 8px; align-items: center; padding: 4px 0; font-size: 13px; }
.wksp-rel-name { color: var(--shunya-text, #e0e0e0); }
.wksp-rel-type { font-size: 11px; color: var(--shunya-text-secondary, #888); }
.wksp-rel-email { font-size: 11px; color: var(--shunya-text-secondary, #888); margin-left: auto; }
.wksp-loading-text { font-size: 14px; color: var(--shunya-text-secondary, #888); text-align: center; padding: 40px; }
.wksp-empty-text { font-size: 14px; color: var(--shunya-text-secondary, #888); text-align: center; padding: 40px; }
      `}</style>
    </div>
  );
};