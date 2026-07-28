/**
 * Workspace Bar — Top navigation bar with workspace tabs and profile menu.
 */

import { useState } from 'react';
import { SessionManager } from '../../api/session';
import { useActiveWorkspace, useWorkspaceList, useWorkspaceActions } from '../../hooks/workspace-hooks';

export function WorkspaceBar() {
  const active = useActiveWorkspace();
  const workspaces = useWorkspaceList();
  const { activate, close } = useWorkspaceActions();
  const [showProfile, setShowProfile] = useState(false);

  const handleLogout = () => {
    SessionManager.clear();
    window.location.reload();
  };

  const session = SessionManager.load();

  return (
    <div className="sh-bar" role="navigation" aria-label="Workspace navigation">
      <div className="sh-bar-tabs">
        {workspaces.map((ws, i) => {
          const isActive = active?.identity.id === ws.identity.id;
          const shortcut = i < 9 ? `⌘${i + 1}` : '';
          return (
            <button
              key={ws.identity.id}
              className={`sh-bar-tab ${isActive ? 'sh-bar-tab-active' : ''}`}
              onClick={() => activate(ws.identity.id)}
              title={`${ws.identity.name}${shortcut ? ` (${shortcut})` : ''}`}
              aria-current={isActive ? 'page' : undefined}
            >
              <span className="sh-bar-tab-label">{ws.identity.name}</span>
              <span className="sh-bar-tab-close" onClick={e => { e.stopPropagation(); close(ws.identity.id); }} role="button" aria-label={`Close ${ws.identity.name}`}>×</span>
            </button>
          );
        })}
      </div>

      <div className="sh-bar-profile">
        <button
          className="sh-bar-profile-btn"
          onClick={() => setShowProfile(!showProfile)}
          aria-label="Profile menu"
          aria-expanded={showProfile}
        >
          {session?.email?.charAt(0).toUpperCase() ?? '?'}
        </button>
        {showProfile && (
          <>
            <div className="sh-bar-overlay" onClick={() => setShowProfile(false)} />
            <div className="sh-bar-dropdown" role="menu">
              <div className="sh-bar-dropdown-header">
                <div className="sh-bar-dropdown-email">{session?.email ?? 'Unknown'}</div>
              </div>
              <hr />
              <button className="sh-bar-dropdown-item" onClick={handleLogout} role="menuitem">
                Sign Out
              </button>
            </div>
          </>
        )}
      </div>

      <style>{`
.sh-bar {
  display: flex; align-items: center; justify-content: space-between;
  height: 40px; background: var(--shunya-surface-1, #16161e);
  border-bottom: 1px solid var(--shunya-surface-2, #22222e);
  padding: 0 8px; flex-shrink: 0; z-index: 50;
}
.sh-bar-tabs { display: flex; align-items: center; gap: 2px; flex: 1; min-width: 0; overflow-x: auto; }
.sh-bar-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 10px; font-size: 0.8rem; color: #888;
  background: transparent; border: none; border-radius: 4px;
  cursor: pointer; white-space: nowrap; transition: all 0.15s;
}
.sh-bar-tab:hover { background: rgba(255,255,255,0.05); color: #ccc; }
.sh-bar-tab-active { background: rgba(255,255,255,0.08); color: #fff; }
.sh-bar-tab-label { font-weight: 400; }
.sh-bar-tab-close {
  font-size: 14px; opacity: 0; cursor: pointer; padding: 0 2px;
  transition: opacity 0.15s; color: #666; line-height: 1;
}
.sh-bar-tab:hover .sh-bar-tab-close { opacity: 0.6; }
.sh-bar-tab-close:hover { opacity: 1 !important; color: #f55; }
.sh-bar-profile { position: relative; }
.sh-bar-profile-btn {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--shunya-color-primary, #444); border: none;
  color: #fff; font-size: 0.75rem; font-weight: 500;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.sh-bar-profile-btn:hover { opacity: 0.8; }
.sh-bar-overlay { position: fixed; inset: 0; z-index: 90; }
.sh-bar-dropdown {
  position: absolute; top: 36px; right: 0; z-index: 100;
  background: #1e1e2a; border: 1px solid #333; border-radius: 8px;
  min-width: 200px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.sh-bar-dropdown-header { padding: 12px 14px; }
.sh-bar-dropdown-email { font-size: 0.8rem; color: #aaa; }
.sh-bar-dropdown hr { border: none; border-top: 1px solid #333; margin: 0; }
.sh-bar-dropdown-item {
  width: 100%; padding: 10px 14px; text-align: left;
  background: transparent; border: none; color: #e0e0e0;
  font-size: 0.85rem; cursor: pointer; display: block;
}
.sh-bar-dropdown-item:hover { background: rgba(255,255,255,0.05); }
`}</style>
    </div>
  );
}