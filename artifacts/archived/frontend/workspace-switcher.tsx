/**
 * WorkspaceSwitcher — Switch between Personal, Business, and other workspaces.
 *
 * Visual Design: Calm, contextual, low control density.
 * Shows current workspace context and allows switching to another workspace
 * or creating a new one.
 */

import { useState, useEffect, useCallback } from 'react';
import { api } from '../../api/client';

interface Workspace {
  workspace_id: string;
  name: string;
  workspace_type: string;
  capabilities: string[];
}

interface WorkspaceType {
  type: string;
  name: string;
  description: string;
}

interface Props {
  onSwitch?: (workspace: Workspace) => void;
}

export function WorkspaceSwitcher({ onSwitch }: Props) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [current, setCurrent] = useState<Workspace | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createType, setCreateType] = useState('business');
  const [workspaceTypes, setWorkspaceTypes] = useState<WorkspaceType[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load workspaces and current context
  const load = useCallback(async () => {
    try {
      const [ctxResp, listResp, typesResp] = await Promise.all([
        api.getWorkspaceContext(),
        api.listWorkspaces(),
        api.getWorkspaceTypes(),
      ]);
      if (ctxResp.success && ctxResp.data) {
        setCurrent({
          workspace_id: ctxResp.data.workspace_id,
          name: ctxResp.data.workspace_name,
          workspace_type: ctxResp.data.workspace_type,
          capabilities: ctxResp.data.capabilities,
        });
      }
      if (listResp.success && listResp.data) {
        setWorkspaces(listResp.data.workspaces);
      }
      if (typesResp.success && typesResp.data) {
        setWorkspaceTypes(typesResp.data.types);
      }
    } catch {
      // Silently fail — workspace is optional
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSwitch = async (ws: Workspace) => {
    const resp = await api.switchWorkspace(ws.workspace_id);
    if (resp.success && resp.data) {
      setCurrent(resp.data.workspace);
      setExpanded(false);
      onSwitch?.(resp.data.workspace);
    }
  };

  const handleCreate = async () => {
    if (!createName.trim()) return;
    setLoading(true);
    setError('');
    try {
      const resp = await api.createWorkspace(createName.trim(), createType);
      if (resp.success && resp.data) {
        setCurrent(resp.data);
        setShowCreate(false);
        setCreateName('');
        onSwitch?.(resp.data);
        load(); // Refresh list
      } else {
        setError('Failed to create workspace');
      }
    } catch {
      setError('Could not connect');
    } finally {
      setLoading(false);
    }
  };

  const typeIcon = (type: string) => {
    switch (type) {
      case 'personal': return '👤';
      case 'business': return '🏢';
      case 'team': return '👥';
      case 'project': return '📋';
      case 'family': return '👨‍👩‍👧‍👦';
      default: return '📁';
    }
  };

  const typeLabel = (type: string) => {
    switch (type) {
      case 'personal': return 'Personal';
      case 'business': return 'Business';
      case 'team': return 'Team';
      case 'project': return 'Project';
      default: return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };

  return (
    <div className="ws-switcher">
      {/* Current workspace indicator */}
      <button
        className="ws-switcher-current"
        onClick={() => setExpanded(!expanded)}
        title="Switch workspace"
        aria-label="Switch workspace"
      >
        <span className="ws-switcher-icon">{current ? typeIcon(current.workspace_type) : '📁'}</span>
        <span className="ws-switcher-name">
          {current ? current.name : 'Loading...'}
        </span>
        <span className="ws-switcher-type">
          {current ? typeLabel(current.workspace_type) : ''}
        </span>
        <span className={`ws-switcher-arrow ${expanded ? 'open' : ''}`}>▾</span>
      </button>

      {/* Expanded dropdown */}
      {expanded && (
        <div className="ws-switcher-dropdown">
          {workspaces.length === 0 && !showCreate && (
            <div className="ws-switcher-empty">No workspaces yet</div>
          )}

          {workspaces.map(ws => (
            <button
              key={ws.workspace_id}
              className={`ws-switcher-item ${current?.workspace_id === ws.workspace_id ? 'active' : ''}`}
              onClick={() => handleSwitch(ws)}
            >
              <span className="ws-switcher-item-icon">{typeIcon(ws.workspace_type)}</span>
              <span className="ws-switcher-item-name">{ws.name}</span>
              <span className="ws-switcher-item-type">{typeLabel(ws.workspace_type)}</span>
              {current?.workspace_id === ws.workspace_id && (
                <span className="ws-switcher-check">✓</span>
              )}
            </button>
          ))}

          {/* Create workspace */}
          {showCreate ? (
            <div className="ws-switcher-create">
              <input
                type="text"
                value={createName}
                onChange={e => setCreateName(e.target.value)}
                placeholder="Workspace name..."
                autoFocus
                disabled={loading}
                className="ws-switcher-create-input"
              />
              <select
                value={createType}
                onChange={e => setCreateType(e.target.value)}
                disabled={loading}
                className="ws-switcher-create-select"
              >
                {workspaceTypes.filter(t => t.type !== 'personal').map(t => (
                  <option key={t.type} value={t.type}>{t.name}</option>
                ))}
              </select>
              <div className="ws-switcher-create-actions">
                <button
                  className="ws-switcher-create-btn"
                  onClick={handleCreate}
                  disabled={loading || !createName.trim()}
                >
                  {loading ? 'Creating...' : 'Create'}
                </button>
                <button
                  className="ws-switcher-cancel-btn"
                  onClick={() => { setShowCreate(false); setError(''); }}
                >
                  Cancel
                </button>
              </div>
              {error && <div className="ws-switcher-error">{error}</div>}
            </div>
          ) : (
            <button
              className="ws-switcher-add"
              onClick={() => setShowCreate(true)}
            >
              + Create workspace
            </button>
          )}
        </div>
      )}

      <style>{wsSwitcherStyles}</style>
    </div>
  );
}

const wsSwitcherStyles = `
.ws-switcher {
  position: relative;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.ws-switcher-current {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 8px;
  background: rgba(255,255,255,0.8);
  cursor: pointer;
  width: 100%;
  text-align: left;
  font-size: 14px;
  color: #1a1c1d;
  transition: background 0.2s;
}

.ws-switcher-current:hover {
  background: rgba(108,74,226,0.05);
}

.ws-switcher-icon {
  font-size: 16px;
}

.ws-switcher-name {
  flex: 1;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ws-switcher-type {
  font-size: 11px;
  color: #8b8b8b;
  background: rgba(0,0,0,0.04);
  padding: 2px 6px;
  border-radius: 4px;
}

.ws-switcher-arrow {
  font-size: 10px;
  color: #8b8b8b;
  transition: transform 0.2s;
}

.ws-switcher-arrow.open {
  transform: rotate(180deg);
}

.ws-switcher-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: white;
  border: 1px solid rgba(26,28,29,0.1);
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  z-index: 100;
  padding: 4px;
  min-width: 280px;
}

.ws-switcher-empty {
  padding: 16px;
  text-align: center;
  color: #8b8b8b;
  font-size: 13px;
}

.ws-switcher-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  width: 100%;
  text-align: left;
  font-size: 13px;
  color: #1a1c1d;
  border-radius: 6px;
  transition: background 0.15s;
}

.ws-switcher-item:hover {
  background: rgba(108,74,226,0.06);
}

.ws-switcher-item.active {
  background: rgba(108,74,226,0.08);
}

.ws-switcher-item-icon {
  font-size: 16px;
  width: 24px;
  text-align: center;
}

.ws-switcher-item-name {
  flex: 1;
  font-weight: 450;
}

.ws-switcher-item-type {
  font-size: 11px;
  color: #8b8b8b;
}

.ws-switcher-check {
  color: #6c4ae2;
  font-weight: 600;
}

.ws-switcher-add {
  display: block;
  width: 100%;
  padding: 8px 10px;
  margin-top: 4px;
  border: 1px dashed rgba(0,0,0,0.1);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: #6c4ae2;
  transition: background 0.15s;
}

.ws-switcher-add:hover {
  background: rgba(108,74,226,0.06);
}

.ws-switcher-create {
  padding: 8px 10px;
  margin-top: 4px;
  border-top: 1px solid rgba(0,0,0,0.06);
}

.ws-switcher-create-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 6px;
  box-sizing: border-box;
}

.ws-switcher-create-select {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 8px;
  background: white;
  box-sizing: border-box;
}

.ws-switcher-create-actions {
  display: flex;
  gap: 8px;
}

.ws-switcher-create-btn {
  flex: 1;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: #6c4ae2;
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.ws-switcher-create-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.ws-switcher-cancel-btn {
  padding: 6px 12px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: #1a1c1d;
}

.ws-switcher-error {
  margin-top: 6px;
  font-size: 12px;
  color: #e53e3e;
}
`;