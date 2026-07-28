/**
 * Commitment Runtime — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Model business promises (commitments) as first-class runtime entities
 * - Manage the commitment lifecycle: draft → → proposed → accepted → planned → active → waiting/blocked/at-risk → completed/cancelled → archived
 * - Derive progress from evidence and state, not manual percentages
 * - Compute explainable confidence from evidence, dependencies, activity, and AI observations
 * - Reference Object Graph nodes for relationship data (never duplicate)
 * - Emit timeline events on every state transition
 * - Provide execution state to the Intelligence Runtime for analysis (not ownership)
 *
 * ── Events Published ──────────────────────────────────────────
 * CommitmentCreated, CommitmentActivated, CommitmentBlocked,
 * CommitmentResumed, CommitmentCompleted, CommitmentCancelled,
 * CommitmentEvidenceAdded, CommitmentConfidenceChanged, CommitmentRiskDetected
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * ObjectUpdated  → re-evaluate evidence progress
 * ObjectLoaded   → re-evaluate dependency health
 * GraphHydrated  → re-evaluate relationship-connected evidence
 *
 * ── Owned State ───────────────────────────────────────────────
 * Commitment registry (Map<id, CommitmentEntity>)
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * ObjectGraphRuntime  — relationship nodes and edges
 * TimelineRuntime     — event stream (reads/writes via events)
 * IntelligenceRuntime — AI analysis (consumes commitment state)
 *
 * ── Persistence Policy ────────────────────────────────────────
 * Session (active commitments survive tab refresh)
 * Snapshot on every state transition
 *
 * ── Synchronisation Policy ────────────────────────────────────
 * Optimistic local updates, confirmed/synced by server response
 *
 * ── Snapshot Strategy ─────────────────────────────────────────
 * Snapshot on every CommitmentStateChanged event for full replay
 *
 * ── Recovery Behaviour ────────────────────────────────────────
 * Rehydrate from State Fabric on startup
 * Recalculate confidence and progress from cached evidence
 *
 * ── Health Probe ──────────────────────────────────────────────
 * Reports active count, pending transitions, last activity timestamp
 */

import { bus } from '../event-bus';
import { stateFabric } from '../state-fabric';

// ── Types ──────────────────────────────────────────────────────

export type CommitmentStatus =
  | 'draft' | 'proposed' | 'accepted' | 'planned' | 'active'
  | 'waiting' | 'blocked' | 'at_risk'
  | 'completed' | 'cancelled' | 'archived';

export interface CommitmentEntity {
  id: string;
  title: string;
  description: string;
  objective: string;
  status: CommitmentStatus;
  progress: number;          // 0-1, derived
  confidence: number;        // 0-1, explainable
  priority: 'critical' | 'high' | 'medium' | 'low';
  owner: string;
  participants: string[];
  relatedObjectIds: string[];
  dependencyCommitmentIds: string[];
  evidenceIds: string[];
  risks: { description: string; severity: 'low' | 'medium' | 'high'; detected: number }[];
  outcome: string;
  deadline: number | null;
  createdAt: number;
  updatedAt: number;
}

export const VALID_TRANSITIONS: Record<CommitmentStatus, CommitmentStatus[]> = {
  draft: ['proposed', 'cancelled'],
  proposed: ['accepted', 'draft', 'cancelled'],
  accepted: ['planned', 'draft', 'cancelled'],
  planned: ['active', 'cancelled'],
  active: ['waiting', 'blocked', 'at_risk', 'completed', 'cancelled'],
  waiting: ['active', 'blocked', 'at_risk', 'cancelled'],
  blocked: ['active', 'waiting', 'at_risk', 'cancelled'],
  at_risk: ['active', 'blocked', 'completed', 'cancelled'],
  completed: ['archived'],
  cancelled: ['archived'],
  archived: [],
};

// ── Helpers ────────────────────────────────────────────────────

export function canTransition(from: CommitmentStatus, to: CommitmentStatus): boolean {
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}

function newId(): string { return `cmt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`; }

// ── Progress Strategies ───────────────────────────────────────

type ProgressStrategy = 'milestone' | 'weighted_evidence' | 'deterministic';

const PROGRESS_STRATEGIES: Record<string, ProgressStrategy> = {
  default: 'weighted_evidence',
  project: 'milestone',
  payment: 'deterministic',
};

function calcProgress(commitment: CommitmentEntity): number {
  const strategy = PROGRESS_STRATEGIES[commitment.priority] ?? PROGRESS_STRATEGIES.default;
  if (strategy === 'deterministic') {
    return commitment.status === 'completed' ? 1 : commitment.status === 'active' ? 0.5 : 0;
  }
  if (strategy === 'weighted_evidence') {
    // Each piece of evidence = 10% progress, cap at 90% (last 10% is verification)
    return Math.min(commitment.evidenceIds.length * 0.1, 0.9);
  }
  // milestone: 0 until active, 50% after first evidence, 90% in final stages
  if (commitment.status === 'completed') return 1;
  if (commitment.status === 'active' && commitment.evidenceIds.length > 0) return 0.5;
  if (commitment.status === 'active') return 0.25;
  return 0;
}

// ── Confidence Engine ─────────────────────────────────────────

function calcConfidence(commitment: CommitmentEntity): number {
  let score = 0;
  const factors: string[] = [];

  // Evidence completeness (up to 0.4)
  const evidenceFactor = Math.min(commitment.evidenceIds.length * 0.08, 0.4);
  score += evidenceFactor;
  if (commitment.evidenceIds.length > 0) factors.push(`evidence: ${evidenceFactor.toFixed(2)}`);

  // Status-based (up to 0.25)
  const statusConfidence: Record<CommitmentStatus, number> = {
    draft: 0.1, proposed: 0.2, accepted: 0.35, planned: 0.5,
    active: 0.65, waiting: 0.4, blocked: 0.2, at_risk: 0.35,
    completed: 1, cancelled: 0, archived: 1,
  };
  score += statusConfidence[commitment.status] * 0.25;
  factors.push(`status: ${(statusConfidence[commitment.status] * 0.25).toFixed(2)}`);

  // Overdue penalty (up to -0.15)
  if (commitment.deadline && Date.now() > commitment.deadline) {
    const overdueDays = (Date.now() - commitment.deadline) / (1000 * 60 * 60 * 24);
    const penalty = Math.min(overdueDays * 0.02, 0.15);
    score -= penalty;
    factors.push(`overdue penalty: -${penalty.toFixed(2)}`);
  }

  // Risks penalty (up to -0.2)
  const riskPenalty = commitment.risks.reduce((sum, r) => {
    return sum + (r.severity === 'high' ? 0.1 : r.severity === 'medium' ? 0.05 : 0.02);
  }, 0);
  const cappedPenalty = Math.min(riskPenalty, 0.2);
  score -= cappedPenalty;
  if (cappedPenalty > 0) factors.push(`risk penalty: -${cappedPenalty.toFixed(2)}`);

  return Math.max(0, Math.min(1, score));
}

// ── Registry ──────────────────────────────────────────────────

const commitments = new Map<string, CommitmentEntity>();
let lastActivity = Date.now();

function snap(commitment: CommitmentEntity): void {
  stateFabric.write('commitment-runtime', {
    [commitment.id]: {
      status: commitment.status,
      progress: commitment.progress,
      confidence: commitment.confidence,
    },
  }, `commitment_${commitment.status}`);
}

// ── Runtime ───────────────────────────────────────────────────

export const CommitmentRuntime = {
  // ── CRUD ──────────────────────────────────────────────────────

  create(opts: {
    title: string; description?: string; objective?: string;
    priority?: CommitmentEntity['priority']; owner?: string;
    deadline?: number; outcome?: string;
  }): CommitmentEntity {
    const entity: CommitmentEntity = {
      id: newId(),
      title: opts.title,
      description: opts.description ?? '',
      objective: opts.objective ?? opts.title,
      status: 'draft',
      progress: 0,
      confidence: 0,
      priority: opts.priority ?? 'medium',
      owner: opts.owner ?? '',
      participants: [],
      relatedObjectIds: [],
      dependencyCommitmentIds: [],
      evidenceIds: [],
      risks: [],
      outcome: opts.outcome ?? '',
      deadline: opts.deadline ?? null,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    commitments.set(entity.id, entity);
    lastActivity = Date.now();
    snap(entity);
    bus.emit({ type: 'CommitmentCreated' as any, commitmentId: entity.id } as any);
    return entity;
  },

  get(id: string): CommitmentEntity | undefined {
    return commitments.get(id);
  },

  getAll(): CommitmentEntity[] {
    return Array.from(commitments.values());
  },

  getByStatus(status: CommitmentStatus): CommitmentEntity[] {
    return this.getAll().filter(c => c.status === status);
  },

  // ── Transitions ──────────────────────────────────────────────

  transition(id: string, to: CommitmentStatus): boolean {
    const c = commitments.get(id);
    if (!c || !canTransition(c.status, to)) return false;

    c.status = to;
    c.updatedAt = Date.now();
    c.progress = calcProgress(c);
    c.confidence = calcConfidence(c);
    lastActivity = Date.now();
    snap(c);

    const eventType = ({
      active: 'CommitmentActivated', blocked: 'CommitmentBlocked',
      completed: 'CommitmentCompleted', cancelled: 'CommitmentCancelled',
    } as Record<string, string>)[to];

    if (eventType) {
      bus.emit({ type: eventType as any, commitmentId: id } as any);
    }
    return true;
  },

  // ── Evidence ─────────────────────────────────────────────────

  addEvidence(commitmentId: string, evidenceId: string): void {
    const c = commitments.get(commitmentId);
    if (!c || c.evidenceIds.includes(evidenceId)) return;
    c.evidenceIds.push(evidenceId);
    c.updatedAt = Date.now();
    c.progress = calcProgress(c);
    c.confidence = calcConfidence(c);
    snap(c);
    bus.emit({ type: 'CommitmentEvidenceAdded' as any, commitmentId } as any);
  },

  removeEvidence(commitmentId: string, evidenceId: string): void {
    const c = commitments.get(commitmentId);
    if (!c) return;
    c.evidenceIds = c.evidenceIds.filter(e => e !== evidenceId);
    c.updatedAt = Date.now();
    c.progress = calcProgress(c);
    c.confidence = calcConfidence(c);
    snap(c);
  },

  // ── Risks ────────────────────────────────────────────────────

  addRisk(commitmentId: string, description: string, severity: 'low' | 'medium' | 'high'): void {
    const c = commitments.get(commitmentId);
    if (!c) return;
    c.risks.push({ description, severity, detected: Date.now() });
    c.confidence = calcConfidence(c);
    c.updatedAt = Date.now();
    snap(c);
    bus.emit({ type: 'CommitmentRiskDetected' as any, commitmentId } as any);
  },

  // ── Progress & Confidence ────────────────────────────────────

  recalculate(id: string): void {
    const c = commitments.get(id);
    if (!c) return;
    c.progress = calcProgress(c);
    c.confidence = calcConfidence(c);
    c.updatedAt = Date.now();
    snap(c);
    bus.emit({ type: 'CommitmentConfidenceChanged' as any, commitmentId: id } as any);
  },

  /** Get a human-readable explanation of the confidence score. */
  explainConfidence(id: string): { score: number; factors: string[] } {
    const c = commitments.get(id);
    if (!c) return { score: 0, factors: ['Commitment not found'] };
    const score = calcConfidence(c);
    const factors: string[] = [];
    factors.push(`progress: ${(c.progress * 100).toFixed(0)}%`);
    factors.push(`evidence: ${c.evidenceIds.length} item(s)`);
    factors.push(`risks: ${c.risks.length} active`);
    if (c.deadline) {
      const remaining = c.deadline - Date.now();
      factors.push(remaining > 0 ? `deadline: ${Math.ceil(remaining / (1000 * 60 * 60 * 24))}d remaining` : 'overdue');
    }
    factors.push(`status: ${c.status}`);
    return { score, factors };
  },

  // ── Dependencies ─────────────────────────────────────────────

  addDependency(commitmentId: string, dependencyId: string): boolean {
    const c = commitments.get(commitmentId);
    const dep = commitments.get(dependencyId);
    if (!c || !dep) return false;
    if (c.dependencyCommitmentIds.includes(dependencyId)) return true;

    // Cycle detection
    const visited = new Set<string>();
    function hasCycle(id: string): boolean {
      if (id === commitmentId) return true;
      if (visited.has(id)) return false;
      visited.add(id);
      const depCommitment = commitments.get(id);
      return depCommitment?.dependencyCommitmentIds.some(d => hasCycle(d)) ?? false;
    }
    if (hasCycle(dependencyId)) return false;

    c.dependencyCommitmentIds.push(dependencyId);
    c.updatedAt = Date.now();
    return true;
  },

  // ── Lifecycle ────────────────────────────────────────────────

  clear(): void {
    commitments.clear();
    lastActivity = Date.now();
  },

  stats(): { active: number; total: number; byStatus: Record<string, number>; lastActivity: number } {
    const byStatus: Record<string, number> = {};
    for (const c of commitments.values()) {
      byStatus[c.status] = (byStatus[c.status] ?? 0) + 1;
    }
    return { active: this.getByStatus('active').length, total: commitments.size, byStatus, lastActivity };
  },
};