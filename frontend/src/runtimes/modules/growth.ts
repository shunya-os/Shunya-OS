/**
 * G5 — Campaign Growth Workspace Module
 *
 * Integrates into the existing SHUNYA workspace architecture.
 * No generic marketing dashboard. No walls of charts.
 *
 * Follows:
 *   70% calm whitespace
 *   20% contextual information
 *   10% controls
 *
 * Registers:
 *   - Campaign context panel (when viewing a campaign)
 *   - Growth pulse panel (home view)
 *   - Campaign search
 *   - Campaign Q&A
 *
 * Uses real G5 API at /api/v1/growth/
 * Integrates with G4 commercial for end-to-end outcome visibility.
 */

import { ShunyaModule } from '../module-registry';
import { WorkspaceRegistry } from '../composition/engine';
import { layouts } from '../layout/engine';

const BASE = '/api/v1/growth';

async function json<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { credentials: 'include' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

interface CampaignBrief {
  id: number;
  name: string;
  description: string;
  objective: string;
  status: string;
  budget: string;
  start_date: string | null;
  end_date: string | null;
  utm_source: string;
  utm_campaign: string;
  utm_medium: string;
  created_by: string;
  created_at: string;
}

interface IntelAssessment {
  has_response: boolean;
  has_conversion: boolean;
  has_learning: boolean;
  roi_known: boolean;
  total_interactions: number;
  total_attributions: number;
  total_revenue: string;
  roi: string;
}

interface IntelResponse {
  campaign: CampaignBrief;
  assessment: IntelAssessment;
  interaction_summary: { by_type: Record<string, number>; by_source: Record<string, number> };
  what_is_working: any[];
  what_needs_attention: any[];
  actionable_recommendations: any[];
  recent_events: any[];
  insufficient_evidence: boolean;
  confidence_summary: string;
}

async function discoverCampaigns(): Promise<Record<string, any>> {
  const data: Record<string, any> = {};
  try {
    // List campaigns from marketing OS
    const resp = await fetch('/api/v1/marketing/campaigns?tenant_id=1', { credentials: 'include' });
    const campaigns = resp.ok ? (await resp.json()).campaigns ?? [] : [];
    data.campaigns = campaigns;
    data.totalCampaigns = campaigns.length;
    data.activeCampaigns = campaigns.filter((c: any) => c.status === 'active').length;

    // Get growth overview
    try {
      const overview = await json<{ success: boolean; overview: any }>('/intelligence/overview');
      data.overview = overview.overview ?? {};
    } catch {
      data.overview = {};
    }

    // Get intelligence for active campaigns
    const intelMap: Record<number, IntelResponse> = {};
    for (const c of campaigns.slice(0, 10)) {
      try {
        const intel = await json<{ success: boolean; intelligence: IntelResponse }>(`/intelligence/${c.id}`);
        if (intel.success) intelMap[c.id] = intel.intelligence;
      } catch {}
    }
    data.intelligenceMap = intelMap;

    // Get learnings
    try {
      const lr = await json<{ success: boolean; learnings: any[] }>('/learnings');
      data.learnings = lr.learnings ?? [];
      data.hasActionableLearnings = lr.learnings?.some((l: any) => l.is_actionable) ?? false;
    } catch {
      data.learnings = [];
      data.hasActionableLearnings = false;
    }
  } catch {
    data.campaigns = [];
    data.totalCampaigns = 0;
  }
  return data;
}

const module: ShunyaModule = {
  id: 'growth',
  name: 'Growth & Campaigns',

  discover: async () => {
    return discoverCampaigns();
  },

  register: async (_data: Record<string, any>) => {
    const overview = _data.overview ?? {};
    const intelMap: Record<number, IntelResponse> = _data.intelligenceMap ?? {};
    const totalCampaigns = _data.totalCampaigns ?? 0;
    const activeCampaigns = _data.activeCampaigns ?? 0;
    const hasActionableLearnings = _data.hasActionableLearnings ?? false;

    // Add campaign panel slot to the campaign layout (via existing layouts)
    if (layouts.customer) {
      const panels = layouts.customer.panels;
      if (!panels.find(p => p.id === 'campaign-context')) {
        panels.push({
          id: 'campaign-context',
          name: 'Campaign Context',
          minWidth: 260,
          weight: 280,
          order: 3,
        });
      }
    }

    // Register workspace panels for campaign object view
    WorkspaceRegistry.register({
      id: 'campaign-workspace',
      name: 'Campaign',
      description: 'Campaign context — what is happening, what matters, what is emerging',
      supportedObjectTypes: ['campaign'],
      requiredRuntimes: ['object'],
      layoutTemplate: 'customer',
      panels: [
        {
          componentId: 'campaign-status',
          dependsOn: ['object'],
          critical: false,
          label: 'Campaign Status',
          propsResolver: (state: Record<string, unknown>) => {
            const s = state as any;
            const campId = s?.data?.id ?? s?.id;
            const intel = campId ? intelMap[campId] : null;
            if (intel) {
              const assessment = intel.assessment;
              const lines: string[] = [];
              lines.push(`Status: ${intel.campaign.status}`);
              lines.push(`Objective: ${intel.campaign.objective}`);
              if (assessment.has_response) lines.push(`${assessment.total_interactions} interactions recorded`);
              if (assessment.has_conversion) lines.push(`Revenue: ${assessment.total_revenue}`);
              if (assessment.roi_known) lines.push(`ROI: ${assessment.roi}`);
              if (assessment.has_learning) lines.push('Insights available');
              if (intel.insufficient_evidence) lines.push('Insufficient data for assessment');
              return {
                title: intel.campaign.name || 'Campaign',
                body: lines.join('  ·  '),
                confidence: assessment.has_response ? ('medium' as const) : ('low' as const),
                type: 'summary' as const,
              };
            }
            return {
              title: 'Campaign',
              body: 'No data available yet. Campaign intelligence will appear once interactions and outcomes are recorded.',
              confidence: 'low' as const,
              type: 'observation' as const,
            };
          },
        },
        {
          componentId: 'insight-card',
          dependsOn: ['object'],
          label: 'What Is Happening',
          propsResolver: (state: Record<string, unknown>) => {
            const s = state as any;
            const campId = s?.data?.id ?? s?.id;
            const intel = campId ? intelMap[campId] : null;
            if (!intel) {
              return {
                title: 'Awaiting Data',
                body: 'Set up campaign tracking to see what is happening.',
                confidence: 'low' as const,
                type: 'observation' as const,
              };
            }
            if (intel.insufficient_evidence) {
              return {
                title: 'Insufficient Evidence',
                body: 'Not enough data to assess campaign performance yet. Continue capturing interactions and tracking responses.',
                confidence: 'low' as const,
                type: 'observation' as const,
              };
            }
            const parts: string[] = [];
            const byType = intel.interaction_summary.by_type;
            const topType = Object.entries(byType).sort(([, a], [, b]) => b - a).slice(0, 3);
            if (topType.length > 0) {
              parts.push(`Top interactions: ${topType.map(([k, v]) => `${k}(${v})`).join(', ')}`);
            }
            if (intel.what_is_working.length > 0) {
              parts.push(`Working: ${intel.what_is_working.map((l: any) => l.title).join(', ')}`);
            }
            if (intel.what_needs_attention.length > 0) {
              parts.push(`Needs attention: ${intel.what_needs_attention.length} items`);
            }
            return {
              title: 'What Is Happening',
              body: parts.length > 0 ? parts.join('  ·  ') : 'Campaign active — no patterns detected yet.',
              confidence: intel.assessment.has_response ? ('medium' as const) : ('low' as const),
              type: 'summary' as const,
            };
          },
        },
        {
          componentId: 'next-best-action',
          dependsOn: ['object'],
          label: 'Next Action',
          propsResolver: (state: Record<string, unknown>) => {
            const s = state as any;
            const campId = s?.data?.id ?? s?.id;
            const intel = campId ? intelMap[campId] : null;
            if (intel && intel.actionable_recommendations && intel.actionable_recommendations.length > 0) {
              const rec = intel.actionable_recommendations[0];
              return {
                action: rec.recommendation_action || 'Review campaign',
                reason: rec.recommendation || rec.title,
                confidence: rec.recommendation_confidence >= 70 ? ('high' as const) : ('medium' as const),
              };
            }
            if (intel?.insufficient_evidence) {
              return {
                action: 'Set up campaign tracking',
                reason: 'Connect sources and capture interactions to enable campaign intelligence.',
                confidence: 'low' as const,
              };
            }
            return {
              action: 'Monitor campaign activity',
              reason: totalCampaigns > 0 ? 'Campaign is active — responses and outcomes will appear here.' : 'No campaigns yet. Create a campaign to get started.',
              confidence: 'low' as const,
            };
          },
        },
      ],
    });

    // Register home panel showing growth pulse
    WorkspaceRegistry.register({
      id: 'growth-pulse',
      name: 'Growth Pulse',
      description: 'At-a-glance campaign and growth awareness',
      supportedObjectTypes: [],
      requiredRuntimes: [],
      layoutTemplate: 'home',
      panels: [
        {
          componentId: 'metric',
          dependsOn: [],
          critical: false,
          label: 'Campaigns',
          propsResolver: () => ({
            value: totalCampaigns,
            subtitle: activeCampaigns > 0 ? `${activeCampaigns} active` : 'No active campaigns',
          }),
        },
        {
          componentId: 'metric',
          dependsOn: [],
          critical: false,
          label: 'Attributed Revenue',
          propsResolver: () => ({
            value: overview.total_attributed_revenue ?? '0',
            subtitle: overview.total_interactions > 0 ? `${overview.total_interactions} interactions tracked` : 'No revenue attributed yet',
          }),
        },
        {
          componentId: 'metric',
          dependsOn: [],
          critical: false,
          label: 'Learnings',
          propsResolver: () => ({
            value: overview.total_learnings ?? 0,
            subtitle: hasActionableLearnings ? 'Actionable insights available' : 'No insights yet',
            variant: hasActionableLearnings ? ('warning' as const) : ('neutral' as const),
          }),
        },
        {
          componentId: 'insight-card',
          dependsOn: [],
          label: 'Growth Pulse',
          propsResolver: () => {
            const lines: string[] = [];
            if (totalCampaigns > 0) {
              lines.push(`${totalCampaigns} campaign(s)`);
              if (activeCampaigns > 0) lines.push(`${activeCampaigns} active`);
            }
            if (overview.total_attributed_revenue && parseFloat(overview.total_attributed_revenue) > 0) {
              lines.push(`Revenue: ${overview.total_attributed_revenue}`);
            }
            if (overview.total_interactions > 0) {
              lines.push(`Interactions: ${overview.total_interactions}`);
            }
            if (overview.total_learnings > 0) {
              lines.push(`${overview.total_learnings} insight(s)`);
              if (hasActionableLearnings) lines.push('Actionable recommendations available');
            }
            return {
              title: 'Growth Pulse',
              body: lines.length > 0 ? lines.join('\n') : 'No campaign activity yet. Create a campaign to get started.',
              confidence: totalCampaigns > 0 ? ('medium' as const) : ('low' as const),
              type: 'summary' as const,
            };
          },
        },
      ],
    });
  },

  search: async (query: string): Promise<{ id: string; type: string; title: string; subtitle: string; status?: string }[]> => {
    try {
      const resp = await fetch('/api/v1/marketing/campaigns?tenant_id=1', { credentials: 'include' });
      if (!resp.ok) return [];
      const data = await resp.json();
      const campaigns = data.campaigns ?? [];
      return campaigns
        .filter((c: any) =>
          c.name?.toLowerCase().includes(query.toLowerCase()) ||
          c.description?.toLowerCase().includes(query.toLowerCase()) ||
          c.objective?.toLowerCase().includes(query.toLowerCase())
        )
        .map((c: any) => ({
          id: String(c.id),
          type: 'campaign',
          title: c.name ?? 'Unknown',
          subtitle: `${c.objective ?? 'awareness'} · ${c.status}`,
          status: c.status,
        }));
    } catch {
      return [];
    }
  },

  ask: async (_question: string): Promise<string | null> => {
    // For now, return null — campaign Q&A can be added via the AI engine
    return null;
  },
};

export default module;