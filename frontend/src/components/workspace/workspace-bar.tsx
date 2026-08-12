/** Workspace Bar — Tab-based workspace switcher at the top of the screen. */

import { useWorkspaceStore } from '../../runtimes/workspace/store';
import { useWorkspaceList, useActiveWorkspace } from '../../hooks/workspace-hooks';

function Tab({ ws, active, onActivate, onClose }: {
  ws: { identity: { id: string; name: string; type: string; pinned?: boolean }; dirty?: boolean };
  active: boolean;
  onActivate: (id: string) => void;
  onClose: (id: string) => void;
}) {
  const cls = ['wksp-tab', active ? 'wksp-tab-active' : ''].filter(Boolean).join(' ');

  return (
    <div className={cls} onClick={() => onActivate(ws.identity.id)} role="tab" aria-selected={active}>
      <span className="wksp-tab-icon">{ws.identity.type === 'home' ? '🏠' : ws.identity.type === 'object' ? '📄' : '📋'}</span>
      <span className="wksp-tab-name">{ws.identity.name}</span>
      {ws.dirty && <span className="wksp-tab-dirty">•</span>}
      {ws.identity.pinned && <span className="wksp-tab-pinned">📌</span>}
      <button
        className="wksp-tab-close"
        onClick={(e) => { e.stopPropagation(); onClose(ws.identity.id); }}
        aria-label={`Close ${ws.identity.name}`}
      >×</button>
    </div>
  );
}

export function WorkspaceBar() {
  const workspaces = useWorkspaceList();
  const active = useActiveWorkspace();
  const activate = useWorkspaceStore((s: any) => s.activate);
  const close = useWorkspaceStore((s: any) => s.close);

  if (workspaces.length === 0) return null;

  return (
    <div className="wksp-bar" role="tablist" aria-label="Workspaces">
      {workspaces.map((ws) => (
        <Tab
          key={ws.identity.id}
          ws={ws}
          active={ws.identity.id === active?.identity.id}
          onActivate={activate}
          onClose={close}
        />
      ))}
      <style>{`
.wksp-bar { display: flex; gap: 2px; padding: 4px 8px; background: var(--shunya-surface-1, #15151f); border-bottom: 1px solid var(--shunya-surface-2, #22222e); overflow-x: auto; flex-shrink: 0; scrollbar-width: thin; align-items: center; min-height: 36px; }
.wksp-tab { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 13px; color: var(--shunya-text-secondary, #888); white-space: nowrap; transition: background 0.15s, color 0.15s; border: 1px solid transparent; border-bottom: none; }
.wksp-tab:hover { background: var(--shunya-surface-2, #22222e); color: var(--shunya-text, #e0e0e0); }
.wksp-tab-active { background: var(--shunya-surface-3, #2a2a3a); color: var(--shunya-text, #e0e0e0); border-color: var(--shunya-surface-2, #22222e); }
.wksp-tab-icon { font-size: 14px; }
.wksp-tab-name { max-width: 160px; overflow: hidden; text-overflow: ellipsis; }
.wksp-tab-dirty { color: #f5a623; font-size: 16px; line-height: 1; }
.wksp-tab-pinned { font-size: 11px; }
.wksp-tab-close { all: unset; cursor: pointer; font-size: 14px; color: #666; padding: 0 2px; line-height: 1; border-radius: 3px; }
.wksp-tab-close:hover { color: #fff; background: rgba(255,255,255,0.1); }
      `}</style>
    </div>
  );
}