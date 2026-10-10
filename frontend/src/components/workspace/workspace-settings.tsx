/**
 * Workspace Settings — name, type, description, capabilities display.
 *
 * Lazy imported; opened via workspace store with type 'workspace-settings'.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  IconSettings, IconPencil, IconCheck, IconX, IconBuildingStore,
  IconUsers, IconBriefcase, IconStar,
} from '@tabler/icons-react';

interface WorkspaceInfo {
  name: string;
  type: string;
  description: string;
  capabilities: { id: string; label: string; enabled: boolean }[];
}

const DEFAULT_WORKSPACE: WorkspaceInfo = {
  name: 'SHUNYA OS',
  type: 'organization',
  description: 'The primary SHUNYA operating surface — organization-wide workspace.',
  capabilities: [
    { id: 'objects', label: 'Universal Objects', enabled: true },
    { id: 'relationships', label: 'Relationship Intelligence', enabled: true },
    { id: 'analytics', label: 'Analytics & Dashboards', enabled: true },
    { id: 'execution', label: 'Task Execution', enabled: true },
    { id: 'memory', label: 'Memory & Knowledge', enabled: true },
    { id: 'documents', label: 'Document Management', enabled: true },
    { id: 'search', label: 'Universal Search', enabled: true },
    { id: 'ai', label: 'AI Intelligence', enabled: true },
    { id: 'commercial', label: 'Commercial Execution', enabled: true },
    { id: 'marketing', label: 'Marketing OS', enabled: true },
    { id: 'finance', label: 'Finance Intelligence', enabled: true },
  ],
};

const TYPE_ICONS: Record<string, React.ReactNode> = {
  organization: <IconBuildingStore size={18} />,
  team: <IconUsers size={18} />,
  personal: <IconBriefcase size={18} />,
  project: <IconStar size={18} />,
};

export function WorkspaceSettings() {
  const [workspace, setWorkspace] = useState<WorkspaceInfo>(DEFAULT_WORKSPACE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<'name' | 'description' | null>(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        // Try loading from workspace API; fall back to defaults
        const r = await fetch('/api/v1/workspace', { credentials: 'include' });
        const d = await r.json();
        if (d.success && d.data) {
          setWorkspace((prev) => ({
            ...prev,
            name: d.data.name || prev.name,
            type: d.data.workspace_type || d.data.type || prev.type,
            description: d.data.description || prev.description,
          }));
        }
      } catch {
        // Use defaults
      }
      setLoading(false);
    })();
  }, []);

  const startEdit = useCallback((field: 'name' | 'description') => {
    setEditing(field);
    setEditValue(workspace[field]);
    setSaveSuccess(false);
  }, [workspace]);

  const cancelEdit = useCallback(() => {
    setEditing(null);
    setEditValue('');
  }, []);

  const saveEdit = useCallback(async (field: 'name' | 'description') => {
    if (!editValue.trim()) return;
    setSaving(true);
    try {
      const r = await fetch('/api/v1/workspace', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ [field]: editValue.trim() }),
      });
      const d = await r.json();
      if (d.success) {
        setWorkspace((prev) => ({ ...prev, [field]: editValue.trim() }));
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 2000);
      } else {
        setError(d.error || 'Failed to save');
      }
    } catch {
      setError('Network error saving changes');
    }
    setSaving(false);
    setEditing(null);
  }, [editValue]);

  if (loading) {
    return (
      <div className="ws-settings">
        <div className="ws-loading">
          <div className="ws-loading-shimmer" />
          <p className="ws-loading-text">Loading workspace settings…</p>
        </div>
        <style>{wsCss}</style>
      </div>
    );
  }

  return (
    <div className="ws-settings">
      <div className="ws-header">
        <div className="ws-header-icon"><IconSettings size={22} /></div>
        <div>
          <h2 className="ws-title">Workspace Settings</h2>
          <p className="ws-subtitle">Configure your SHUNYA workspace</p>
        </div>
      </div>

      {/* Workspace Name */}
      <div className="ws-card">
        <div className="ws-card-header">
          <span className="ws-card-icon">{TYPE_ICONS[workspace.type] || <IconBuildingStore size={18} />}</span>
          <span className="ws-card-title">Workspace Name</span>
        </div>
        <div className="ws-card-body">
          {editing === 'name' ? (
            <div className="ws-edit-row">
              <input
                className="ws-input"
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') saveEdit('name'); if (e.key === 'Escape') cancelEdit(); }}
                autoFocus
              />
              <button className="ws-btn ws-btn-primary" onClick={() => saveEdit('name')} disabled={saving}>
                <IconCheck size={14} />
              </button>
              <button className="ws-btn" onClick={cancelEdit}>
                <IconX size={14} />
              </button>
            </div>
          ) : (
            <div className="ws-display-row">
              <span className="ws-value">{workspace.name}</span>
              <button className="ws-btn ws-btn-ghost" onClick={() => startEdit('name')}>
                <IconPencil size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Workspace Type */}
      <div className="ws-card">
        <div className="ws-card-header">
          <span className="ws-card-icon">{TYPE_ICONS[workspace.type] || <IconBuildingStore size={18} />}</span>
          <span className="ws-card-title">Workspace Type</span>
        </div>
        <div className="ws-card-body">
          <div className="ws-display-row">
            <span className="ws-badge ws-badge-type">{workspace.type}</span>
          </div>
        </div>
      </div>

      {/* Description */}
      <div className="ws-card">
        <div className="ws-card-header">
          <span className="ws-card-icon"><IconPencil size={18} /></span>
          <span className="ws-card-title">Description</span>
        </div>
        <div className="ws-card-body">
          {editing === 'description' ? (
            <div className="ws-edit-row ws-edit-row-column">
              <textarea
                className="ws-textarea"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                rows={3}
                autoFocus
              />
              <div className="ws-edit-actions">
                <button className="ws-btn ws-btn-primary" onClick={() => saveEdit('description')} disabled={saving}>
                  <IconCheck size={14} /> Save
                </button>
                <button className="ws-btn" onClick={cancelEdit}>
                  <IconX size={14} /> Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="ws-display-row">
              <p className="ws-description">{workspace.description}</p>
              <button className="ws-btn ws-btn-ghost" onClick={() => startEdit('description')}>
                <IconPencil size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Capabilities */}
      <div className="ws-card">
        <div className="ws-card-header">
          <span className="ws-card-icon"><IconStar size={18} /></span>
          <span className="ws-card-title">Capabilities Enabled</span>
        </div>
        <div className="ws-card-body">
          <div className="ws-cap-grid">
            {workspace.capabilities.map((cap) => (
              <div key={cap.id} className={`ws-cap-item ${cap.enabled ? 'ws-cap-enabled' : ''}`}>
                <span className={`ws-cap-dot ${cap.enabled ? 'ws-cap-dot-on' : 'ws-cap-dot-off'}`} />
                <span className="ws-cap-label">{cap.label}</span>
                <span className={`ws-cap-status ${cap.enabled ? 'ws-cap-status-on' : 'ws-cap-status-off'}`}>
                  {cap.enabled ? 'Active' : 'Inactive'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Save feedback */}
      {saveSuccess && <div className="ws-toast">✓ Changes saved</div>}
      {error && <div className="ws-error-msg">{error}</div>}

      <style>{wsCss}</style>
    </div>
  );
}

const wsCss = `
.ws-settings { display: flex; flex-direction: column; gap: 16px; padding: 32px; max-width: 640px; }
.ws-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.ws-header-icon { width: 40px; height: 40px; border-radius: 12px; background: rgba(164,134,95,0.10); color: #A4865F; display: flex; align-items: center; justify-content: center; }
.ws-title { font-size: 18px; font-weight: 600; color: #1A1C1D; margin: 0; }
.ws-subtitle { font-size: 12px; color: rgba(26,28,29,0.45); margin: 2px 0 0; }

.ws-card { background: rgba(255,255,255,0.6); border: 1px solid rgba(26,28,29,0.06); border-radius: 12px; overflow: hidden; }
.ws-card-header { display: flex; align-items: center; gap: 8px; padding: 14px 16px 0; }
.ws-card-icon { font-size: 14px; color: rgba(26,28,29,0.4); }
.ws-card-title { font-size: 11px; font-weight: 600; color: rgba(26,28,29,0.5); text-transform: uppercase; letter-spacing: 0.06em; }
.ws-card-body { padding: 12px 16px 16px; }

.ws-display-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.ws-value { font-size: 14px; font-weight: 500; color: #1A1C1D; }
.ws-description { font-size: 13px; color: rgba(26,28,29,0.6); margin: 0; line-height: 1.5; flex: 1; }

.ws-edit-row { display: flex; gap: 6px; align-items: center; }
.ws-edit-row-column { flex-direction: column; align-items: flex-start; }
.ws-edit-actions { display: flex; gap: 6px; }
.ws-input { flex: 1; padding: 8px 12px; border: 1px solid rgba(164,134,95,0.3); border-radius: 6px; font-size: 14px; font-family: inherit; outline: none; background: #fff; color: #1A1C1D; }
.ws-input:focus { border-color: #A4865F; }
.ws-textarea { width: 100%; padding: 8px 12px; border: 1px solid rgba(164,134,95,0.3); border-radius: 6px; font-size: 13px; font-family: inherit; outline: none; background: #fff; color: #1A1C1D; resize: vertical; }
.ws-textarea:focus { border-color: #A4865F; }

.ws-btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px; border: 1px solid rgba(26,28,29,0.08); border-radius: 6px; background: transparent; font-size: 12px; color: rgba(26,28,29,0.55); cursor: pointer; font-family: inherit; transition: all 0.15s; }
.ws-btn:hover { border-color: #A4865F; color: #1A1C1D; }
.ws-btn-primary { background: #A4865F; color: #fff; border-color: #A4865F; }
.ws-btn-primary:hover { opacity: 0.85; color: #fff; }
.ws-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ws-btn-ghost { border-color: transparent; }

.ws-badge { display: inline-flex; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }
.ws-badge-type { background: rgba(164,134,95,0.08); color: #A4865F; text-transform: capitalize; }

.ws-cap-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.ws-cap-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: rgba(255,255,255,0.5); border-radius: 8px; border: 1px solid rgba(26,28,29,0.04); }
.ws-cap-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.ws-cap-dot-on { background: #2D6A4F; }
.ws-cap-dot-off { background: rgba(26,28,29,0.15); }
.ws-cap-label { font-size: 12px; color: #1A1C1D; flex: 1; }
.ws-cap-status { font-size: 10px; font-weight: 500; }
.ws-cap-status-on { color: #2D6A4F; }
.ws-cap-status-off { color: rgba(26,28,29,0.3); }

.ws-toast { position: fixed; bottom: 80px; right: 24px; padding: 10px 18px; background: #2D6A4F; color: #fff; border-radius: 8px; font-size: 12px; font-weight: 500; z-index: 100; animation: ws-fade-in 0.2s ease-out; }
.ws-error-msg { font-size: 12px; color: #B91C1C; padding: 8px 12px; background: rgba(185,28,28,0.06); border-radius: 6px; }
.ws-loading { display: flex; flex-direction: column; gap: 12px; padding: 40px; }
.ws-loading-shimmer { height: 3px; background: linear-gradient(90deg, rgba(26,28,29,0.07) 0%, #A4865F 50%, rgba(26,28,29,0.07) 100%); background-size: 200% 100%; animation: ws-shimmer 1.5s infinite; border-radius: 2px; }
.ws-loading-text { font-size: 13px; color: rgba(26,28,29,0.5); }
@keyframes ws-shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
@keyframes ws-fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 480px) {
  .ws-settings { padding: 20px; }
  .ws-cap-grid { grid-template-columns: 1fr; }
}
`;