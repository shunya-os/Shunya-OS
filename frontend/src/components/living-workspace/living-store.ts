/**
 * SHUNYA LX-01 — Living Workspace Store
 *
 * ── Memory Architecture (LX-05) ─────────────────────────────────────
 *   Session Memory  — discarded when founder closes (interactionHistory, observations, realityEvents)
 *   Founder Memory   — explainable, reviewable, resettable (founderPreferences, reflectionMessages)
 *   Business Memory  — permanent canonical truth (objects, relationships, outcomes from Reality Engine)
 *
 * SHUNYA remembers businesses permanently, remembers founders intentionally,
 * and remembers sessions temporarily. These three forms of memory shall never be confused.
 *
 * Polls backend APIs to continuously refresh reality, understanding, and objects.
 *
 * LX-45: Frontend adaptation is acceptable as an experience prototype until Launch Candidate.
 */

import { create } from 'zustand';
import { bus } from '../../runtimes/event-bus';
import type {
  LivingWorkspaceState,
  RealityEvent,
  AIObservation,
  AIRecommendation,
  Execution,
  LivingObject,
  AwarenessSignal,
} from './types';

// ── Constants ────────────────────────────────────────────────────────

// ── Adaptation Types ────────────────────────────────────────────────

interface InteractionRecord {
  timestamp: string;
  actionType: string;
  actionLabel: string;
  objectType?: string;
  outcome?: 'executed' | 'dismissed' | 'completed' | 'failed';
}

interface FounderPreference {
  /** Pattern: action types the founder prefers for specific object types */
  preferredActions: Record<string, string[]>;  // object_type → list of action labels
  /** Pattern: object types the founder engages with most */
  activeObjectTypes: string[];
  /** Pattern: timing — what urgency levels the founder actually acts on */
  actedOnUrgency: string[];  // 'now' | 'today' | 'this_week' — which ones get action
  /** Pattern: how often the founder uses quick action vs. expanded exploration */
  prefersQuickAction: boolean;
  /** Updated as confidence grows */
  confidence: number;  // 0.0 - 1.0 — how well SHUNYA knows this founder
  /** How many interactions SHUNYA has observed */
  totalInteractions: number;
  /** Whether the founder tends to approve prepared actions */
  approvesPreparedActions: boolean;
}

interface ReflectionMessage {
  id: string;
  message: string;
  type: 'learning' | 'observation' | 'adaptation';
  timestamp: string;
  seen: boolean;
}

// ── Helpers ──────────────────────────────────────────────────────────

function timestamp(): string {
  return new Date().toISOString();
}

// ── Store ────────────────────────────────────────────────────────────

interface LivingStore extends LivingWorkspaceState {
  // Actions
  fetchReality: () => Promise<void>;
  fetchInsights: () => Promise<void>;
  fetchLivingObjects: () => Promise<void>;
  executeAction: (actionType: string, payload: Record<string, unknown>) => Promise<void>;
  expandObject: (id: string | null) => void;
  toggleSidebar: () => void;
  setCommandOpen: (open: boolean) => void;
  setFounderName: (name: string) => void;
  dismissRecommendation: (id: string) => void;
  dismissObservation: (id: string) => void;
  startPolling: () => () => void;

  // Awareness
  acknowledgeSignal: (id: string) => void;
  dismissSignal: (id: string) => void;
  snoozeSignal: (id: string) => void;
  addAwarenessSignal: (signal: AwarenessSignal) => void;

  // ── LX-04 Adaptation ──
  interactionHistory: InteractionRecord[];
  founderPreferences: FounderPreference;
  reflectionMessages: ReflectionMessage[];
  observeAction: (record: Omit<InteractionRecord, 'timestamp'>) => void;
  dismissReflection: (id: string) => void;
  getAdaptationContext: () => string | null;
  /** LX-05: Reset founder memory — explainable, reviewable, resettable */
  resetFounderMemory: () => void;
}

export const useLivingStore = create<LivingStore>((set, get) => ({
  // ── Initial State ──
  realityEvents: [],
  realityLoading: false,
  realityError: null,
  realityPollTime: '',

  observations: [],
  activeReasoning: null,
  reasoningHistory: [],

  recommendations: [],
  activeRecommendation: null,

  activeExecutions: [],
  executionHistory: [],

  livingObjects: [],
  expandedObjectId: null,
  objectsLoading: false,

  // ── Awareness ──
  awarenessSignals: [],
  awarenessCount: 0,
  awarenessCalm: true,

  founderName: 'Founder',
  lastUpdated: timestamp(),
  sidebarCollapsed: false,
  commandOpen: false,

  // ── LX-04 Adaptation State ──
  interactionHistory: [],
  founderPreferences: {
    preferredActions: {},
    activeObjectTypes: [],
    actedOnUrgency: [],
    prefersQuickAction: true,
    confidence: 0.0,
    totalInteractions: 0,
    approvesPreparedActions: false,
  },
  reflectionMessages: [],

  // ── Reality ──
  fetchReality: async () => {
      // Only set loading on the very first load — never flash on subsequent polls
      if (get().realityEvents.length === 0) {
        set({ realityLoading: true, realityError: null });
      }
      const pollTimestamp = timestamp();
      try {
        const params = new URLSearchParams({
          workspace_type: 'founder',
          workspace_id: 'default',
        });
        const resp = await fetch(`/api/v1/reality?${params}`, { credentials: 'include' });
        if (!resp.ok) throw new Error(`Reality Engine error (${resp.status})`);
        const json = await resp.json();
        if (json.success && json.data) {
          const d = json.data;

          // Reality events from projection
          const events: RealityEvent[] = (d.events || []).map((a: any, i: number) => ({
            id: a.event_id || `evt-${i}`,
            type: a.type || 'system_event',
            title: a.title,
            description: a.description || a.title,
            object_type: a.object_type,
            object_id: a.object_id,
            object_name: a.object_name,
            timestamp: a.timestamp,
            actor: a.actor,
            importance: a.importance || 'normal',
          }));

          // Attention items → recommendations
          const recommendations: AIRecommendation[] = (d.attention_items || []).map((a: any) => ({
            id: a.item_id,
            title: a.label,
            description: a.description,
            action_label: a.label.startsWith('Observation:') ? 'Review observation'
              : a.label.startsWith('Decision:') ? 'Review decision'
              : a.label.startsWith('Insight:') ? 'Explore insight'
              : 'Take action',
            action_type: 'outcome',
            action_payload: { name: 'process_attention', data: { item_id: a.item_id, source_type: a.source_type } },
            confidence: a.priority_score || a.signals?.evidence_confidence || 0.5,
            urgency: a.priority_score >= 0.7 ? 'now' : a.priority_score >= 0.4 ? 'today' : 'this_week',
            source_observation: a.label,
          }));

          // Living objects from projection
          const objects: LivingObject[] = (d.objects || d.living_objects || []).map((o: any) => ({
            id: o.id,
            object_id: o.object_id || o.id,
            object_type: o.object_type,
            name: o.name,
            current_stage: o.current_stage || 'Active',
            story: o.story || [],
            stage_history: o.stage_history || [],
            stage_pipeline: o.stage_pipeline || [],
            summary: o.summary || `${o.count || 0} ${o.object_type || 'object'}(s)`,
            time_narrative: o.time_narrative || 'Recently updated',
            recommendation: o.recommendation || {
              label: 'Review Record',
              type: 'navigate',
              confidence: 0.5,
              reasoning: 'Keeping records current ensures SHUNYA provides accurate insights.',
            },
            next_action: o.next_action ? {
              label: o.next_action.label || `View ${o.object_type}`,
              description: o.recommendation?.reasoning || '',
              action_type: o.next_action.action_type || 'navigate',
              action_payload: { type: o.object_type },
              confidence: o.next_action.confidence || 0.8,
              is_primary: true,
            } : null,
            alternative_actions: [],
            relationships: (o.relationships || []).map((r: any) => ({
              object_name: r.target_name,
              object_id: r.target_id,
              explanation: r.explanation || 'Related entity',
              relationship: r.type || 'relates_to',
              direction: r.direction || 'outbound',
              confidence: r.confidence || 0.5,
            })),
            data: { count: o.count },
            created_at: '',
            updated_at: '',
            status: 'active',
          }));

          // Briefing data — used by ExecutiveBriefing component
          set({
            realityEvents: events,
            recommendations,
            livingObjects: objects,
            activeExecutions: [],
            observations: [],
            lastUpdated: d.timestamp || timestamp(),
            realityPollTime: pollTimestamp,
            realityLoading: false,
          });
        } else {
          throw new Error(json.error || 'No reality data');
        }
      } catch (e) {
        set({
          realityError: e instanceof Error ? e.message : 'Failed to load reality',
          realityLoading: false,
        });
      }
    },

  // ── AI Insights ──
  fetchInsights: async () => {
    try {
      const resp = await fetch('/api/v1/ai/insights', { credentials: 'include' });
      if (!resp.ok) return;
      const json = await resp.json();
      if (json.success && Array.isArray(json.data) && json.data.length > 0) {
        const observations: AIObservation[] = json.data.map((i: any, idx: number) => ({
          id: `obs-${idx}-${Date.now()}`,
          title: i.title,
          description: i.description,
          type: i.type || 'insight',
          confidence: i.confidence || 0.8,
          evidence: i.evidence || '',
          source: i.source || 'AI Runtime',
          timestamp: timestamp(),
        }));
        set((s) => ({
          observations: [...observations, ...s.observations].slice(0, 20),
        }));
      }
    } catch {
      // silent — insights are advisory
    }
  },

  // ── Living Objects ──
  fetchLivingObjects: async () => {
    set({ objectsLoading: true });
    try {
      const resp = await fetch('/api/v1/objects/types', { credentials: 'include' });
      if (!resp.ok) return;
      const json = await resp.json();
      if (json.success && json.data) {
        const types = Object.keys(json.data);
        const objects: LivingObject[] = [];
        const existing = get().livingObjects;
        const existingMap = new Map(existing.map((o) => [o.object_type, o]));

        for (const type of types.slice(0, 8)) {
          const prev = existingMap.get(type);
          objects.push({
            id: `obj-${type}`,
            object_id: '',
            object_type: type,
            name: type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
            current_stage: prev?.current_stage || 'Active',
            story: prev?.story || [],
            stage_history: prev?.stage_history || [],
            stage_pipeline: prev?.stage_pipeline || [],
            summary: prev?.summary || `Active ${type.replace(/_/g, ' ')}`,
            time_narrative: prev?.time_narrative || 'Recently updated',
            recommendation: prev?.recommendation || {
              label: 'Review Record',
              type: 'navigate',
              confidence: 0.5,
              reasoning: 'Keeping records current ensures SHUNYA provides accurate insights.',
            },
            next_action: {
              label: `Create ${type.replace(/_/g, ' ')}`,
              description: `Start a new ${type.replace(/_/g, ' ')}`,
              action_type: 'outcome',
              action_payload: { name: `create_${type}`, data: {} },
              confidence: 0.85,
              is_primary: true,
            },
            alternative_actions: [],
            relationships: [],
            data: {},
            created_at: '',
            updated_at: '',
            status: 'active',
          });
        }
        set({ livingObjects: objects, objectsLoading: false });
      }
    } catch {
      set({ objectsLoading: false });
    }
  },

  // ── Actions ──
  executeAction: async (actionType, payload) => {
    const executionId = `exec-${Date.now()}`;
    const actionLabel = (payload.label as string) || 'Executing action…';
    const objectType = (payload.type as string) || (payload.name as string) || undefined;
    const exec: Execution = {
      id: executionId,
      label: actionLabel,
      description: '',
      status: 'in_progress',
      progress: 0,
      started_at: timestamp(),
    };
    set((s) => ({ activeExecutions: [...s.activeExecutions, exec] }));

    // Record the action for adaptation
    get().observeAction({
      actionType,
      actionLabel,
      objectType,
      outcome: 'executed',
    });

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      set((s) => ({
        activeExecutions: s.activeExecutions.map((e) =>
          e.id === executionId
            ? { ...e, progress: Math.min(e.progress + 0.15, 0.9) }
            : e
        ),
      }));
    }, 2000);

    try {
      let result: any;
      if (actionType === 'outcome') {
        const resp = await fetch('/outcomes/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(payload),
        });
        result = await resp.json();
      } else {
        // Generic API call
        const resp = await fetch(
          `/api/v1/objects/${encodeURIComponent((payload as any).type || '')}`,
          { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify(payload) }
        );
        result = await resp.json();
      }

      clearInterval(progressInterval);

      const completed: Execution = {
        id: executionId,
        label: exec.label,
        description: '',
        status: result.success ? 'completed' : 'failed',
        progress: result.success ? 1.0 : 0.0,
        started_at: exec.started_at,
        completed_at: timestamp(),
        outcome: result.message || result.explanation || (result.success ? 'Completed' : 'Failed'),
        error: result.error,
      };

      set((s) => ({
        activeExecutions: s.activeExecutions.filter((e) => e.id !== executionId),
        executionHistory: [...s.executionHistory, completed],
        realityEvents: [
          {
            id: `reality-${Date.now()}`,
            type: 'execution_completed' as const,
            title: result.message || exec.label,
            description: result.explanation || result.error || '',
            timestamp: timestamp(),
            importance: result.success ? ('normal' as const) : ('high' as const),
          },
          ...s.realityEvents,
        ].slice(0, 50),
      }));

      // Refresh reality after execution
      get().fetchReality();
    } catch (e) {
      clearInterval(progressInterval);
      set((s) => ({
        activeExecutions: s.activeExecutions.filter((e) => e.id !== executionId),
        executionHistory: [
          ...s.executionHistory,
          {
            ...exec,
            status: 'failed',
            error: e instanceof Error ? e.message : 'Action failed',
            completed_at: timestamp(),
          },
        ],
      }));
    }
  },

  // ── UI actions ──
  expandObject: (id) => set({ expandedObjectId: id }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setCommandOpen: (open) => set({ commandOpen: open }),
  setFounderName: (name) => set({ founderName: name }),
  dismissRecommendation: (id) => {
    // Record the dismissal for adaptation
    const rec = get().recommendations.find((r) => r.id === id);
    if (rec) {
      get().observeAction({
        actionType: rec.action_type,
        actionLabel: rec.action_label,
        objectType: rec.source_observation?.split(':')[0]?.trim() || undefined,
        outcome: 'dismissed',
      });
    }
    set((s) => ({ recommendations: s.recommendations.filter((r) => r.id !== id) }));
  },
  dismissObservation: (id) =>
    set((s) => ({ observations: s.observations.filter((o) => o.id !== id) })),

  // ── Awareness Actions ──
  acknowledgeSignal: (id) =>
    set((s) => ({
      awarenessSignals: s.awarenessSignals.map((sig) =>
        sig.signal_id === id ? { ...sig, status: 'acknowledged' as const } : sig
      ),
      awarenessCount: Math.max(0, s.awarenessCount - 1),
      awarenessCalm: s.awarenessCount <= 1,
    })),
  dismissSignal: (id) =>
    set((s) => ({
      awarenessSignals: s.awarenessSignals.filter((sig) => sig.signal_id !== id),
      awarenessCount: Math.max(0, s.awarenessCount - 1),
      awarenessCalm: s.awarenessCount <= 1,
    })),
  snoozeSignal: (id) =>
    set((s) => ({
      awarenessSignals: s.awarenessSignals.filter((sig) => sig.signal_id !== id),
      awarenessCount: Math.max(0, s.awarenessCount - 1),
      awarenessCalm: s.awarenessCount <= 1,
    })),
  addAwarenessSignal: (signal) =>
    set((s) => {
      // Dedup: avoid adding the same signal twice
      if (s.awarenessSignals.some((sig) => sig.signal_id === signal.signal_id)) return s;
      const updated = [signal, ...s.awarenessSignals].slice(0, 20);
      return {
        awarenessSignals: updated,
        awarenessCount: updated.filter((sig) => sig.status === 'active').length,
        awarenessCalm: false,
      };
    }),

  // ── Reality via SSE Runtime ──
  startPolling: () => {
    // Initial fetch (the SSE stream will keep it updated)
    get().fetchReality();

    // Subscribe to reality:snapshot events from the SSE Runtime
    const unsubSnapshot = bus.on('reality:snapshot', (e) => {
      if (e.type !== 'reality:snapshot') return;
      const data = e.data as Record<string, any>;

      // Update reality events
      const events: RealityEvent[] = (data.events || []).map((a: any, i: number) => ({
        id: a.event_id || `evt-${i}`,
        type: a.type || 'system_event',
        title: a.title,
        description: a.description || a.title,
        object_type: a.object_type,
        object_id: a.object_id,
        object_name: a.object_name,
        timestamp: a.timestamp,
        actor: a.actor,
        importance: a.importance || 'normal',
      }));

      set({
        realityEvents: events,
        realityLoading: false,
        realityError: null,
      });

      // Extract observations from attention queue
      const attention = data.attention_queue || data.attention_items || [];
      if (attention.length > 0) {
        const observations = attention.map((a: any, i: number) => ({
          id: a.item_id || `obs-${i}-${Date.now()}`,
          title: a.label,
          description: a.description || '',
          source: a.source_type || 'reality',
          timestamp: new Date().toISOString(),
          priority: a.priority_score || 0,
        }));
        set({ observations });
      }
    });

    // Subscribe to individual canonical events from the SSE stream
    const unsubEvent = bus.on('reality:event', (e) => {
      if (e.type !== 'reality:event') return;
      const data = e.data as Record<string, any>;
      if (!data || !data.event_type) return;

      // Map canonical event to RealityEvent
      const evt: RealityEvent = {
        id: data.event_id || `re-${Date.now()}`,
        type: (data.event_type || 'system_event') as any,
        title: data.event_type?.replace(/\./g, ' ') || 'System Event',
        description: data.payload?.message || data.event_type || '',
        object_type: data.object?.type || data.object_type,
        object_id: data.object?.id || data.object_id,
        object_name: data.object?.name || data.object_name,
        timestamp: data.timestamp || new Date().toISOString(),
        actor: data.actor?.name || data.actor || '',
        importance: data.confidence != null && data.confidence < 0.5 ? 'high' as const
          : 'normal' as const,
      };

      // Update execution state from event type
      const evtType = data.event_type || '';
      if (evtType.includes('execution_') || evtType.includes('processing')) {
        // Update active executions
        const existing = get().activeExecutions;
        const isCompletion = evtType.includes('completed') || evtType.includes('success');
        const isFailure = evtType.includes('failed') || evtType.includes('error');
        const isStart = evtType.includes('started') || evtType.includes('begun') || evtType.includes('processing');

        if (isStart) {
          const exec = {
            id: data.event_id || `exec-${Date.now()}`,
            label: evt.title,
            description: evt.description,
            status: 'in_progress' as const,
            progress: 0.3,
            started_at: data.timestamp || new Date().toISOString(),
          };
          set({ activeExecutions: [...existing, exec] });
        } else if (isCompletion || isFailure) {
          const outcome = existing.find(e => e.label === evt.title);
          if (outcome) {
            const completed = {
              ...outcome,
              status: isCompletion ? 'completed' as const : 'failed' as const,
              progress: isCompletion ? 1.0 : 0.0,
              completed_at: new Date().toISOString(),
              outcome: data.payload?.message || (isCompletion ? 'Completed' : 'Failed'),
              error: isFailure ? (data.payload?.error || 'Execution failed') : undefined,
            };
            set({
              activeExecutions: existing.filter(e => e.id !== outcome.id),
              executionHistory: [completed, ...get().executionHistory].slice(0, 50),
            });
          }
        }
      }

      // ── Awareness: detect awareness:* events ──
      if (evtType.startsWith('awareness:')) {
        const payload = data.payload || {};
        const signal: AwarenessSignal = {
          signal_id: payload.signal_id || data.event_id,
          signal_type: (payload.signal_type || 'attention') as any,
          title: payload.title || evt.title,
          description: payload.description || evt.description,
          reason: payload.reason || '',
          priority: (payload.priority || 'normal') as any,
          relevance_score: payload.relevance || 0.5,
          source_event_id: payload.source_event_id || '',
          suggested_action: payload.suggested_action || '',
          evidence: payload.evidence || [],
          affected_object_id: data.object_id,
          affected_object_type: data.object_type,
          status: (payload.status || 'active') as any,
          created_at: payload.created_at || data.timestamp || new Date().toISOString(),
        };
        get().addAwarenessSignal(signal);
      }

      // Prepend to reality events
      set((s) => ({
        realityEvents: [evt, ...s.realityEvents].slice(0, 50),
        realityLoading: false,
        realityError: null,
      }));
    });

    return () => {
      unsubSnapshot();
      unsubEvent();
    };
  },

  // ── LX-04 Adaptation Actions ──

  observeAction: (record) => {
    const history = get().interactionHistory;
    const prefs = { ...get().founderPreferences };

    // Record the interaction
    const interaction: InteractionRecord = {
      ...record,
      timestamp: timestamp(),
    };
    const updatedHistory = [...history, interaction].slice(-100); // Keep last 100

    // Inference: count how many times each action label appears per object type
    const actionCounts: Record<string, number> = {};
    for (const h of updatedHistory) {
      if (h.outcome === 'executed') {
        const key = `${h.objectType || 'general'}:${h.actionLabel}`;
        actionCounts[key] = (actionCounts[key] || 0) + 1;
      }
    }

    // Inference: identify the founder's most-used action per object type
    const preferredByType: Record<string, string[]> = {};
    for (const h of updatedHistory) {
      if (h.outcome === 'executed' && h.objectType) {
        if (!preferredByType[h.objectType]) preferredByType[h.objectType] = [];
        if (!preferredByType[h.objectType].includes(h.actionLabel)) {
          preferredByType[h.objectType].push(h.actionLabel);
        }
      }
    }

    // Inference: identify engaged object types
    const typeCounts: Record<string, number> = {};
    for (const h of updatedHistory) {
      if (h.outcome === 'executed' && h.objectType) {
        typeCounts[h.objectType] = (typeCounts[h.objectType] || 0) + 1;
      }
    }
    const activeTypes = Object.entries(typeCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([type]) => type);

    // Inference: track how many prepared actions were approved vs stopped
    const executedCount = updatedHistory.filter((h) => h.outcome === 'executed').length;
    const dismissedCount = updatedHistory.filter((h) => h.outcome === 'dismissed').length;
    const totalInteractions = updatedHistory.length;

    // Update confidence: slowly grows as founder interacts
    const confidence = Math.min(0.95, totalInteractions / 50);
    const approvesPrepared = executedCount > dismissedCount * 2 && totalInteractions > 5;

    set({
      interactionHistory: updatedHistory,
      founderPreferences: {
        preferredActions: preferredByType,
        activeObjectTypes: activeTypes,
        actedOnUrgency: prefs.actedOnUrgency,
        prefersQuickAction: prefs.prefersQuickAction,
        confidence,
        totalInteractions,
        approvesPreparedActions: approvesPrepared,
      },
    });

    // Generate reflection after every 10th interaction
    if (totalInteractions > 0 && totalInteractions % 10 === 0) {
      const topType = activeTypes[0];
      const topAction = preferredByType[topType]?.[0];
      const reflection: ReflectionMessage = {
        id: `reflect_${totalInteractions}`,
        message: topType && topAction
          ? `I've noticed you tend to ${topAction.toLowerCase()} when working with ${topType.replace(/_/g, ' ')} records. I'll keep this in mind for future recommendations.`
          : `I've observed ${totalInteractions} interactions so far. Your patterns are helping me make better recommendations.`,
        type: 'learning',
        timestamp: timestamp(),
        seen: false,
      };
      set((s) => ({
        reflectionMessages: [...s.reflectionMessages, reflection].slice(-5),
      }));
    }
  },

  dismissReflection: (id) => {
    set((s) => ({
      reflectionMessages: s.reflectionMessages.map((r) =>
        r.id === id ? { ...r, seen: true } : r
      ),
    }));
  },

  getAdaptationContext: () => {
    const prefs = get().founderPreferences;
    if (prefs.totalInteractions < 3) return null;

    const topType = prefs.activeObjectTypes[0];
    const topAction = prefs.preferredActions[topType]?.[0];

    if (prefs.totalInteractions < 10) {
      return `I'm still learning how you work. Based on ${prefs.totalInteractions} interaction${prefs.totalInteractions !== 1 ? 's' : ''}, I'm beginning to understand your preferences.`;
    }

    if (topType && topAction) {
      return `Based on our previous work together, I've noticed you prefer to ${topAction.toLowerCase()} when handling ${topType.replace(/_/g, ' ')} records. I've adjusted my recommendations accordingly.`;
    }

    return `After ${prefs.totalInteractions} interactions, I'm getting better at understanding your working style.`;
  },

  /** LX-05: Reset founder memory — explainable, reviewable, resettable */
  resetFounderMemory: () => {
    set({
      interactionHistory: [],
      founderPreferences: {
        preferredActions: {},
        activeObjectTypes: [],
        actedOnUrgency: [],
        prefersQuickAction: true,
        confidence: 0.0,
        totalInteractions: 0,
        approvesPreparedActions: false,
      },
      reflectionMessages: [],
    });
  },
}));