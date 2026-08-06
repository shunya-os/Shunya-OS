/**
 * Layout Engine v2 — SX-11 Living Workspace Layouts
 *
 * Every object type gets its own contextual panel arrangement.
 * Not generic — each layout answers: what does this object need to show?
 */
export interface PanelSlot {
  id: string;
  name: string;
  minWidth: number;
  weight: number;
  order: number;
}

export interface LayoutDefinition {
  name: string;
  panels: PanelSlot[];
  overflow: 'stack' | 'collapse' | 'overlay';
}

export const layouts: Record<string, LayoutDefinition> = {
  // ── Home / Executive Dashboard ──
  home: {
    name: 'Executive Home',
    overflow: 'stack',
    panels: [
      { id: 'ai-understanding', name: 'AI Understanding', minWidth: 300, weight: 1, order: 0 },
      { id: 'priorities', name: 'Priorities', minWidth: 280, weight: 360, order: 1 },
      { id: 'recent-activity', name: 'Recent Activity', minWidth: 280, weight: 360, order: 2 },
      { id: 'active-commitments', name: 'Active Commitments', minWidth: 280, weight: 340, order: 3 },
      { id: 'capability-bar', name: 'Capability Bar', minWidth: 200, weight: 80, order: 4 },
    ],
  },

  // ── Customer Workspace — every relationship has context ──
  customer: {
    name: 'Customer Workspace',
    overflow: 'stack',
    panels: [
      { id: 'object-identity', name: 'Customer', minWidth: 280, weight: 350, order: 0 },
      { id: 'ai-understanding', name: 'AI Understanding', minWidth: 280, weight: 1, order: 1 },
      { id: 'timeline', name: 'Activity Timeline', minWidth: 260, weight: 300, order: 2 },
      { id: 'related-objects', name: 'Related Objects', minWidth: 240, weight: 260, order: 3 },
      { id: 'next-actions', name: 'Next Actions', minWidth: 240, weight: 240, order: 4 },
      { id: 'commitments', name: 'Commitments', minWidth: 240, weight: 240, order: 5 },
    ],
  },

  // ── Trip Workspace — a story, not an itinerary ──
  trip: {
    name: 'Trip Workspace',
    overflow: 'stack',
    panels: [
      { id: 'object-identity', name: 'Trip Overview', minWidth: 280, weight: 350, order: 0 },
      { id: 'ai-understanding', name: 'Trip Intelligence', minWidth: 280, weight: 1, order: 1 },
      { id: 'timeline', name: 'Itinerary', minWidth: 260, weight: 300, order: 2 },
      { id: 'related-expenses', name: 'Expenses', minWidth: 240, weight: 260, order: 3 },
      { id: 'related-documents', name: 'Documents', minWidth: 240, weight: 240, order: 4 },
      { id: 'next-actions', name: 'Next Steps', minWidth: 240, weight: 240, order: 5 },
    ],
  },

  // ── Invoice Workspace — a commitment, not a line item ──
  invoice: {
    name: 'Invoice Workspace',
    overflow: 'stack',
    panels: [
      { id: 'object-identity', name: 'Invoice', minWidth: 280, weight: 350, order: 0 },
      { id: 'ai-understanding', name: 'AI Risk & Insight', minWidth: 280, weight: 1, order: 1 },
      { id: 'timeline', name: 'Payment Timeline', minWidth: 260, weight: 280, order: 2 },
      { id: 'related-customer', name: 'Customer', minWidth: 240, weight: 260, order: 3 },
      { id: 'related-objects', name: 'Related', minWidth: 240, weight: 240, order: 4 },
      { id: 'next-actions', name: 'Actions', minWidth: 240, weight: 240, order: 5 },
    ],
  },

  // ── Document Workspace — content is the hero ──
  document: {
    name: 'Document Workspace',
    overflow: 'stack',
    panels: [
      { id: 'object-identity', name: 'Document', minWidth: 280, weight: 350, order: 0 },
      { id: 'ai-understanding', name: 'AI Summary', minWidth: 280, weight: 1, order: 1 },
      { id: 'timeline', name: 'Version History', minWidth: 260, weight: 280, order: 2 },
      { id: 'related-objects', name: 'Related', minWidth: 240, weight: 260, order: 3 },
      { id: 'conversations', name: 'Conversations', minWidth: 240, weight: 240, order: 4 },
      { id: 'next-actions', name: 'Actions', minWidth: 240, weight: 240, order: 5 },
    ],
  },

  // ── Project Workspace — milestones, not tasks ──
  project: {
    name: 'Project Workspace',
    overflow: 'stack',
    panels: [
      { id: 'object-identity', name: 'Project', minWidth: 280, weight: 350, order: 0 },
      { id: 'ai-understanding', name: 'AI Status', minWidth: 280, weight: 1, order: 1 },
      { id: 'timeline', name: 'Milestones', minWidth: 260, weight: 300, order: 2 },
      { id: 'related-objects', name: 'Team & Tasks', minWidth: 240, weight: 260, order: 3 },
      { id: 'commitments', name: 'Commitments', minWidth: 240, weight: 240, order: 4 },
      { id: 'next-actions', name: 'Next Actions', minWidth: 240, weight: 240, order: 5 },
    ],
  },

  // ── Company Workspace — organizational intelligence ──
  company: {
    name: 'Company Workspace',
    overflow: 'stack',
    panels: [
      { id: 'object-identity', name: 'Company', minWidth: 280, weight: 350, order: 0 },
      { id: 'ai-understanding', name: 'AI Analysis', minWidth: 280, weight: 1, order: 1 },
      { id: 'timeline', name: 'Activity', minWidth: 260, weight: 280, order: 2 },
      { id: 'related-contacts', name: 'Contacts', minWidth: 240, weight: 260, order: 3 },
      { id: 'related-deals', name: 'Deals & Invoices', minWidth: 240, weight: 240, order: 4 },
      { id: 'next-actions', name: 'Actions', minWidth: 240, weight: 240, order: 5 },
    ],
  },

  // ── Generic Object Workspace (fallback) ──
  object: {
    name: 'Object Workspace',
    overflow: 'stack',
    panels: [
      { id: 'object-identity', name: 'Identity', minWidth: 280, weight: 350, order: 0 },
      { id: 'ai-understanding', name: 'AI Understanding', minWidth: 280, weight: 1, order: 1 },
      { id: 'timeline', name: 'Activity', minWidth: 260, weight: 280, order: 2 },
      { id: 'related-objects', name: 'Related', minWidth: 240, weight: 260, order: 3 },
      { id: 'next-actions', name: 'Next Actions', minWidth: 240, weight: 240, order: 4 },
    ],
  },

  // ── Conversation ──
  conversation: {
    name: 'Conversation',
    overflow: 'overlay',
    panels: [
      { id: 'messages', name: 'Messages', minWidth: 300, weight: 1, order: 0 },
      { id: 'context', name: 'Context', minWidth: 280, weight: 350, order: 1 },
      { id: 'ai-assist', name: 'AI Assistant', minWidth: 260, weight: 300, order: 2 },
    ],
  },

  // ── Commitment ──
  commitment: {
    name: 'Commitment',
    overflow: 'stack',
    panels: [
      { id: 'graph', name: 'Execution Graph', minWidth: 280, weight: 450, order: 0 },
      { id: 'narrative', name: 'Progress Narrative', minWidth: 300, weight: 1, order: 1 },
      { id: 'ai-insight', name: 'AI Insight', minWidth: 280, weight: 380, order: 2 },
    ],
  },

  // ── Search Results ──
  search: {
    name: 'Search',
    overflow: 'stack',
    panels: [
      { id: 'results', name: 'Results', minWidth: 300, weight: 1, order: 0 },
      { id: 'preview', name: 'Preview', minWidth: 300, weight: 400, order: 1 },
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
export function fitPanels(layout: LayoutDefinition, availableWidth: number): PanelSlot[] {
  const sorted = [...layout.panels].sort((a, b) => a.order - b.order);
  if (layout.overflow === 'stack') {
    let remaining = availableWidth;
    const result: PanelSlot[] = [];
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
