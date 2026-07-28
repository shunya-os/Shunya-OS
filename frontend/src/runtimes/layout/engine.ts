/**
 * Layout Engine — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Define panel arrangements (which panels exist)
 * - Never define how a panel looks (that is the component's domain)
 * - Provide panel ordering given a workspace type and available width
 *
 * ── Events Published ──────────────────────────────────────────
 * (none — passive engine, queried by workspace runtime)
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * (none)
 *
 * ── Owned State ───────────────────────────────────────────────
 * Layout definitions (ordered panel lists with minimum width constraints)
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * (none)
 */

export interface Panel {
  id: string;
  /** Human-readable name for debugging/accessibility only. */
  name: string;
  /** Minimum width in pixels before the panel collapses. */
  minWidth: number;
  /** Layout weight. 1 = flexible (fills remaining space), >1 = fixed px. */
  weight: number;
  /** Display order. */
  order: number;
}

export interface LayoutDefinition {
  name: string;
  panels: Panel[];
  /** How panels behave when the container is narrower than all minWidths combined. */
  overflow: 'stack' | 'collapse' | 'overlay';
}

/**
 * Layout registry — the single place where panel arrangements live.
 * Each entry answers only: which panels exist, in what order, with what constraints.
 */
export const layouts: Record<string, LayoutDefinition> = {
  home: {
    name: 'Home Workspace',
    overflow: 'stack',
    panels: [
      { id: 'org-health',  name: 'Organization Health', minWidth: 300, weight: 1, order: 0 },
      { id: 'recent-decs', name: 'Recent Decisions',    minWidth: 280, weight: 400, order: 1 },
      { id: 'active-tasks',name: 'Active Tasks',        minWidth: 280, weight: 400, order: 2 },
      { id: 'upcoming',    name: 'Upcoming Deadlines',  minWidth: 300, weight: 1, order: 3 },
    ],
  },
  object: {
    name: 'Object Workspace',
    overflow: 'stack',
    panels: [
      { id: 'object-identity', name: 'Identity', minWidth: 280, weight: 400, order: 0 },
      { id: 'insight-card',    name: 'Details',   minWidth: 300, weight: 1, order: 1 },
    ],
  },
  conversation: {
    name: 'Conversation',
    overflow: 'overlay',
    panels: [
      { id: 'messages',    name: 'Messages',  minWidth: 300, weight: 1, order: 0 },
      { id: 'context',     name: 'Context',   minWidth: 280, weight: 350, order: 1 },
    ],
  },
  approval: {
    name: 'Approval Queue',
    overflow: 'stack',
    panels: [
      { id: 'queue',       name: 'Queue',  minWidth: 300, weight: 400, order: 0 },
      { id: 'detail',      name: 'Detail', minWidth: 300, weight: 1, order: 1 },
    ],
  },
  commitment: {
    name: 'Commitment',
    overflow: 'stack',
    panels: [
      { id: 'graph',       name: 'Execution Graph',     minWidth: 280, weight: 450, order: 0 },
      { id: 'narrative',   name: 'Progress Narrative',  minWidth: 300, weight: 1, order: 1 },
      { id: 'ai-insight',  name: 'AI Insight',          minWidth: 280, weight: 380, order: 2 },
    ],
  },
  search: {
    name: 'Search',
    overflow: 'stack',
    panels: [
      { id: 'results',     name: 'Results',     minWidth: 300, weight: 1, order: 0 },
      { id: 'preview',     name: 'Preview',     minWidth: 300, weight: 400, order: 1 },
    ],
  },
};

export function getLayout(type: string): LayoutDefinition {
  return layouts[type] ?? layouts.object;
}

/**
 * Given a layout and available width, return ordered panels that fit.
 * Pure function — no side effects, no presentation logic.
 */
export function fitPanels(layout: LayoutDefinition, availableWidth: number): Panel[] {
  const sorted = [...layout.panels].sort((a, b) => a.order - b.order);
  if (layout.overflow === 'stack') {
    let remaining = availableWidth;
    const result: Panel[] = [];
    for (const p of sorted) {
      if (remaining >= p.minWidth) {
        result.push(p);
        remaining -= p.weight === 1 ? Math.max(p.minWidth, availableWidth / sorted.length) : p.weight;
      }
    }
    return result.length > 0 ? result : [sorted[0]];
  }
  return sorted;
}