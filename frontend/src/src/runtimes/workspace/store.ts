/**
 * Workspace Runtime — Event-driven, framework-independent workspace state.
 *
 * Manages workspace lifecycle. Transitions happen on external events
 * (ObjectLoaded, TimelineLoaded via event bus) — not on timers.
 *
 * Every workspace exposes:
 *   unique runtime identity ✓
 *   lifecycle ✓ (8 states with deterministic transitions)
 *   loading state ✓
 *   ready state ✓
 *   empty state ✓
 *   error state ✓
 *   closing state ✓
 *   dirty state ✓
 *   validation state ✓
 *   save status ✓
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
  closeWithConfirmation: (id: string) => boolean;
  suspend: (id: string) => void;
  resume: (id: string) => void;
  pin: (id: string) => void;
  activate: (id: string) => void;
  transitionTo: (id: string, status: WorkspaceStatus) => boolean;
  markError: (id: string, error: string) => void;
  markDirty: (id: string, dirty: boolean) => void;
  markSaving: (id: string) => void;
  markSaved: (id: string) => void;
  markSaveFailed: (id: string, error: string) => void;
  setValidationErrors: (id: string, errors: Record<string, string>) => void;
  hydrate: () => void;
  prune: () => void;
  persist: () => void;
  getWorkspace: (id: string) => WorkspaceState | undefined;
  /** Returns true if any workspace has unsaved changes. */
  hasDirty: () => boolean;
  /** Returns IDs of workspaces with unsaved changes. */
  getDirtyIds: () => string[];
}

type StoreState = { workspaces: WorkspaceState[]; activeId: string | null };

function transitionTo(s: StoreState, id: string, status: WorkspaceStatus): StoreState {
  const ws = s.workspaces.find(w => w.identity.id === id);
  if (!ws || !canTransition(ws.status, status)) return s;
  const from = ws.status;
  if (from !== status) {
    bus.emit({ type: 'WorkspaceChanged', workspaceId: id, from, to: status });
  }
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
  bus.on('ObjectError', (e: RuntimeEvent) => {
    if (e.type === 'ObjectError') {
      for (const w of get().workspaces) {
        if (w.identity.objectType === e.objectType && w.identity.objectId === e.objectId) {
          set(s => transitionTo(s, w.identity.id, 'error'));
          bus.emit({ type: 'WorkspaceError', workspaceId: w.identity.id, error: e.error });
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
      const ws = get().workspaces.find(w => w.identity.id === id);
      if (!ws) return;
      // If dirty, emit closing event — caller should check hasDirty first
      if (ws.dirty) {
        bus.emit({ type: 'WorkspaceClosing', workspaceId: id });
      }
      bus.emit({ type: 'ObjectClosed', objectType: ws.identity.objectType ?? '', objectId: ws.identity.objectId ?? '', workspaceId: id });
      bus.emit({ type: 'WorkspaceDestroyed', workspaceId: id });
      set(s => ({
        workspaces: s.workspaces.filter(w => w.identity.id !== id),
        activeId: s.activeId === id ? (s.workspaces.find(w => w.identity.id !== id)?.identity.id ?? null) : s.activeId,
      }));
      get().prune();
      get().persist();
    },

    closeWithConfirmation: (id) => {
      const ws = get().workspaces.find(w => w.identity.id === id);
      if (!ws) return true;
      if (ws.dirty) {
        bus.emit({ type: 'WorkspaceClosing', workspaceId: id });
        return false; // caller should confirm
      }
      get().close(id);
      return true;
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
      if (ws.status === 'error') {
        // Retry from error state
        set(s => transitionTo(s, id, 'loading'));
      }
      set(s => ({ ...s, activeId: id }));
    },

    transitionTo: (id, status) => {
      const ws = get().workspaces.find(w => w.identity.id === id);
      if (!ws || !canTransition(ws.status, status)) return false;
      set(s => transitionTo(s, id, status));
      get().persist();
      return true;
    },

    markError: (id, error) => {
      set(s => ({
        ...s,
        workspaces: s.workspaces.map(w =>
          w.identity.id === id ? { ...w, status: 'error' as WorkspaceStatus, error } : w
        ),
      }));
      bus.emit({ type: 'WorkspaceError', workspaceId: id, error });
      get().persist();
    },

    markDirty: (id, dirty) => {
      set(s => ({
        ...s,
        workspaces: s.workspaces.map(w =>
          w.identity.id === id ? { ...w, dirty } : w
        ),
      }));
      if (dirty) {
        const ws = get().workspaces.find(w => w.identity.id === id);
        if (ws) {
          bus.emit({ type: 'ObjectDirtyChanged', objectType: ws.identity.objectType ?? '', objectId: ws.identity.objectId ?? '', dirty });
        }
      }
    },

    markSaving: (id) => {
      set(s => ({
        ...s,
        workspaces: s.workspaces.map(w =>
          w.identity.id === id ? { ...w, saveStatus: 'saving' as const } : w
        ),
      }));
    },

    markSaved: (id) => {
      set(s => ({
        ...s,
        workspaces: s.workspaces.map(w =>
          w.identity.id === id ? { ...w, saveStatus: 'saved' as const, dirty: false, validationErrors: {} } : w
        ),
      }));
      const ws = get().workspaces.find(w => w.identity.id === id);
      if (ws) {
        bus.emit({ type: 'ObjectSaved', objectType: ws.identity.objectType ?? '', objectId: ws.identity.objectId ?? '', workspaceId: id });
      }
    },

    markSaveFailed: (id, error) => {
      set(s => ({
        ...s,
        workspaces: s.workspaces.map(w =>
          w.identity.id === id ? { ...w, saveStatus: 'failed' as const, error } : w
        ),
      }));
      const ws = get().workspaces.find(w => w.identity.id === id);
      if (ws) {
        bus.emit({ type: 'ObjectSaveFailed', objectType: ws.identity.objectType ?? '', objectId: ws.identity.objectId ?? '', workspaceId: id, error });
      }
    },

    setValidationErrors: (id, errors) => {
      set(s => ({
        ...s,
        workspaces: s.workspaces.map(w =>
          w.identity.id === id ? { ...w, validationErrors: errors } : w
        ),
      }));
    },

    hydrate: () => {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        const data: WorkspaceState[] = JSON.parse(raw);
        const filtered = data.filter(w => w.identity.pinned || Date.now() - w.identity.lastAccessed < ARCHIVE_MS)
          .map(w => ({ ...w, status: 'suspended' as WorkspaceStatus, saveStatus: 'idle' as const }));
        set({
          workspaces: filtered,
          activeId: filtered.length > 0 ? filtered[0].identity.id : null,
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

    getWorkspace: (id) => {
      return get().workspaces.find(w => w.identity.id === id);
    },

    hasDirty: () => {
      return get().workspaces.some(w => w.dirty);
    },

    getDirtyIds: () => {
      return get().workspaces.filter(w => w.dirty).map(w => w.identity.id);
    },
  };
});