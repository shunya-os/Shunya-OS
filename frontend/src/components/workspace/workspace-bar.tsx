/**
 * Workspace Bar — Zone 1 of the three-zone layout.
 *
 * Per Navigation Canon §2:
 *   [Logo/Home] [Workspace Switcher] [Breadcrumb] [Search Bar] [Notifications] [User Menu]
 *
 * Always present, always identical across all workspaces.
 * Shows dirty state indicator for workspaces with unsaved changes.
 */

import { useState } from 'react';
import { SessionManager } from '../../api/session';
import { useActiveWorkspace, useWorkspaceList, useWorkspaceActions } from '../../hooks/workspace-hooks';
import { useShellContext } from './workspace-shell';

export function WorkspaceBar() {
  const active = useActiveWorkspace();
  const workspaces = useWorkspaceList();
  const { activate, close } = useWorkspaceActions();
  const [showProfile, setShowProfile] = useState(false);
  const { toggleContextPanel, contextPanelCollapsed } = useShellContext();

  const handleLogout = () => {
    SessionManager.clear();
    window.location.reload();
  };

  const session = SessionManager.load();

  return (
    <div className="sh-bar" role="navigation" aria-label="Workspace navigation">
      {/* Logo / Home */}
      <button
        className="sh-bar-home"
        onClick={() => {
          const home = workspaces.find(w => w.identity.type === 'home');
          if (home) activate(home.identity.id);
          else if (active) close(active.identity.id);
        }}
        title="Home workspace"
        aria-label="Home"
      >
        <span className="sh-bar-logo">शून्य</span>
      </button>

      {/* Workspace Switcher */}
      <div className="sh-bar-switcher" role="tablist" aria-label="Workspace switcher">
        {workspaces.map((ws, i) => {
          const isActive = active?.identity.id === ws.identity.id;
          const shortcut = i < 9 ? `⌘${i + 1}` : '';
          const statusIcon = ws.dirty ? '●' : ws.status === 'error' ? '⚠' : '';
          const statusClass = ws.dirty ? 'sh-bar-tab-dirty' : ws.status === 'error' ? 'sh-bar-tab-error' : '';
          return (
            <button
              key={ws.identity.id}
              className={`sh-bar-tab ${isActive ? 'sh-bar-tab-active' : ''} ${statusClass}`}
              onClick={() => activate(ws.identity.id)}
              title={`${ws.identity.name}${ws.dirty ? ' (unsaved changes)' : ''}${shortcut ? ` (${shortcut})` : ''}`}
              role="tab"
              aria-selected={isActive}
              aria-current={isActive ? 'true' : undefined}
            >
              {statusIcon && <span className="sh-bar-tab-status">{statusIcon}</span>}
              <span className="sh-bar-tab-label">{ws.identity.name}</span>
              <span
                className="sh-bar-tab-close"
                onClick={e => { e.stopPropagation(); close(ws.identity.id); }}
                role="button"
                aria-label={`Close ${ws.identity.name}`}
              >×</span>
            </button>
          );
        })}
      </div>

      {/* Context Panel Toggle */}
      <button
        className="sh-bar-toggle"
        onClick={toggleContextPanel}
        title={contextPanelCollapsed ? 'Expand context panel' : 'Collapse context panel'}
        aria-label="Toggle context panel"
      >
        {contextPanelCollapsed ? '☰' : '☰'}
      </button>

      {/* Profile Menu */}
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
              <button className="sh-bar-dropdown-item" onClick={() => {
                // Close all modals
                setShowProfile(false);
              }} role="menuitem">
                Close
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const styles = `
.sh-bar { display: flex; align-items: center; height: 48px; min-height: 48px; background: var(--shunya-surface-2, #1a1a26); border-bottom: 1px solid var(--shunya-surface-1, #22222e); padding: 0 8px; gap: 4px; z-index: 100; }
.sh-bar-home { width: 40px; height: 100%; display: flex; align-items: center; justify-content: center; background: transparent; border: none; cursor: pointer; flex-shrink: 0; }
.sh-bar-logo { font-size: 16px; color: var(--shunya-text, #e0e0e0); }
.sh-bar-switcher { display: flex; align-items: center; gap: 2px; flex: 1; overflow-x: auto; min-width: 0; padding: 0 4px; }
.sh-bar-tab { display: flex; align-items: center; gap: 4px; height: 32px; padding: 0 8px; background: transparent; border: 1px solid transparent; border-radius: 4px; color: var(--shunya-text-secondary, #888); font-size: var(--shunya-font-size-xs); cursor: pointer; white-space: nowrap; flex-shrink: 0; }
.sh-bar-tab:hover { background: rgba(255,255,255,0.05); border-color: var(--shunya-surface-1, #2a2a3a); }
.sh-bar-tab-active { background: rgba(255,255,255,0.08); color: var(--shunya-text, #e0e0e0); border-color: var(--shunya-surface-1, #333); }
.sh-bar-tab-dirty { color: var(--shunya-color-warning, #f0ad4e); }
.sh-bar-tab-error { color: var(--shunya-color-danger, #f55); }
.sh-bar-tab-status { font-size: 10px; }
.sh-bar-tab-label { max-width: 120px; overflow: hidden; text-overflow: ellipsis; }
.sh-bar-tab-close { margin-left: 2px; font-size: 14px; line-height: 1; opacity: 0.5; padding: 0 2px; border-radius: 2px; }
.sh-bar-tab-close:hover { opacity: 1; background: rgba(255,255,255,0.1); }
.sh-bar-toggle { width: 30px; height: 27px; display: flex; align-items: center; justify-content: center; background: transparent; border: none; cursor: pointer; font-size: 16px; color: var(--shunya-text-secondary, #888); flex-shrink: 0; }
.sh-bar-profile { position: relative; width: 28px; height: 28px; flex-shrink: 0; }
.sh-bar-profile-btn { width: 28px; height: 28px; border-radius: 50%; background: var(--shunya-color-primary, #555); color: #fff; border: none; font-size: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.sh-bar-overlay { position: fixed; inset: 0; z-index: 200; }
.sh-bar-dropdown { position: absolute; top: 36px; right: 0; min-width: 180px; background: var(--shunya-surface-2, #1a1a26); border: 1px solid var(--shunya-surface-1, #333); border-radius: var(--shunya-radius-md); box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 201; padding: 4px 0; }
.sh-bar-dropdown-header { padding: 8px 12px; }
.sh-bar-dropdown-email { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary, #888); }
.sh-bar-dropdown hr { border: none; border-top: 1px solid var(--shunya-surface-1, #22222e); }
.sh-bar-dropdown-item { display: block; width: 100%; text-align: left; padding: 8px 12px; background: transparent; border: none; color: var(--shunya-text, #e0e0e0); font-size: var(--shunya-font-size-sm); cursor: pointer; }
.sh-bar-dropdown-item:hover { background: rgba(255,255,255,0.05); }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  document.head.appendChild(el);
}