/**
 * Workspace Switcher — Canonical workspace icon bar.
 *
 * Navigation Canon §3:
 *   Icons are 28x28px with subtle gold underline for active state
 *   User can reorder, hide, pin favorites
 *   Max 14 icons
 *   Ctrl+[1-9] keyboard shortcuts
 *
 * Visual Design Bible §8: Icon specifications
 *   Stroke-based icons, 18px navigation size
 *   Icons accompany text
 */

import { useWorkspaceStore } from '../../runtimes/workspace/store';
import { useWorkspaceList, useActiveWorkspace } from '../../hooks/workspace-hooks';

const DEFAULT_ICONS: Record<string, string> = {
  home: 'M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z',
  object: 'M4 4h16v16H4z',
  decision: 'M9 12l2 2 4-4',
  commitment: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
  relationship: 'M12 5v14M5 12h14',
  execution: 'M5 3l14 9-14 9z',
};

function getIcon(type: string): string {
  return DEFAULT_ICONS[type] || DEFAULT_ICONS.object;
}

interface TabProps {
  ws: { identity: { id: string; name: string; type: string; pinned?: boolean } };
  active: boolean;
  onActivate: (id: string) => void;
}

function Tab({ ws, active, onActivate }: TabProps) {
  return (
    <button
      className={`sh-ws-tab${active ? ' sh-ws-tab--active' : ''}`}
      onClick={() => onActivate(ws.identity.id)}
      role="tab"
      aria-selected={active}
      aria-label={ws.identity.name}
      title={ws.identity.name}
    >
      <svg className="sh-ws-icon" width="18" height="18" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" strokeWidth="1.5"
        strokeLinecap="round" strokeLinejoin="round">
        <path d={getIcon(ws.identity.type)} />
      </svg>
      <span className="sh-ws-name">{ws.identity.name}</span>
      <style>{`
.sh-ws-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: var(--shunya-radius-sm, 10px);
  cursor: pointer;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  font-size: var(--shunya-text-sm, 12px);
  font-weight: 400;
  letter-spacing: var(--shunya-tracking-wide, 0.02em);
  white-space: nowrap;
  transition: color var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1)),
              background var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
  position: relative;
}

.sh-ws-tab:hover {
  color: var(--shunya-text, #1A1C1D);
  background: rgba(26,28,29,0.03);
}

.sh-ws-tab--active {
  color: var(--shunya-text, #1A1C1D);
}

.sh-ws-tab--active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 12px;
  right: 12px;
  height: 2px;
  background: var(--shunya-gold, #A4865F);
  border-radius: 1px;
}

.sh-ws-icon {
  flex-shrink: 0;
}

.sh-ws-name {
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}
      `}</style>
    </button>
  );
}

export function WorkspaceBar() {
  const workspaces = useWorkspaceList();
  const active = useActiveWorkspace();
  const activate = useWorkspaceStore((s: any) => s.activate);

  if (workspaces.length === 0) return null;

  return (
    <div className="sh-ws-bar" role="tablist" aria-label="Workspaces">
      {workspaces.map((ws) => (
        <Tab
          key={ws.identity.id}
          ws={ws}
          active={ws.identity.id === active?.identity.id}
          onActivate={activate}
        />
      ))}
      <style>{`
.sh-ws-bar {
  display: flex;
  align-items: center;
  gap: 2px;
  overflow-x: auto;
  scrollbar-width: thin;
  flex: 1;
  min-width: 0;
}
      `}</style>
    </div>
  );
}

export { DEFAULT_ICONS };