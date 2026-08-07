/**
 * useWorkspaceMemory — Persistent Workspace Memory via sessionStorage
 *
 * Saves and restores workspace UI state scoped to the current browser session.
 * Each workspace gets its own storage key: `shunya_ws_memory_{workspaceId}`.
 *
 * Returns:
 *  - memory: current memory state for this workspace
 *  - saveMemory(partial): merge partial state into existing memory + persist
 *  - clearMemory(workspaceId?): clear memory for one workspace or all
 *  - restoreScroll(ref): restore scroll position on the given scrollable element
 */

import { useState, useCallback, RefObject } from 'react';

export interface WorkspaceMemory {
  scrollPosition: number;
  expandedSections: string[];
  collapsedSections: string[];
  filters: string;
  selectedTab: string | null;
  openedObject: string | null;
  aiContext: string;
  panelWidths: Record<string, number>;
  layoutState: string;
}

const DEFAULT_MEMORY: WorkspaceMemory = {
  scrollPosition: 0,
  expandedSections: [],
  collapsedSections: [],
  filters: '',
  selectedTab: null,
  openedObject: null,
  aiContext: '',
  panelWidths: {},
  layoutState: '',
};

const STORAGE_PREFIX = 'shunya_ws_memory_';

function getKey(workspaceId: string): string {
  return `${STORAGE_PREFIX}${workspaceId}`;
}

function loadMemory(workspaceId: string): WorkspaceMemory {
  try {
    const raw = sessionStorage.getItem(getKey(workspaceId));
    if (raw) {
      return { ...DEFAULT_MEMORY, ...JSON.parse(raw) };
    }
  } catch {
    /* sessionStorage unavailable */
  }
  return { ...DEFAULT_MEMORY };
}

function writeMemory(workspaceId: string, memory: WorkspaceMemory): void {
  try {
    sessionStorage.setItem(getKey(workspaceId), JSON.stringify(memory));
  } catch {
    /* sessionStorage unavailable or quota exceeded */
  }
}

export function useWorkspaceMemory(workspaceId: string | null) {
  const [memory, setMemory] = useState<WorkspaceMemory>(() =>
    workspaceId ? loadMemory(workspaceId) : { ...DEFAULT_MEMORY }
  );

  const saveMemory = useCallback(
    (partial: Partial<WorkspaceMemory>) => {
      if (!workspaceId) return;
      setMemory((prev) => {
        const next = { ...prev, ...partial };
        writeMemory(workspaceId, next);
        return next;
      });
    },
    [workspaceId],
  );

  const clearMemory = useCallback(
    (targetWorkspaceId?: string) => {
      if (targetWorkspaceId) {
        try {
          sessionStorage.removeItem(getKey(targetWorkspaceId));
        } catch {
          /* noop */
        }
        if (targetWorkspaceId === workspaceId) {
          setMemory({ ...DEFAULT_MEMORY });
        }
      } else if (workspaceId) {
        // Clear all workspace-scoped memories
        try {
          for (let i = sessionStorage.length - 1; i >= 0; i--) {
            const key = sessionStorage.key(i);
            if (key && key.startsWith(STORAGE_PREFIX)) {
              sessionStorage.removeItem(key);
            }
          }
        } catch {
          /* noop */
        }
        setMemory({ ...DEFAULT_MEMORY });
      }
    },
    [workspaceId],
  );

  const restoreScroll = useCallback(
    (ref: RefObject<HTMLDivElement | null>) => {
      if (memory.scrollPosition <= 0) return;
      const attempt = () => {
        if (ref.current) {
          ref.current.scrollTop = memory.scrollPosition;
        }
      };
      // Try immediately, then again after one frame for lazy-rendered content
      attempt();
      requestAnimationFrame(attempt);
    },
    [memory.scrollPosition],
  );

  return { memory, saveMemory, clearMemory, restoreScroll };
}