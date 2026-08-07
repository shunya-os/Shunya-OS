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
    </div>
  );
};