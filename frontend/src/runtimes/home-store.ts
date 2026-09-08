/**
 * Home Store — SHUNYA Home page state.
 *
 * Loads live task data from the execution API and refreshes it on a schedule:
 *   - active tasks: every 5s (SHUNYA NOW must feel alive)
 *   - recent + attention tasks: every 30s (lower churn)
 *
 * The store degrades gracefully: on API failure it keeps the last known data
 * and exposes `error` so the Home page can show a truthful reconnecting state.
 * It never fabricates tasks, phases, or progress.
 */

import { create } from 'zustand';
import {
  fetchActiveTasks,
  fetchRecentTasks,
  fetchAttentionTasks,
  type TaskLifecycle,
} from '../api/execution-api';

const ACTIVE_POLL_MS = 5000;
const LISTS_POLL_MS = 30000;

interface HomeStoreState {
  // Live data
  activeTasks: TaskLifecycle[];
  recentTasks: TaskLifecycle[];
  attentionTasks: TaskLifecycle[];

  // Derived convenience — completed view of recentTasks
  completedTasks: TaskLifecycle[];

  // Loading / error
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;

  // Actions
  loadAll: () => Promise<void>;
  refreshActive: () => Promise<void>;
  refreshLists: () => Promise<void>;
  clearError: () => void;
  /** Starts periodic refresh. Returns a stop function. */
  startPolling: () => () => void;
}

function isCompleted(t: TaskLifecycle): boolean {
  return t.status === 'completed' || t.outcome === 'completed' || t.outcome === 'partial';
}

function deriveCompleted(recent: TaskLifecycle[]): TaskLifecycle[] {
  return recent.filter(isCompleted);
}

export const useHomeStore = create<HomeStoreState>((set, get) => {
  let activeTimer: ReturnType<typeof setInterval> | null = null;
  let listsTimer: ReturnType<typeof setInterval> | null = null;

  const refreshActive = async (): Promise<void> => {
    const res = await fetchActiveTasks();
    if (res.success) {
      set((s) => ({
        activeTasks: res.data ?? s.activeTasks,
        error: null,
        lastUpdated: Date.now(),
      }));
    } else if (res.error) {
      set({ error: res.error });
    }
  };

  const refreshLists = async (): Promise<void> => {
    const [recentRes, attentionRes] = await Promise.all([
      fetchRecentTasks(),
      fetchAttentionTasks(),
    ]);

    if (recentRes.success) {
      const recentTasks = recentRes.data ?? get().recentTasks;
      set(() => ({
        recentTasks,
        completedTasks: deriveCompleted(recentTasks),
        error: null,
        lastUpdated: Date.now(),
      }));
    } else if (recentRes.error) {
      set({ error: recentRes.error });
    }

    if (attentionRes.success) {
      set((s) => ({
        attentionTasks: attentionRes.data ?? s.attentionTasks,
        error: null,
        lastUpdated: Date.now(),
      }));
    } else if (attentionRes.error) {
      set({ error: attentionRes.error });
    }
  };

  const loadAll = async (): Promise<void> => {
    set(() => ({ isLoading: get().activeTasks.length === 0 && get().recentTasks.length === 0 }));
    await Promise.all([refreshActive(), refreshLists()]);
    set({ isLoading: false });
  };

  const startPolling = (): (() => void) => {
    loadAll();

    if (activeTimer) clearInterval(activeTimer);
    if (listsTimer) clearInterval(listsTimer);

    activeTimer = setInterval(() => {
      refreshActive();
    }, ACTIVE_POLL_MS);

    listsTimer = setInterval(() => {
      refreshLists();
    }, LISTS_POLL_MS);

    return () => {
      if (activeTimer) clearInterval(activeTimer);
      if (listsTimer) clearInterval(listsTimer);
      activeTimer = null;
      listsTimer = null;
    };
  };

  return {
    activeTasks: [],
    recentTasks: [],
    attentionTasks: [],
    completedTasks: [],
    isLoading: true,
    error: null,
    lastUpdated: null,

    loadAll,
    refreshActive,
    refreshLists,

    clearError: () => set({ error: null }),

    startPolling,
  };
});