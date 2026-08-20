/**
 * Relationship Workspace — Real relationship drill-down.
 *
 * Shows relationships, timeline, and AI memory
 * from the existing /relationships/api/v1/relationships API.
 */

import { useState, useEffect } from 'react';
import type { FC } from 'react';

interface RelItem {
  id: number;
  name?: string;
  company_name?: string;
  email?: string;
  relationship_type: string;
  status: string;
  created_at: string;
}

interface TimelineEntry {
  id: number;
  event_type: string;
  summary: string;
  created_at: string;
}

interface AIMemory {
  id: number;
  memory: Record<string, unknown>;
  engagement_score?: number;
  health_score?: number;
  created_at: string;
}

async function api<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    return await r.json() as T;
  } catch { return null; }
}

export const RelationshipWorkspace: FC = () => {
  const [relationships, setRelationships] = useState<RelItem[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [memory, setMemory] = useState<AIMemory | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const data = await api<any>('/relationships/api/v1/relationships?limit=100');
        if (data) setRelationships(data.relationships || []);
      } catch {
        setError('Could not load relationships');
      }
      setLoading(false);
    })();
  }, []);

  const handleExpand = async (id: number) => {
    if (expandedId === id) { setExpandedId(null); return; }
    setExpandedId(id);
    setDetailLoading(true);
    try {
      const [tlData, memData] = await Promise.all([
        api<any>(`/relationships/api/v1/relationships/${id}/timeline`),
        api<any>(`/relationships/api/v1/relationships/${id}/memory`),
      ]);
      if (tlData) setTimeline(tlData.timeline || []);
      else setTimeline([]);
      if (memData) setMemory(memData.ai_memory || null);
      else setMemory(null);
    } catch {
      setTimeline([]);
      setMemory(null);
    }
    setDetailLoading(false);
  };

  return (
    <div className="pw-panel-container">
      <div className="pw-domain-header">
        <span className="pw-domain-icon">◈</span>
        <h2 className="pw-domain-title">Relationships</h2>
      </div>

      {loading && <div className="pw-domain-loading">Loading relationships…</div>}
      {error && <div className="pw-error-msg">{error}</div>}

      {!loading && (
        <div className="pw-commercial-list">
          {relationships.length === 0 && <div className="pw-domain-empty"><p>No relationships found.</p></div>}
          {relationships.map((rel) => {
            const name = rel.name || rel.company_name || rel.email || `Relationship #${rel.id}`;
            return (
              <div key={rel.id}>
                <div
                  className="pw-commercial-item"
                  onClick={() => handleExpand(rel.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="pw-commercial-item-title">{name}</div>
                  <div className="pw-commercial-item-meta">
                    <span className="pw-commercial-tag">{rel.relationship_type}</span>
                    <span className={`pw-commercial-tag pw-status-${rel.status}`}>{rel.status}</span>
                    <span className="pw-commercial-date">{new Date(rel.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                {expandedId === rel.id && (
                  <div className="pw-rel-detail">
                    {detailLoading && <p className="pw-domain-loading">Loading detail…</p>}
                    {!detailLoading && (
                      <>
                        {/* Timeline */}
                        {timeline.length > 0 && (
                          <div className="pw-rel-section">
                            <p className="pw-rel-section-title">Timeline ({timeline.length})</p>
                            {timeline.map((t) => (
                              <div key={t.id} className="pw-rel-timeline-item">
                                <span className="pw-rel-tl-dot" />
                                <div>
                                  <p className="pw-rel-tl-text">{t.summary}</p>
                                  <span className="pw-commercial-date">{new Date(t.created_at).toLocaleDateString()}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                        {timeline.length === 0 && <p className="pw-domain-loading">No timeline entries.</p>}

                        {/* AI Memory */}
                        {memory && (
                          <div className="pw-rel-section">
                            <p className="pw-rel-section-title">AI Memory</p>
                            <div className="pw-rel-memory">
                              <p>Health: {memory.health_score ?? '?'} · Engagement: {memory.engagement_score ?? '?'}</p>
                              <p className="pw-commercial-date">Since {new Date(memory.created_at).toLocaleDateString()}</p>
                            </div>
                          </div>
                        )}
                      </>
                    )}
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