/**
 * EP-03 — Universal Living Object Workspace
 *
 * Every Living Object renders through the same canonical component.
 * The workspace derives itself from object type, runtime capabilities,
 * relationships, available actions, evidence, and execution state.
 *
 * No switch statements. No object-specific pages.
 * New object types require no new component implementation.
 */
import { useState, useEffect, type FC } from 'react';
import { motion } from 'framer-motion';

// ── Types ─────────────────────────────────────────────────────────

interface UniversalWorkspaceData {
  identity: { object_id: string; object_type: string; name: string; created_at: string; status: string };
  reality: any[];
  relationships: any[];
  timeline: any[];
  evidence: any[];
  conversation: any[];
  commitments: any[];
  execution: any[];
  observations: any[];
  predictions: any[];
  files: any[];
  actions: Array<{id: string; label: string; type: string; icon: string}>;
  sections: string[];
}

// ── Section Renderers ──────────────────────────────────────────────

// Each section renders itself based on data, not object type.
// Adding a new section type requires no changes to existing sections.

const IdentitySection: FC<{ data: any }> = ({ data }) => (
  <div className="lw-ws-section">
    <div className="lw-ws-section-title">Identity</div>
    <div className="lw-ws-section-body">
      <div className="lw-ws-identity-row">
        <span className="lw-ws-identity-name">{data.name}</span>
        <span className="lw-ws-identity-type">{data.object_type}</span>
        <span className="lw-ws-identity-status">{data.status}</span>
      </div>
      <div className="lw-ws-identity-meta">
        <span>ID: {data.object_id}</span>
        <span>Created: {new Date(data.created_at).toLocaleDateString()}</span>
      </div>
    </div>
  </div>
);

const RealitySection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return (
    <div className="lw-ws-section">
      <div className="lw-ws-section-title">Reality</div>
      <div className="lw-ws-section-body">
        {data.map((event, i) => (
          <div key={i} className="lw-ws-reality-event">{event.title}</div>
        ))}
      </div>
    </div>
  );
};

const RelationshipsSection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return (
    <div className="lw-ws-section">
      <div className="lw-ws-section-title">Relationships</div>
      <div className="lw-ws-section-body">
        {data.map((rel, i) => (
          <div key={i} className="lw-ws-relationship">{rel.object_name || rel.object_id}</div>
        ))}
      </div>
    </div>
  );
};

const TimelineSection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return (
    <div className="lw-ws-section">
      <div className="lw-ws-section-title">Timeline</div>
      <div className="lw-ws-section-body">
        {data.map((entry, i) => (
          <div key={i} className="lw-ws-timeline-item">
            <div className="lw-ws-timeline-dot" />
            <span>{entry.label || entry.stage}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const EvidenceSection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return <div className="lw-ws-section"><div className="lw-ws-section-title">Evidence</div></div>;
};

const ConversationSection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return <div className="lw-ws-section"><div className="lw-ws-section-title">Conversation</div></div>;
};

const CommitmentsSection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return (
    <div className="lw-ws-section">
      <div className="lw-ws-section-title">Commitments</div>
      <div className="lw-ws-section-body">
        {data.map((c, i) => (
          <div key={i} className="lw-ws-commitment">{c.title || c.label}</div>
        ))}
      </div>
    </div>
  );
};

const ExecutionSection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return <div className="lw-ws-section"><div className="lw-ws-section-title">Execution</div></div>;
};

const ObservationsSection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return (
    <div className="lw-ws-section">
      <div className="lw-ws-section-title">AI Observations</div>
      <div className="lw-ws-section-body">
        {data.map((obs, i) => (
          <div key={i} className="lw-ws-observation">
            <div className="lw-ws-obs-label">{obs.label}</div>
            <div className="lw-ws-obs-conf">{(obs.confidence * 100).toFixed(0)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
};

const PredictionsSection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return <div className="lw-ws-section"><div className="lw-ws-section-title">Predictions</div></div>;
};

const FilesSection: FC<{ data: any[] }> = ({ data }) => {
  if (data.length === 0) return null;
  return <div className="lw-ws-section"><div className="lw-ws-section-title">Files</div></div>;
};

// Map section IDs to renderers
const sectionRenderer: Record<string, FC<{ data: any; objectType: string }>> = {
  identity: IdentitySection,
  reality: RealitySection,
  relationships: RelationshipsSection,
  timeline: TimelineSection,
  evidence: EvidenceSection,
  conversation: ConversationSection,
  commitments: CommitmentsSection,
  execution: ExecutionSection,
  observations: ObservationsSection,
  predictions: PredictionsSection,
  files: FilesSection,
};

// ── Main Workspace Component ──────────────────────────────────────

interface UniversalObjectWorkspaceProps {
  objectId: string;
  objectType: string;
  objectName: string;
  onClose: () => void;
}

export const UniversalObjectWorkspace: FC<UniversalObjectWorkspaceProps> = ({
  objectId, objectType, objectName, onClose,
}) => {
  const [workspace, setWorkspace] = useState<UniversalWorkspaceData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/v1/workspace/${objectId}?type=${objectType}&name=${encodeURIComponent(objectName)}`, {
      credentials: 'include',
    })
      .then((r) => r.json())
      .then((json) => {
        if (!cancelled && json.success) {
          setWorkspace(json.data as UniversalWorkspaceData);
        }
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [objectId, objectType, objectName]);

  if (loading) {
    return (
      <div className="lw-ws-overlay" onClick={onClose}>
        <div className="lw-ws-panel" onClick={(e) => e.stopPropagation()}>
          <div className="lw-ws-loading">Loading workspace…</div>
        </div>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="lw-ws-overlay" onClick={onClose}>
        <div className="lw-ws-panel" onClick={(e) => e.stopPropagation()}>
          <div className="lw-ws-error">Failed to load workspace</div>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  return (
    <div className="lw-ws-overlay" onClick={onClose}>
      <motion.div
        className="lw-ws-panel"
        onClick={(e) => e.stopPropagation()}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {/* Header */}
        <div className="lw-ws-header">
          <div className="lw-ws-header-info">
            <span className="lw-ws-header-type">{workspace.identity.object_type}</span>
            <h2 className="lw-ws-header-name">{workspace.identity.name}</h2>
          </div>
          <button className="lw-ws-close" onClick={onClose}>×</button>
        </div>

        {/* Actions — dynamically generated, driven by runtime */}
        <div className="lw-ws-actions">
          {workspace.actions.map((action) => (
            <motion.button
              key={action.id}
              className="lw-ws-action-btn"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => console.log('Action:', action.id)}
            >
              <span className="lw-ws-action-icon">{action.icon}</span>
              <span className="lw-ws-action-label">{action.label}</span>
            </motion.button>
          ))}
        </div>

        {/* Sections — dynamically composed, driven by section registry */}
        <div className="lw-ws-sections">
          {workspace.sections.map((sectionId) => {
            const Renderer = sectionRenderer[sectionId];
            if (!Renderer) return null;
            return (
              <Renderer
                key={sectionId}
                data={(workspace as any)[sectionId]}
                objectType={objectType}
              />
            );
          })}
        </div>
      </motion.div>
      <style>{`
/* ── Desktop-first responsive ―────────────────────────── */
.lw-ws-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.lw-ws-panel {
  background: var(--shunya-bg, #0f172a); color: var(--shunya-fg, #e2e8f0);
  border: 1px solid var(--shunya-border, #1e293b);
  border-radius: 16px;
  width: 100%; max-width: 800px;
  max-height: 90vh; overflow-y: auto;
  display: flex; flex-direction: column;
}
.lw-ws-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 20px 24px 0; gap: 12px;
}
.lw-ws-header-info { flex: 1; min-width: 0; }
.lw-ws-header-type {
  font-size: 11px; text-transform: uppercase; letter-spacing: .08em;
  color: var(--shunya-muted, #64748b);
}
.lw-ws-header-name {
  font-size: 20px; font-weight: 600; margin: 2px 0 0; line-height: 1.3;
  word-break: break-word;
}
.lw-ws-close {
  background: none; border: none; color: var(--shunya-muted, #64748b);
  font-size: 28px; line-height: 1; cursor: pointer; padding: 0 4px;
  flex-shrink: 0;
}
.lw-ws-close:hover { color: var(--shunya-fg, #e2e8f0); }
.lw-ws-actions {
  display: flex; flex-wrap: wrap; gap: 8px;
  padding: 12px 24px;
}
.lw-ws-action-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--shunya-surface, #1e293b); color: var(--shunya-fg, #e2e8f0);
  border: 1px solid var(--shunya-border, #334155);
  border-radius: 8px; padding: 6px 12px;
  font-size: 13px; cursor: pointer;
}
.lw-ws-action-icon { font-size: 16px; }
.lw-ws-sections {
  display: flex; flex-direction: column; gap: 16px;
  padding: 0 24px 24px;
}
.lw-ws-section {
  background: var(--shunya-surface, #1e293b);
  border-radius: 10px; overflow: hidden;
}
.lw-ws-section-title {
  font-size: 13px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .06em; color: var(--shunya-muted, #64748b);
  padding: 12px 16px 0;
}
.lw-ws-section-body { padding: 8px 16px 12px; }
.lw-ws-identity-row {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
}
.lw-ws-identity-name { font-size: 16px; font-weight: 500; }
.lw-ws-identity-type {
  font-size: 11px; background: var(--shunya-accent, #6C4AE2);
  color: #fff; border-radius: 4px; padding: 2px 6px;
}
.lw-ws-identity-status {
  font-size: 11px; background: var(--shunya-green-dim, #065f46);
  color: var(--shunya-green, #34d399); border-radius: 4px; padding: 2px 6px;
}
.lw-ws-identity-meta {
  display: flex; flex-wrap: wrap; gap: 12px; margin-top: 4px;
  font-size: 12px; color: var(--shunya-muted, #64748b);
}
.lw-ws-reality-event,
.lw-ws-relationship,
.lw-ws-commitment {
  padding: 6px 0; font-size: 14px;
  border-bottom: 1px solid var(--shunya-border, #334155);
}
.lw-ws-timeline-item {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 0; font-size: 14px;
}
.lw-ws-timeline-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--shunya-accent, #6C4AE2); flex-shrink: 0;
}
.lw-ws-observation {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 0; font-size: 14px;
}
.lw-ws-obs-conf { font-size: 12px; color: var(--shunya-muted, #64748b); }
.lw-ws-loading, .lw-ws-error {
  padding: 40px; text-align: center; color: var(--shunya-muted, #64748b);
}

/* ── Tablet (768px) ──────────────────────────────────── */
@media (max-width: 768px) {
  .lw-ws-overlay { padding: 0; align-items: flex-end; }
  .lw-ws-panel {
    max-width: 100%; border-radius: 16px 16px 0 0;
    max-height: 85vh;
  }
  .lw-ws-header { padding: 16px 16px 0; }
  .lw-ws-header-name { font-size: 18px; }
  .lw-ws-actions { padding: 10px 16px; gap: 6px; }
  .lw-ws-sections { padding: 0 16px 16px; gap: 12px; }
  .lw-ws-section-title { font-size: 12px; }
  .lw-ws-action-btn { font-size: 12px; padding: 5px 10px; }
}

/* ── Phone (480px) ────────────────────────────────────── */
@media (max-width: 480px) {
  .lw-ws-panel { max-height: 92vh; border-radius: 12px 12px 0 0; }
  .lw-ws-header { padding: 14px 12px 0; }
  .lw-ws-header-name { font-size: 16px; }
  .lw-ws-actions { padding: 8px 12px; gap: 4px; }
  .lw-ws-action-btn {
    padding: 4px 8px; font-size: 11px;
    flex: 1 1 calc(50% - 4px); justify-content: center;
  }
  .lw-ws-sections { padding: 0 12px 12px; gap: 10px; }
  .lw-ws-section-body { padding: 6px 12px 10px; }
  .lw-ws-identity-row { flex-direction: column; align-items: flex-start; }
  .lw-ws-identity-meta { flex-direction: column; gap: 2px; }
}
      `}</style>
    </div>
  );
};