/**
 * G4 Commercial Context Module — Integrates commercial context into
 * the existing workspace architecture.
 *
 * No CRM dashboard. No pipeline. No sidebar modules.
 *
 * When a user is viewing a relationship/object, this module adds:
 * - Commercial context panel: "What matters about this relationship right now?"
 * - Opportunity/need state
 * - Active proposals
 * - Next commercial actions
 * - Relevant commercial history
 *
 * Uses the real G4 API at /api/v1/commercial/
 */

import { ShunyaModule } from '../module-registry';
import { WorkspaceRegistry } from '../composition/engine';
import { layouts } from '../layout/engine';

const BASE = '/api/v1/commercial';

async function json<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { credentials: 'include' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

const module: ShunyaModule = {
  id: 'commercial',
  name: 'Commercial Context',

  discover: async () => {
    const data: Record<string, any> = {};

    // Discover commercial intelligence snapshot
    try {
      const intelligence = await json<{ success: boolean; intelligence: any }>('/intelligence');
      data.intelligence = intelligence.intelligence ?? {};
      data.hasCommercialData = (intelligence.intelligence?.total_opportunities ?? 0) > 0;
    } catch {
      data.intelligence = {};
      data.hasCommercialData = false;
    }

    // Discover commercial types (config-driven vocabulary)
    try {
      const types = await json<{ success: boolean; types: any[] }>('/types');
      data.types = types.types ?? [];
    } catch {
      data.types = [];
    }

    // Discover attention items
    try {
      const attention = await json<{ success: boolean; needs_attention: any[]; upcoming_follow_ups: any[] }>('/attention');
      data.needsAttention = attention.needs_attention ?? [];
      data.upcomingFollowUps = attention.upcoming_follow_ups ?? [];
      data.attentionCount = attention.needs_attention?.length ?? 0;
    } catch {
      data.needsAttention = [];
      data.upcomingFollowUps = [];
      data.attentionCount = 0;
    }

    return data;
  },

  register: async (_data: Record<string, any>) => {
    const intelligence = _data.intelligence ?? {};
    const needsAttention = _data.needsAttention ?? [];
    const attentionCount = _data.attentionCount ?? 0;
    const hasData = _data.hasCommercialData ?? false;

    // Add commercial-context panel slot to the customer layout
    if (layouts.customer) {
      const existingPanels = layouts.customer.panels;
      const commercialPanel = {
        id: 'commercial-context',
        name: 'Commercial Context',
        minWidth: 260,
        weight: 280,
        order: 1.5,
      };
      if (!existingPanels.find(p => p.id === 'commercial-context')) {
        existingPanels.splice(2, 0, commercialPanel);
      }
    }

    // Register workspace panels for relationship/commercial object view
    WorkspaceRegistry.register({
      id: 'relationship-commercial',
      name: 'Relationship Commercial',
      description: 'Commercial context for a relationship',
      supportedObjectTypes: ['relationship', 'customer', 'person', 'contact'],
      requiredRuntimes: ['object'],
      layoutTemplate: 'customer',
      panels: [
        {
          componentId: 'commercial-context',
          dependsOn: ['object'],
          critical: false,
          label: 'Commercial Context',
          propsResolver: (state: Record<string, unknown>) => {
            const objState = state as any;
            const relId = objState?.data?.relationship?.id ?? objState?.data?.id ?? objState?.id;
            return {
              relationshipId: relId,
              organizationId: objState?.data?.organization_id ?? 1,
            };
          },
        },
        {
          componentId: 'insight-card',
          dependsOn: ['object'],
          label: 'Commercial Overview',
          propsResolver: () => {
            if (!hasData) {
              return {
                title: 'No Commercial Data',
                body: 'This relationship has no recorded commercial activity. Commercial context will appear here when opportunities, proposals, or needs are identified.',
                confidence: 'low' as const,
                type: 'observation' as const,
              };
            }
            const lines: string[] = [];
            if (intelligence.total_opportunities > 0) {
              lines.push(`${intelligence.total_opportunities} opportunity(-ies) tracked`);
            }
            if (intelligence.total_active_value > 0) {
              lines.push(`Active value: ${intelligence.total_active_value}`);
            }
            if (intelligence.needs_attention_count > 0) {
              lines.push(`${intelligence.needs_attention_count} need(s) attention`);
            }
            if (intelligence.urgent_opportunities > 0) {
              lines.push(`${intelligence.urgent_opportunities} urgent`);
            }
            return {
              title: 'Commercial Overview',
              body: lines.length > 0 ? lines.join('  ·  ') : 'No commercial activity',
              confidence: 'medium' as const,
              type: 'summary' as const,
            };
          },
        },
        {
          componentId: 'next-best-action',
          dependsOn: ['object'],
          label: 'Next Commercial Action',
          propsResolver: (state: Record<string, unknown>) => {
            const s = state as any;
            const relId = s?.data?.relationship?.id ?? s?.data?.id ?? s?.id;
            const forThisRel = needsAttention.find((n: any) =>
              n.relationship_id === relId || String(n.relationship_id) === String(relId)
            );
            if (forThisRel) {
              const reasons = forThisRel.attention_reasons ?? [];
              return {
                action: forThisRel.next_action || 'Review opportunity',
                reason: reasons[0] || `Opportunity "${forThisRel.title}" needs attention`,
                confidence: 'high' as const,
              };
            }
            return {
              action: 'Explore commercial context',
              reason: hasData ? 'Commercial data available — open a relationship to see context' : 'No pending commercial actions',
              confidence: 'low' as const,
            };
          },
        },
      ],
    });

    // Register home overview panel showing commercial pulse
    WorkspaceRegistry.register({
      id: 'commercial-pulse',
      name: 'Commercial Pulse',
      description: 'At-a-glance commercial awareness',
      supportedObjectTypes: [],
      requiredRuntimes: [],
      layoutTemplate: 'home',
      panels: [
        {
          componentId: 'metric',
          dependsOn: [],
          critical: false,
          label: 'Opportunities',
          propsResolver: () => ({
            value: intelligence.total_opportunities ?? 0,
            subtitle: intelligence.total_opportunities > 0 ? 'Active opportunities' : 'No opportunities yet',
          }),
        },
        {
          componentId: 'metric',
          dependsOn: [],
          critical: false,
          label: 'Needs Attention',
          propsResolver: () => ({
            value: attentionCount,
            subtitle: attentionCount > 0
              ? `${attentionCount} opportunity(-ies) need attention`
              : 'All opportunities on track',
            variant: attentionCount > 0 ? ('warning' as const) : ('neutral' as const),
          }),
        },
        {
          componentId: 'insight-card',
          dependsOn: [],
          label: 'Commercial Pulse',
          propsResolver: () => {
            const lines: string[] = [];
            if (intelligence.total_opportunities > 0) {
              const dist = intelligence.state_distribution ?? {};
              const stateLabels: Record<string, string> = {
                discovered: 'New', active: 'Active', waiting: 'Waiting',
                proposal_pending: 'Proposal Sent', accepted: 'Accepted',
                committed: 'Committed', executing: 'Executing', lost: 'Lost',
              };
              const parts = Object.entries(dist)
                .filter(([, count]) => (count as number) > 0)
                .map(([state, count]) => `${stateLabels[state] ?? state}: ${count}`);
              if (parts.length > 0) lines.push(parts.join(' · '));
            }
            if (intelligence.total_active_value > 0) {
              lines.push(`Total active value: ${intelligence.total_active_value}`);
            }
            if (attentionCount > 0) {
              const urgent = intelligence.urgent_opportunities ?? 0;
              if (urgent > 0) lines.push(`${urgent} urgent`);
            }
            return {
              title: 'Commercial Pulse',
              body: lines.length > 0 ? lines.join('\n') : 'No commercial activity yet',
              confidence: hasData ? 'medium' as const : 'low' as const,
              type: 'summary' as const,
            };
          },
        },
      ],
    });
  },

  /** Search across commercial opportunities. */
  search: async (query: string): Promise<{ id: string; type: string; title: string; subtitle: string; status?: string }[]> => {
    try {
      const resp = await fetch(`${BASE}/opportunities?state=&limit=10`, { credentials: 'include' });
      if (!resp.ok) return [];
      const data = await resp.json();
      const opps = data.opportunities ?? [];
      return opps
        .filter((o: any) =>
          o.title?.toLowerCase().includes(query.toLowerCase()) ||
          o.description?.toLowerCase().includes(query.toLowerCase())
        )
        .map((o: any) => ({
          id: String(o.id),
          type: 'opportunity',
          title: o.title ?? 'Unknown',
          subtitle: o.lifecycle_state ?? 'discovered',
          status: o.lifecycle_state,
        }));
    } catch {
      return [];
    }
  },

  /** Answer a commercial intelligence question. */
  ask: async (question: string): Promise<string | null> => {
    try {
      const resp = await fetch(`${BASE}/intelligence/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ question }),
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      return data.answer ?? null;
    } catch {
      return null;
    }
  },
};

export default module;