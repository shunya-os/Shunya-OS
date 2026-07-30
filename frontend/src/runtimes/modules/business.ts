/**
 * Business Operations Module — Discovers and displays seeded demo data.
 *
 * Self-registering. Platform knows nothing about this module.
 * Remove from manifest to disable. Platform is unaffected.
 */

import { ShunyaModule } from '../module-registry';
import { WorkspaceRegistry } from '../composition/engine';

const BASE = '/api/v1';

async function json<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { credentials: 'include' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

const module: ShunyaModule = {
  id: 'business',
  name: 'Business Operations',

  discover: async () => {
    const data: Record<string, any> = {};
    // Discover available object types from the founder API
    try {
      const types = await json<{ data: Record<string, number> }>('/founder/objects/types');
      data.objectTypes = types.data ?? {};
      data.hasObjects = Object.keys(types.data ?? {}).length > 0;
    } catch { /* unavailable */ }

    // Fetch all objects if available
    if (data.hasObjects) {
      try {
        const objs = await json<{ data: any[]; count: number }>('/founder/objects');
        data.objects = objs.data ?? [];
        data.objectCount = objs.count ?? 0;
      } catch { /* unavailable */ }
    }

    // Also try legacy endpoints for relationships
    try {
      const rels = await json<{ relationships: any[] }>('/relationships/api/v1/relationships');
      data.relationships = rels.relationships ?? [];
      data.hasRelationships = data.relationships.length > 0;
    } catch { /* unavailable */ }

    return data;
  },

  register: async (data: Record<string, any>) => {
    const objs = data.objects ?? [];
    const rels = data.relationships ?? [];
    const types = data.objectTypes ?? {};
    const objCount = objs.length;
    void(rels); // kept for future use
    const typeList = Object.entries(types) as [string, number][];

    // Count by type
    const customers = typeList.find(([t]) => t === 'customer')?.[1] ?? 0;
    const invoices = typeList.find(([t]) => t === 'invoice')?.[1] ?? 0;
    const commitments = typeList.find(([t]) => t === 'commitment')?.[1] ?? 0;
    const conversations = typeList.find(([t]) => t === 'conversation')?.[1] ?? 0;
    const timeline = typeList.find(([t]) => t === 'timeline_event')?.[1] ?? 0;
    const notes = typeList.find(([t]) => t === 'note')?.[1] ?? 0;

    // Timeline milestones
    const milestones = objs.filter((o: any) => o.object_type === 'timeline_event');
    const activeConversations = objs.filter((o: any) => o.object_type === 'conversation');
    void activeConversations; // reserved for future panel
    const activeCommitments = objs.filter((o: any) => o.object_type === 'commitment');

    WorkspaceRegistry.register({
      id: 'home', name: 'Home', description: 'Your business at a glance',
      supportedObjectTypes: [], requiredRuntimes: [], layoutTemplate: 'home',
      panels: [
        { componentId: 'metric', dependsOn: [], critical: true, label: 'Customers',
          propsResolver: () => ({ value: customers, subtitle: customers > 0 ? 'Active customers' : 'No customers yet' }) },
        { componentId: 'metric', dependsOn: [], critical: true, label: 'Invoices',
          propsResolver: () => ({ value: invoices, subtitle: invoices > 0 ? 'Total invoices' : 'No invoices yet' }) },
        { componentId: 'metric', dependsOn: [], label: 'Commitments',
          propsResolver: () => ({ value: commitments, subtitle: commitments > 0 ? 'Active commitments' : 'No commitments' }) },
        { componentId: 'metric', dependsOn: [], label: 'Conversations',
          propsResolver: () => ({ value: conversations, subtitle: conversations > 0 ? 'Active conversations' : 'No conversations' }) },
        { componentId: 'insight-card', dependsOn: [], label: 'Business Overview',
          propsResolver: () => ({
            title: `${customers + invoices + commitments + conversations + timeline + notes} total records`,
            body: `${customers} customers · ${invoices} invoices · ${commitments} commitments · ${timeline} milestones · ${notes} notes`,
            confidence: 'high', type: 'summary',
          })},
        ...(milestones.length > 0 ? [{
          componentId: 'insight-card', dependsOn: [], label: 'Recent Milestones',
          propsResolver: () => {
            const recent = milestones.slice(0, 3);
            return {
              title: 'Milestones',
              body: recent.map((m: any) => {
                try { const d = JSON.parse(m.content ?? '{}'); return `• ${m.name}: ${d.text ?? ''}`; }
                catch { return `• ${m.name}`; }
              }).join('\n'),
              confidence: 'high' as const, type: 'observation',
            };
          },
        }] : []),
        ...(activeCommitments.length > 0 ? [{
          componentId: 'next-best-action', dependsOn: [], label: 'Next Action',
          propsResolver: () => {
            const atRisk = activeCommitments.find((c: any) => {
              try { return JSON.parse(c.content ?? '{}').status === 'at_risk'; }
              catch { return false; }
            });
            return {
              action: atRisk ? `Review: ${atRisk.name}` : `Explore your ${objCount} business records`,
              reason: atRisk ? `This commitment is at risk — review and update status` : `Your workspace has ${objCount} objects across ${Object.keys(types).length} types`,
              confidence: 'high' as const,
            };
          },
        }] : []),
      ],
    });

    WorkspaceRegistry.register({
      id: 'object', name: 'Object', description: 'Business object view',
      supportedObjectTypes: ['*'], requiredRuntimes: [], layoutTemplate: 'object',
      panels: [
        { componentId: 'object-identity', dependsOn: ['object'], label: 'Identity',
          propsResolver: (s: any) => ({ name: s.name ?? 'Unknown', type: s.object_type ?? 'object', status: s.status ?? 'active', id: s.object_id ?? '' }) },
        { componentId: 'insight-card', dependsOn: ['object'], label: 'Details',
          propsResolver: (s: any) => {
            const lines: string[] = [];
            if (s.content) lines.push(s.content);
            if (s.created_at) lines.push(`Created: ${new Date(s.created_at).toLocaleDateString()}`);
            if (s.updated_at) lines.push(`Updated: ${new Date(s.updated_at).toLocaleDateString()}`);
            const body = lines.length > 0 ? lines.join('\n') : 'No additional data';
            return { title: `${s.object_type ?? 'Object'} Data`, body, confidence: 'medium', type: 'observation' };
          }},
        { componentId: 'insight-card', dependsOn: ['object'], label: 'Properties',
          propsResolver: (s: any) => {
            const fields = [
              ['Name', s.name],
              ['Type', s.object_type],
              ['Status', s.status],
              ['Space', s.space_id],
              ['Created', s.created_at ? new Date(s.created_at).toLocaleString() : ''],
              ['Updated', s.updated_at ? new Date(s.updated_at).toLocaleString() : ''],
            ].filter(([,v]) => v);
            return {
              title: 'Properties',
              body: fields.map(([l, v]) => `${l}: ${v}`).join('\n'),
              confidence: 'high',
              type: 'summary',
            };
          }},
      ],
    });

    WorkspaceRegistry.register({
      id: 'conversation', name: 'Conversation', description: 'Business conversation context',
      supportedObjectTypes: ['conversation'], requiredRuntimes: [], layoutTemplate: 'conversation',
      panels: [
        { componentId: 'conversation-card', dependsOn: [], critical: true, label: 'Conversation',
          propsResolver: (s: any) => {
            try { const d = JSON.parse(s.content ?? '{}'); return { title: d.title ?? s.name, intent: d.objective ?? '', status: d.status ?? 'active', participants: d.participants ?? [], objectCount: 0 }; }
            catch { return { title: s.name, intent: '', status: 'active', participants: [], objectCount: 0 }; }
          }},
        { componentId: 'insight-card', dependsOn: [], label: 'AI Summary',
          propsResolver: (s: any) => {
            try { const d = JSON.parse(s.content ?? '{}'); const ai = d.ai_analysis ?? {}; return { title: 'AI Analysis', body: d.summary ?? 'No summary available', confidence: ai.confidence ?? 'medium', type: 'observation' }; }
            catch { return { title: 'AI Analysis', body: 'No summary available', confidence: 'medium', type: 'observation' }; }
          }},
      ],
    });

    WorkspaceRegistry.register({
      id: 'commitment', name: 'Commitment', description: 'Execution tracking',
      supportedObjectTypes: ['commitment'], requiredRuntimes: [], layoutTemplate: 'commitment',
      panels: [
        { componentId: 'progress-bar', dependsOn: [], critical: true, label: 'Progress',
          propsResolver: (s: any) => {
            try { const d = JSON.parse(s.content ?? '{}'); return { value: d.progress ?? 0, label: 'Commitment progress' }; }
            catch { return { value: 0, label: 'Commitment progress' }; }
          }},
        { componentId: 'confidence-meter', dependsOn: [], label: 'Confidence',
          propsResolver: (s: any) => {
            try { const d = JSON.parse(s.content ?? '{}'); return { score: d.confidence ?? 0, factors: d.confidence_factors ?? [] }; }
            catch { return { score: 0, factors: [] }; }
          }},
        { componentId: 'blocker-list', dependsOn: [], label: 'Blockers',
          propsResolver: (s: any) => {
            try { const d = JSON.parse(s.content ?? '{}'); return { blockers: d.risks ?? [] }; }
            catch { return { blockers: [] }; }
          }},
        { componentId: 'next-best-action', dependsOn: [], label: 'Next Action',
          propsResolver: (s: any) => {
            try { const d = JSON.parse(s.content ?? '{}'); return { action: d.next_action ?? 'Review commitment', reason: `Progress: ${Math.round((d.progress ?? 0) * 100)}% · Confidence: ${Math.round((d.confidence ?? 0) * 100)}%`, confidence: (d.confidence ?? 0) >= 0.7 ? 'high' as const : (d.confidence ?? 0) >= 0.4 ? 'medium' as const : 'low' as const }; }
            catch { return { action: 'Review commitment', reason: 'No data available', confidence: 'low' as const }; }
          }},
      ],
    });
  },

  search: async (query: string) => {
    const q = query.toLowerCase();
    const hits: { id: string; type: string; title: string; subtitle: string; status?: string }[] = [];
    try {
      const objs = await json<{ data: any[] }>('/founder/objects');
      for (const o of objs.data ?? []) {
        if ((o.name ?? '').toLowerCase().includes(q))
          hits.push({ id: o.object_id ?? o.id, type: o.object_type ?? 'object', title: o.name, subtitle: o.object_type, status: o.status });
      }
    } catch { /* skip */ }
    return hits;
  },

  ask: async (_question: string) => {
    // Rich AI response based on seeded data
    try {
      const types = await json<{ data: Record<string, number> }>('/founder/objects/types').catch(() => null);
      const counts = types?.data ?? {};
      const total = Object.values(counts).reduce((a: number, b: number) => a + b, 0);
      if (total > 0) {
        const summary = Object.entries(counts).map(([t, c]) => `${c} ${t}`).join(', ');

        // Check for at-risk commitments
        let atRisk = '';
        try {
          const objs = await json<{ data: any[] }>('/founder/objects');
          const risky = objs.data.filter((o: any) => {
            try { const d = JSON.parse(o.content ?? '{}'); return d.status === 'at_risk'; }
            catch { return false; }
          });
          if (risky.length > 0) {
            atRisk = `\n⚠️ ${risky.length} commitment(s) at risk: ${risky.map((r: any) => r.name).join(', ')}`;
          }
        } catch { /* skip */ }

        return `Based on your business data: ${total} records found (${summary}).${atRisk}\n\nAsk me about specific customers, invoices, or commitments.`;
      }
      return null;
    } catch { return null; }
  },
};

export default module;