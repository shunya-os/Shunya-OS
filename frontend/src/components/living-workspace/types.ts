/**
 * SHUNYA LX-01 — Living Workspace Types
 *
 * Core type definitions for the canonical SHUNYA experience.
 * Every type aligns with the four categories: Reality, Understanding, Recommendation, Execution.
 */

// ── Reality ── What changed, what exists, what is happening

export type RealityEventType =
  | 'object_created'
  | 'object_updated'
  | 'object_evolved'
  | 'ai_observation'
  | 'system_event'
  | 'execution_completed'
  | 'milestone_reached';

export interface RealityEvent {
  id: string;
  type: RealityEventType;
  title: string;
  description: string;
  object_type?: string;
  object_id?: string;
  object_name?: string;
  timestamp: string;
  actor?: string;
  importance: 'critical' | 'high' | 'normal' | 'low';
}

// ── Understanding ── What SHUNYA observes, reasons, and is confident about

export interface AIObservation {
  id: string;
  title: string;
  description: string;
  type: 'reminder' | 'opportunity' | 'alert' | 'suggestion' | 'insight';
  confidence: number; // 0.0 - 1.0
  evidence: string;
  source: string;
  timestamp: string;
}

export interface AIReasoning {
  id: string;
  query: string;
  steps: ReasoningStep[];
  conclusion: string;
  confidence: number;
  duration_ms?: number;
  timestamp: string;
}

export interface ReasoningStep {
  label: string;
  detail: string;
  status: 'complete' | 'in_progress' | 'pending' | 'error';
  confidence?: number;
}

// ── Recommendation ── What SHUNYA suggests doing

export interface AIRecommendation {
  id: string;
  title: string;
  description: string;
  action_label: string;
  action_type: string;
  action_payload: Record<string, unknown>;
  confidence: number;
  reasoning_id?: string;
  urgency: 'now' | 'today' | 'this_week' | 'when_possible';
  source_observation?: string;
}

// ── Execution ── What SHUNYA is currently doing

export interface Execution {
  id: string;
  label: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'awaiting_approval' | 'error';
  progress: number;
  started_at?: string;
  completed_at?: string;
  outcome?: string;
  error?: string;
  subtasks?: Execution[];
  currentStage?: string;
  stages?: string[];
  result?: string;
}

// ── Living Object ── A business object as a continuously evolving story

export interface LivingObject {
  id: string;
  object_id: string;
  object_type: string;
  name: string;
  current_stage: string;
  story: ObjectLifecycleEvent[];
  stage_history: StageMilestone[];
  stage_pipeline: string[];
  summary: string;
  time_narrative: string;
  recommendation: ObjectRecommendation;
  next_action: NextAction | null;
  alternative_actions: NextAction[];
  relationships: ObjectRelationship[];
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  status: string;
}

export interface StageMilestone {
  stage: string;
  timestamp: string;
  label: string;
  actor: string;
}

export interface ObjectRecommendation {
  label: string;
  type: string;
  confidence: number;
  reasoning: string;
}

export interface ObjectLifecycleEvent {
  stage: string;
  label: string;
  timestamp: string;
  description: string;
  actor?: string;
  outcome?: string;
}

export interface NextAction {
  label: string;
  description: string;
  action_type: string;
  action_payload: Record<string, unknown>;
  confidence: number;
  is_primary: boolean;
}

export interface ObjectRelationship {
  object_type?: string;
  object_id: string;
  object_name: string;
  relationship: string;
  explanation: string;
  direction: 'inbound' | 'outbound' | 'bidirectional';
  confidence: number;
}

// ── Workspace State ──

// ── Awareness ── What matters now

export interface AwarenessSignal {
  signal_id: string;
  signal_type: 'change' | 'attention' | 'risk' | 'commitment' | 'opportunity' | 'information' | 'pattern' | 'conflict' | 'overdue' | 'blocked' | 'external';
  title: string;
  description: string;
  reason: string;
  priority: 'critical' | 'high' | 'normal' | 'low';
  relevance_score: number;
  source_event_id: string;
  suggested_action: string;
  evidence: Array<{ source: string; event_id: string; timestamp: string; detail: string }>;
  affected_object_id?: string;
  affected_object_type?: string;
  status: 'active' | 'acknowledged' | 'dismissed' | 'snoozed' | 'expired' | 'resolved';
  created_at: string;
}

export interface LivingWorkspaceState {
  // Reality
  realityEvents: RealityEvent[];
  realityLoading: boolean;
  realityError: string | null;
  realityPollTime: string;

  // Awareness — what matters now
  awarenessSignals: AwarenessSignal[];
  awarenessCount: number;
  awarenessCalm: boolean;

  // Understanding
  // Understanding
  observations: AIObservation[];
  activeReasoning: AIReasoning | null;
  reasoningHistory: AIReasoning[];

  // Recommendation
  recommendations: AIRecommendation[];
  activeRecommendation: AIRecommendation | null;

  // Execution
  activeExecutions: Execution[];
  executionHistory: Execution[];

  // Living Objects
  livingObjects: LivingObject[];
  expandedObjectId: string | null;
  objectsLoading: boolean;

  // UI State
  founderName: string;
  lastUpdated: string;
  sidebarCollapsed: boolean;
  commandOpen: boolean;

  // LX-04 Adaptation
  interactionHistory: Array<{
    timestamp: string;
    actionType: string;
    actionLabel: string;
    objectType?: string;
    outcome?: 'executed' | 'dismissed' | 'completed' | 'failed';
  }>;
  founderPreferences: {
    preferredActions: Record<string, string[]>;
    activeObjectTypes: string[];
    actedOnUrgency: string[];
    prefersQuickAction: boolean;
    confidence: number;
    totalInteractions: number;
    approvesPreparedActions: boolean;
  };
  reflectionMessages: Array<{
    id: string;
    message: string;
    type: 'learning' | 'observation' | 'adaptation';
    timestamp: string;
    seen: boolean;
  }>;

  // LX-05 Memory Governance
  resetFounderMemory: () => void;
}

// ── API Response shapes ──

export interface ExecutiveHomeResponse {
  success: boolean;
  data?: {
    health: { status: string; bootstrapped: boolean; runtime_count: number };
    priorities: Array<{
      id: string; title: string; reason: string;
      affected_objects: number; urgency: string; recommended_action: string;
    }>;
    recent_activity: RealityEvent[];
    active_commitments: Array<{
      id: string; title: string; type: string;
      status: string; owner: string; due_date: string | null; progress: number;
    }>;
    object_summary: { total: number; by_type: Record<string, number>; at_risk: number };
    generated_at: string;
  };
  error?: string;
}

export interface AIInsightResponse {
  success: boolean;
  data?: AIObservation[];
  error?: string;
}