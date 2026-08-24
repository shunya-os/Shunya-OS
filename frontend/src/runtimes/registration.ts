import { orchestrator, type RuntimeRegistration, type RuntimeHealth, type RuntimeStatus } from './orchestrator';
import { stateFabric, type StateRegistration } from './state-fabric';
import { CommitmentRuntime } from './commitment/engine';
import { ConversationRuntime } from './conversation/engine';
import { experience } from './experience/engine';
import { ObjectRuntime } from './object/engine';
import { ObjectGraphRuntime } from './graph/engine';
import { TimelineRuntime } from './timeline/engine';
import { IntelligenceRuntime } from './intelligence/engine';
import { bus } from './event-bus';

function h(status: RuntimeStatus): RuntimeHealth {
  return { status, startedAt: null, lastActivity: null, lastFailure: null, startupMs: null, retryCount: 0 };
}

function reg(opts: {
  id: string;
  version: string;
  description: string;
  deps: string[];
  critical?: boolean;
  pub: string[];
  sub: string[];
  start: () => Promise<void>;
  stop?: () => Promise<void>;
  health: () => RuntimeHealth;
  state?: StateRegistration;
}): RuntimeRegistration {
  const r: RuntimeRegistration = {
    id: opts.id,
    version: opts.version,
    description: opts.description,
    dependencies: opts.deps,
    critical: opts.critical !== false,
    eventsPublished: opts.pub,
    eventsSubscribed: opts.sub,
    startup: opts.start,
    shutdown: opts.stop ?? (async () => {}),
    health: opts.health,
  };
  if (opts.state) {
    const orig = r.startup;
    r.startup = async () => {
      stateFabric.register(opts.state!);
      await orig();
    };
  }
  return r;
}

const RT = (
  id: string,
  ver: string,
  desc: string,
  deps: string[],
  pub: string[],
  sub: string[],
  start: () => Promise<void>,
  state?: StateRegistration,
): RuntimeRegistration =>
  reg({ id, version: ver, description: desc, deps, pub, sub, start, health: () => h('ready'), state });

const ALL: RuntimeRegistration[] = [
  RT(
    'state-fabric',
    '1.0',
    'Universal State Fabric',
    ['event-bus'],
    [
      'RuntimeStateRegistered',
      'RuntimeStateChanged',
      'RuntimeSnapshotCreated',
      'RuntimeSnapshotRestored',
      'RuntimeStateInvalidated',
      'TransactionCommitted',
      'TransactionRolledBack',
    ],
    [],
    async () => {},
  ),
  RT('event-bus', '1.0', 'Typed event bus', [], [], [], async () => {
    bus.clear();
  }),
  RT('token-runtime', '1.0', 'Design token system', [], [], [], async () => {}),
  RT('layout-engine', '1.0', 'Layout engine', [], [], [], async () => {}),
  RT(
    'workspace-runtime',
    '1.0',
    'Workspace lifecycle',
    [],
    ['WorkspaceOpened', 'WorkspaceHydrated', 'WorkspaceSuspended', 'WorkspaceResumed', 'WorkspaceDestroyed'],
    ['ObjectLoaded', 'TimelineLoaded'],
    async () => {},
    {
      runtimeId: 'workspace-runtime',
      version: 1,
      schema: { activeId: 'string', workspaceCount: 'number' },
      persistence: 'session',
      sync: 'local',
      snapshot: true,
    },
  ),
  RT(
    'object-runtime',
    '1.0',
    'Object lifecycle',
    [],
    ['ObjectRequested', 'ObjectLoaded', 'ObjectUpdated', 'ObjectCached', 'ObjectError'],
    ['WorkspaceOpened'],
    async () => {
      ObjectRuntime.clear();
    },
    {
      runtimeId: 'object-runtime',
      version: 1,
      schema: { cacheSize: 'number' },
      persistence: 'transient',
      sync: 'local',
      snapshot: false,
    },
  ),
  RT(
    'object-graph-runtime',
    '1.0',
    'Relationship graph',
    ['object-runtime'],
    [
      'ObjectLinked',
      'ObjectUnlinked',
      'RelationshipCreated',
      'RelationshipUpdated',
      'RelationshipRemoved',
      'GraphHydrated',
      'GraphExpanded',
      'GraphCollapsed',
    ],
    ['ObjectLoaded', 'WorkspaceOpened'],
    async () => {
      ObjectGraphRuntime.clear();
    },
    {
      runtimeId: 'object-graph-runtime',
      version: 1,
      schema: { nodes: 'number', edges: 'number' },
      persistence: 'transient',
      sync: 'local',
      snapshot: false,
    },
  ),
  RT(
    'timeline-runtime',
    '1.0',
    'Event stream',
    ['object-runtime'],
    ['TimelineRequested', 'TimelineLoaded', 'TimelineUpdated'],
    ['WorkspaceOpened', 'ObjectUpdated'],
    async () => {
      TimelineRuntime.clear();
    },
    {
      runtimeId: 'timeline-runtime',
      version: 1,
      schema: { cachedEvents: 'number' },
      persistence: 'transient',
      sync: 'local',
      snapshot: false,
    },
  ),
  RT(
    'intelligence-runtime',
    '1.0',
    'AI insights',
    ['object-runtime', 'object-graph-runtime', 'timeline-runtime'],
    ['IntelligenceRequested', 'IntelligenceLoaded', 'IntelligenceError'],
    ['WorkspaceOpened', 'ObjectLoaded', 'ObjectUpdated'],
    async () => {
      IntelligenceRuntime.clear();
    },
    {
      runtimeId: 'intelligence-runtime',
      version: 1,
      schema: { cachedInsights: 'number' },
      persistence: 'transient',
      sync: 'local',
      snapshot: true,
    },
  ),
  RT(
    'commitment-runtime',
    '1.0',
    'Execution lifecycle',
    ['object-runtime', 'object-graph-runtime', 'timeline-runtime', 'intelligence-runtime'],
    [
      'CommitmentCreated',
      'CommitmentActivated',
      'CommitmentBlocked',
      'CommitmentResumed',
      'CommitmentCompleted',
      'CommitmentCancelled',
      'CommitmentEvidenceAdded',
      'CommitmentConfidenceChanged',
      'CommitmentRiskDetected',
    ],
    ['ObjectUpdated', 'ObjectLoaded'],
    async () => {
      CommitmentRuntime.clear();
    },
    {
      runtimeId: 'commitment-runtime',
      version: 1,
      schema: { commitments: 'object', stats: 'object' },
      persistence: 'session',
      sync: 'optimistic',
      snapshot: true,
    },
  ),
  RT(
    'conversation-runtime',
    '1.0',
    'Business conversation contexts',
    ['object-runtime', 'object-graph-runtime', 'timeline-runtime', 'intelligence-runtime', 'commitment-runtime'],
    [
      'ConversationCreated',
      'ConversationActivated',
      'ConversationIntentChanged',
      'ConversationContextChanged',
      'ConversationArchived',
      'ConversationParticipantAdded',
      'ConversationParticipantRemoved',
    ],
    [],
    async () => {
      ConversationRuntime.clear();
    },
    {
      runtimeId: 'conversation-runtime',
      version: 1,
      schema: { totalConversations: 'number' },
      persistence: 'session',
      sync: 'optimistic',
      snapshot: true,
    },
  ),
  RT(
    'experience-engine',
    '1.0',
    'Executive Experience Engine',
    ['event-bus', 'workspace-runtime', 'intelligence-runtime', 'commitment-runtime', 'conversation-runtime'],
    ['ExecutiveContextChanged', 'ExecutiveCommandExecuted', 'ExecutiveNotificationCreated'],
    [],
    async () => {
      experience.registerDefaultCommands();
    },
    {
      runtimeId: 'experience-engine',
      version: 1,
      schema: { context: 'string', notificationCount: 'number' },
      persistence: 'session',
      sync: 'local',
      snapshot: false,
    },
  ),
];

// Mark non-critical runtimes (background hydration — don't block workspace)
const NON_CRITICAL = new Set([
  'object-runtime',
  'object-graph-runtime',
  'timeline-runtime',
  'intelligence-runtime',
  'commitment-runtime',
  'conversation-runtime',
  'experience-engine',
]);
for (const r of ALL) {
  if (NON_CRITICAL.has(r.id)) {
    r.critical = false;
  }
}

export function registerAllRuntimes(): void {
  ALL.forEach((r) => orchestrator.register(r));
}