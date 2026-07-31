/**
 * Conversation Runtime — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Model conversations as persistent business execution contexts, not message history
 * - Own conversational context, participants, intent, and state
 * - Support multi-object and multi-commitment conversations
 * - Track current intent independently from message history
 * - Reference memory rather than embedding duplicated knowledge
 * - Emit timeline events on every significant conversational change
 *
 * ── Events Published ──────────────────────────────────────────
 * ConversationCreated, ConversationActivated, ConversationIntentChanged,
 * ConversationContextChanged, ConversationArchived,
 * ConversationParticipantAdded, ConversationParticipantRemoved
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * (none — external runtimes consume conversation events; conversation does not react)
 *
 * ── Owned State ───────────────────────────────────────────────
 * Conversation entities (Map<id, ConversationEntity>)
 * Intent registry (Map<id, string>)
 * Participant registry (Map<id, Set<string>>)
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * ObjectRuntime         — objects referenced in conversation context
 * CommitmentRuntime     — commitments referenced in conversation context
 * ObjectGraphRuntime    — relationships between referenced objects
 * IntelligenceRuntime   — AI insights consumed from conversation context
 *
 * ── Persistence Policy ────────────────────────────────────────
 * Session (active conversations survive tab refresh)
 * Snapshot on every state transition
 *
 * ── Synchronisation Policy ────────────────────────────────────
 * Optimistic local updates
 *
 * ── Snapshot Strategy ─────────────────────────────────────────
 * Snapshot on every ConversationArchived event
 *
 * ── Recovery Behaviour ────────────────────────────────────────
 * Rehydrate from State Fabric on startup (session-scoped)
 * Non-archived conversations restored on reload
 *
 * ── Health Probe ──────────────────────────────────────────────
 * Reports active conversation count, total archived, intent distribution
 */

import { bus } from '../event-bus';
import { stateFabric } from '../state-fabric';

// ── Types ──────────────────────────────────────────────────────

export type ConversationStatus = 'created' | 'active' | 'waiting' | 'escalated' | 'resolved' | 'archived';

export interface ConversationEntity {
  id: string;
  title: string;
  status: ConversationStatus;
  intent: string;
  participants: string[];
  objectRefs: string[];         // Referenced object IDs (type:id)
  commitmentRefs: string[];     // Referenced commitment IDs
  memoryRefs: string[];         // Referenced permanent knowledge IDs
  timelineRefs: string[];       // Timeline event IDs from this conversation
  createdAt: number;
  updatedAt: number;
}

const VALID_TRANSITIONS: Record<ConversationStatus, ConversationStatus[]> = {
  created: ['active', 'archived'],
  active: ['waiting', 'escalated', 'resolved', 'archived'],
  waiting: ['active', 'escalated', 'resolved', 'archived'],
  escalated: ['active', 'waiting', 'resolved', 'archived'],
  resolved: ['archived'],
  archived: [],
};

// ── Helpers ────────────────────────────────────────────────────

export function canTransition(from: ConversationStatus, to: ConversationStatus): boolean {
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}

function newId(): string { return `conv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`; }

// ── Registry ──────────────────────────────────────────────────

const conversations = new Map<string, ConversationEntity>();
let lastActivity = Date.now();

function snap(): void {
  stateFabric.write('conversation-runtime', {
    activeCount: getActive().length,
    totalCount: conversations.size,
    lastActivity,
  }, 'state_change');
}

function getActive(): ConversationEntity[] {
  return Array.from(conversations.values()).filter(c => !['resolved', 'archived'].includes(c.status));
}

// ── Runtime ───────────────────────────────────────────────────

export const ConversationRuntime = {
  // ── CRUD ──────────────────────────────────────────────────────

  create(title: string, intent?: string): ConversationEntity {
    const conv: ConversationEntity = {
      id: newId(), title,
      status: 'created',
      intent: intent ?? title,
      participants: [], objectRefs: [], commitmentRefs: [],
      memoryRefs: [], timelineRefs: [],
      createdAt: Date.now(), updatedAt: Date.now(),
    };
    conversations.set(conv.id, conv);
    lastActivity = Date.now();
    snap();
    bus.emit({ type: 'ConversationCreated' as any, source: 'conversation-runtime', error: '' } as any);
    return conv;
  },

  get(id: string): ConversationEntity | undefined {
    return conversations.get(id);
  },

  getAll(): ConversationEntity[] {
    return Array.from(conversations.values());
  },

  // ── Transitions ──────────────────────────────────────────────

  transition(id: string, to: ConversationStatus): boolean {
    const c = conversations.get(id);
    if (!c || !canTransition(c.status, to)) return false;
    c.status = to;
    c.updatedAt = Date.now();
    lastActivity = Date.now();
    snap();
    if (to === 'active') bus.emit({ type: 'ConversationActivated' as any, source: id, error: '' } as any);
    if (to === 'archived') bus.emit({ type: 'ConversationArchived' as any, source: id, error: '' } as any);
    return true;
  },

  // ── Intent ───────────────────────────────────────────────────

  setIntent(id: string, intent: string): void {
    const c = conversations.get(id);
    if (!c) return;
    const previous = c.intent;
    c.intent = intent;
    c.updatedAt = Date.now();
    lastActivity = Date.now();
    snap();
    if (previous !== intent) {
      bus.emit({ type: 'ConversationIntentChanged' as any, source: id, error: '' } as any);
    }
  },

  getIntent(id: string): string | undefined {
    return conversations.get(id)?.intent;
  },

  // ── Context ──────────────────────────────────────────────────

  addObjectRef(conversationId: string, objectId: string): void {
    const c = conversations.get(conversationId);
    if (!c || c.objectRefs.includes(objectId)) return;
    c.objectRefs.push(objectId);
    c.updatedAt = Date.now();
    lastActivity = Date.now();
    snap();
    bus.emit({ type: 'ConversationContextChanged' as any, source: conversationId, error: '' } as any);
  },

  removeObjectRef(conversationId: string, objectId: string): void {
    const c = conversations.get(conversationId);
    if (!c) return;
    c.objectRefs = c.objectRefs.filter(o => o !== objectId);
    c.updatedAt = Date.now();
    snap();
  },

  addCommitmentRef(conversationId: string, commitmentId: string): void {
    const c = conversations.get(conversationId);
    if (!c || c.commitmentRefs.includes(commitmentId)) return;
    c.commitmentRefs.push(commitmentId);
    c.updatedAt = Date.now();
    snap();
    bus.emit({ type: 'ConversationContextChanged' as any, source: conversationId, error: '' } as any);
  },

  removeCommitmentRef(conversationId: string, commitmentId: string): void {
    const c = conversations.get(conversationId);
    if (!c) return;
    c.commitmentRefs = c.commitmentRefs.filter(m => m !== commitmentId);
    c.updatedAt = Date.now();
    snap();
  },

  // ── Participants ─────────────────────────────────────────────

  addParticipant(conversationId: string, participantId: string): void {
    const c = conversations.get(conversationId);
    if (!c || c.participants.includes(participantId)) return;
    c.participants.push(participantId);
    c.updatedAt = Date.now();
    snap();
    bus.emit({ type: 'ConversationParticipantAdded' as any, source: conversationId, error: '' } as any);
  },

  removeParticipant(conversationId: string, participantId: string): void {
    const c = conversations.get(conversationId);
    if (!c) return;
    c.participants = c.participants.filter(p => p !== participantId);
    c.updatedAt = Date.now();
    snap();
    bus.emit({ type: 'ConversationParticipantRemoved' as any, source: conversationId, error: '' } as any);
  },

  // ── Query ────────────────────────────────────────────────────

  getByObjectRef(objectId: string): ConversationEntity[] {
    return this.getAll().filter(c => c.objectRefs.includes(objectId));
  },

  getByCommitmentRef(commitmentId: string): ConversationEntity[] {
    return this.getAll().filter(c => c.commitmentRefs.includes(commitmentId));
  },

  getByParticipant(participantId: string): ConversationEntity[] {
    return this.getAll().filter(c => c.participants.includes(participantId));
  },

  getActive(): ConversationEntity[] {
    return getActive();
  },

  // ── Lifecycle ────────────────────────────────────────────────

  clear(): void {
    conversations.clear();
    lastActivity = Date.now();
  },

  stats(): { total: number; active: number; byStatus: Record<string, number> } {
    const byStatus: Record<string, number> = {};
    for (const c of conversations.values()) {
      byStatus[c.status] = (byStatus[c.status] ?? 0) + 1;
    }
    return { total: conversations.size, active: getActive().length, byStatus };
  },
};