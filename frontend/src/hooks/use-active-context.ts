/**
 * Active Context Store — Single canonical source for current org context.
 * Initialized on app boot from /api/v1/for2/whoami.
 * No polling. No duplicate state.
 */
import { create } from "zustand";

interface ActiveContextState {
  currentOrgId: number | null;
  initialized: boolean;
  loading: boolean;
  init: () => Promise<void>;
  switchContext: (orgId: number | null) => Promise<void>;
}

export const useActiveContext = create<ActiveContextState>((set, get) => ({
  currentOrgId: null,
  initialized: false,
  loading: false,

  init: async () => {
    if (get().initialized) return;
    set({ loading: true });
    try {
      const r = await fetch("/api/v1/for2/whoami", { credentials: "include" });
      const data = await r.json();
      set({
        currentOrgId: data.current_organization_id || null,
        initialized: true,
        loading: false,
      });
    } catch {
      set({ initialized: true, loading: false });
    }
  },

  switchContext: async (orgId: number | null) => {
    set({ loading: true });
    try {
      if (orgId) {
        await fetch(`/api/v1/for2/organizations/${orgId}/switch`, {
          method: "POST",
          credentials: "include",
        });
      } else {
        await fetch("/api/v1/for2/organizations/switch/personal", {
          method: "POST",
          credentials: "include",
        });
      }
      set({ currentOrgId: orgId, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));
