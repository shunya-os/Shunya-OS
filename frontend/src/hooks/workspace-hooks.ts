/**
 * Workspace Hooks — React bridge for the framework-independent Workspace Runtime.
 *
 * This is the only layer that imports React. The runtime never does.
 * To port to another framework, replace this file; the runtime stays untouched.
 */

import { useEffect } from 'react';
import { useWorkspaceStore } from '../runtimes/workspace/store';

export function useOpenWorkspace() {
  return useWorkspaceStore(s => s.open);
}

export function useActiveWorkspace() {
  const workspaces = useWorkspaceStore(s => s.workspaces);
  const activeId = useWorkspaceStore(s => s.activeId);
  return workspaces.find(w => w.identity.id === activeId) ?? null;
}

export function useWorkspaceList() {
  return useWorkspaceStore(s => s.workspaces);
}

export function useWorkspaceActions() {
  return {
    close: useWorkspaceStore(s => s.close),
    activate: useWorkspaceStore(s => s.activate),
    pin: useWorkspaceStore(s => s.pin),
    suspend: useWorkspaceStore(s => s.suspend),
  };
}

export function useWorkspaceHydration() {
  const hydrate = useWorkspaceStore(s => s.hydrate);
  useEffect(() => { hydrate(); }, [hydrate]);
}

export function useCommandPalette() {
  const open = useWorkspaceStore(s => s.open);
  return {
    openObject: (type: string, id: string, name: string) =>
      open(name, 'object', { objectType: type, objectId: id }),
    openDashboard: () => open('Dashboard', 'dashboard'),
    openSearch: (query: string) => open(`Search: ${query}`, 'search'),
  };
}