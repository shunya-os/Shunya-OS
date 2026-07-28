/**
 * Workspace Runtime — Event-driven, framework-independent workspace state.
 *
 * Manages workspace lifecycle. Transitions happen on external events
 * (ObjectLoaded, TimelineLoaded via event bus) — not on timers.
 */

import { create } from 'zustand';
import { bus, type RuntimeEvent } from '../event-bus';
import { type WorkspaceState, type WorkspaceStatus, type WorkspaceType, canTransition, createWorkspace } from './types';

const STORAGE_KEY = 'shunya_workspaces';
const MAX = 12;
const ARCHIVE_MS = 7 * 24 * 60 * 60 * 1000;

export interface WorkspaceActions {
  open: (name: string, type: WorkspaceType, opts?: Partial<WorkspaceState['identity']>) => string;
  close: (id: string) => void;
  suspend: (id: string) => void;
  resume: (id: string) => void;
  pin: (id: string) => void;
  activate: (id: string) => void;
  transitionTo: (id: string, status: WorkspaceStatus) => boolean;
  hydrate: () => void;
  prune: () => void;
  persist: () => void;
}

type StoreState = { workspaces: WorkspaceState[]; activeId: string | null };

function transitionTo(s: StoreState, id: string, status: WorkspaceStatus): StoreState {
  const ws = s.workspaces.find(w => w.identity.id === id);
  if (!ws || !canTransition(ws.status, status)) return s;
  return {
    ...s,
    workspaces: s.workspaces.map(w =>
      w.identity.id === id ? { ...w, status, identity: { ...w.identity, lastAccessed: Date.now() } } : w
    ),
  };
}

export const useWorkspaceStore = create<StoreState & WorkspaceActions>((set, get) => {
  // Subscribe to events that drive workspace hydration
  bus.on('ObjectLoaded', (e: RuntimeEvent) => {
    if (e.type === 'ObjectLoaded') {
      for (const w of get().workspaces) {
        if (w.identity.objectType === e.objectType && w.identity.objectId === e.objectId && w.status === 'loading') {
          set(s => transitionTo(s, w.identity.id, 'hydrating'));
          bus.emit({ type: 'WorkspaceHydrated', workspaceId: w.identity.id });
        }
      }
    }
  });
  bus.on('TimelineLoaded', (e: RuntimeEvent) => {
    if (e.type === 'TimelineLoaded') {
      for (const w of get().workspaces) {
        if (w.identity.objectType === e.objectType && w.identity.objectId === e.objectId && w.status === 'hydrating') {
          set(s => transitionTo(s, w.identity.id, 'active'));
        }
      }
    }
  });

  return {
    workspaces: [],
    activeId: null,

    open: (name, type, opts) => {
      const state = get();
      const existing = state.workspaces.find(w =>
        w.identity.objectType === opts?.objectType && w.identity.objectId === opts?.objectId && w.identity.type === type
      );
      if (existing) { get().activate(existing.identity.id); return existing.identity.id; }

      if (state.workspaces.length >= MAX) {
        const u = state.workspaces.find(w => !w.identity.pinned);
        if (u) get().close(u.identity.id);
        else return state.workspaces[0].identity.id;
      }

      const ws = createWorkspace(name, type, opts);
      const id = ws.identity.id;
      set(s => ({ workspaces: [...s.workspaces, { ...ws, status: 'loading' as WorkspaceStatus }], activeId: id }));
      get().persist();
      bus.emit({ type: 'WorkspaceOpened', workspaceId: id, objectType: opts?.objectType, objectId: opts?.objectId });
      return id;
    },

    close: (id) => {
      bus.emit({ type: 'WorkspaceDestroyed', workspaceId: id });
      set(s => ({
        workspaces: s.workspaces.filter(w => w.identity.id !== id),
        activeId: s.activeId === id ? (s.workspaces.find(w => w.identity.id !== id)?.identity.id ?? null) : s.activeId,
      }));
      get().prune();
      get().persist();
    },

    suspend: (id) => {
      set(s => transitionTo(s, id, 'suspended'));
      bus.emit({ type: 'WorkspaceSuspended', workspaceId: id });
    },

    resume: (id) => {
      set(s => transitionTo(s, id, 'active'));
      bus.emit({ type: 'WorkspaceResumed', workspaceId: id });
    },

    pin: (id) => {
      set(s => ({
        ...s,
        workspaces: s.workspaces.map(w =>
          w.identity.id === id ? { ...w, identity: { ...w.identity, pinned: !w.identity.pinned } } : w
        ),
      }));
      get().persist();
    },

    activate: (id) => {
      const ws = get().workspaces.find(w => w.identity.id === id);
      if (!ws) return;
      if (ws.status === 'suspended') get().resume(id);
      set(s => ({ ...s, activeId: id }));
    },

    transitionTo: (id, status) => {
      const ws = get().workspaces.find(w => w.identity.id === id);
      if (!ws || !canTransition(ws.status, status)) return false;
      set(s => transitionTo(s, id, status));
      get().persist();
      return true;
    },

    hydrate: () => {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        const data: WorkspaceState[] = JSON.parse(raw);
        set({
          workspaces: data.filter(w => w.identity.pinned || Date.now() - w.identity.lastAccessed < ARCHIVE_MS)
            .map(w => ({ ...w, status: 'suspended' as WorkspaceStatus })),
          activeId: null,
        });
      } catch { /* noop */ }
    },

    prune: () => {
      const cutoff = Date.now() - ARCHIVE_MS;
      set(s => ({ ...s, workspaces: s.workspaces.filter(w => w.identity.pinned || w.identity.lastAccessed > cutoff) }));
    },

    persist: () => {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(get().workspaces)); } catch { /* noop */ }
    },
  };
});