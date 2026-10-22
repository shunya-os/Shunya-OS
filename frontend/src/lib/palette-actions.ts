/**
 * Palette action routing — the single mapping from a `shunya:action` id to a
 * workspace surface.
 *
 * Why this module exists (G1.26-A): the command palette dispatches a
 * `shunya:action` CustomEvent and the app shell navigates. Before G1.25 nothing
 * listened, so every navigation command closed the palette and did nothing —
 * eleven dead commands that no test could catch because the mapping lived inside
 * a component. Extracting it makes the contract testable and gives the palette a
 * single source of truth for "which commands have a real surface".
 *
 * Contract:
 *   - a known id resolves to a target (name + workspace type + optional object);
 *   - an unknown id, an empty string, or a non-string detail resolves to null;
 *   - resolution never throws and never routes to a fallback surface, because
 *     silently rendering the dashboard would look like the command worked.
 */

import type { WorkspaceType } from '../runtimes/workspace/types';

export interface PaletteTarget {
  /** Workspace label shown in the workspace bar. */
  name: string;
  /** Workspace type the shell must render. Must have a render branch. */
  type: WorkspaceType;
  /** Present for domain surfaces opened as canonical objects. */
  objectType?: string;
  objectId?: string;
}

function domain(name: string, id: string, type: WorkspaceType): PaletteTarget {
  return { name, type, objectType: id, objectId: id };
}

/**
 * Every palette id that has a real surface. Ids are the values dispatched by
 * `command-palette.tsx`; the palette's own list is asserted against this map by
 * `palette-actions.test.ts`, so a command cannot ship without a destination.
 */
export const PALETTE_TARGETS: Readonly<Record<string, PaletteTarget>> = Object.freeze({
  home: { name: 'Home', type: 'home' },
  people: domain('People', 'people', 'people'),
  work: domain('Work', 'work', 'commitment'),
  conversations: domain('Conversations', 'conversations', 'conversation'),
  documents: domain('Documents', 'documents', 'object'),
  knowledge: domain('Knowledge', 'knowledge', 'object'),
  relationships: domain('Relationships', 'relationships', 'object'),
  team: { name: 'Team', type: 'team' },
  analytics: { name: 'Analytics', type: 'analytics' },
  settings: { name: 'Settings', type: 'settings' },
  'import-export': { name: 'Import & Export', type: 'import-export' },
  'ask-ai': { name: 'Ask SHUNYA', type: 'ai' },
});

/** Resolve a dispatched action id, or null when it has no destination. */
export function resolvePaletteAction(detail: unknown): PaletteTarget | null {
  if (typeof detail !== 'string') return null;
  const key = detail.trim();
  if (!key) return null;
  return Object.prototype.hasOwnProperty.call(PALETTE_TARGETS, key)
    ? PALETTE_TARGETS[key]
    : null;
}
