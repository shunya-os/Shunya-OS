// Shunya OS — Core Type Definitions
// These mirror the Python architecture canon for TypeScript migration

// ── Foundation Types ──

export type Result<T = any> = {
  success: boolean;
  data?: T;
  error?: string;
};

export enum Priority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum GovernanceLevel {
  DRAFT = "draft",
  AUTO = "auto",
  GOVERN = "govern",
}

// ── Entity Types ──

export interface Entity {
  id: number;
  tenantId: number;
  definitionId: number;
  code: string;
  displayName: string;
  status: string;
  data: Record<string, any>;
  assignedTo?: number;
  isArchived: boolean;
  aiSummary?: string;
  createdAt: string;
  updatedAt: string;
}

export interface EntityDefinition {
  id: number;
  tenantId: number;
  type: string;
  label: string;
  icon: string;
  schema: FieldSchema[];
  statuses: string[];
  layout: "table" | "kanban" | "cards" | "calendar";
  primaryField: string;
  searchableFields: string[];
  isActive: boolean;
}

export interface FieldSchema {
  name: string;
  label: string;
  type: "text" | "number" | "date" | "select" | "boolean" | "textarea" | "file" | "json";
  required?: boolean;
  options?: string[];
}

// ── Knowledge & Memory ──

export enum MemoryClass {
  WORKING = "working",
  EPISODIC = "episodic",
  SEMANTIC = "semantic",
  PROCEDURAL = "procedural",
  RELATIONSHIP = "relationship",
  DECISION = "decision",
  OUTCOME = "outcome",
  LEARNING = "learning",
}

export interface KnowledgeEntry {
  id: number;
  tenantId: number;
  question: string;
  answer: string;
  source: string;
  sourceUrl?: string;
  confidence: number;
  category: string;
  useCount: number;
  createdAt: string;
}

export interface MemoryContext {
  working?: MemoryItem[];
  episodic?: MemoryItem[];
  semantic?: MemoryItem[];
  relationship?: MemoryItem[];
  decision?: MemoryItem[];
}

export interface MemoryItem {
  id: number;
  class: MemoryClass;
  key: string;
  content: string;
  confidence: number;
  authority: number;
  tags: string[];
  entityId?: number;
  createdAt: string;
}

// ── Intelligence Types ──

export interface Decision {
  id: string;
  subject: string;
  outcome: string;
  recommendation: string;
  confidence: number;
  explanation: string;
  evidence: string[];
  alternatives: string[];
  tradeoffs: string[];
  risks: Risk[];
  authority: string;
  timestamp: string;
}

export interface Risk {
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  mitigation?: string;
}

export interface NextAction {
  title: string;
  description: string;
  reason: string;
  priority: Priority;
  targetUrl: string;
  confidence: number;
  requiredAuthority?: string;
}

export interface Plan {
  id: string;
  steps: PlanStep[];
  dependencies: Dependency[];
  createdAt: string;
  status: "active" | "completed" | "stale";
}

export interface PlanStep {
  id: string;
  action: string;
  order: number;
  status: "pending" | "ready" | "active" | "blocked" | "completed";
  assignee?: string;
  dependsOn: string[];
}

export interface Dependency {
  from: string;
  to: string;
  type: "blocks" | "requires" | "triggers";
}

// ── Workflow Types ──

export enum TaskState {
  PENDING = "pending",
  READY = "ready",
  ACTIVE = "active",
  BLOCKED = "blocked",
  AWAITING_APPROVAL = "awaiting_approval",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export interface Workflow {
  id: string;
  planId: string;
  entityId?: number;
  tasks: WorkflowTask[];
  createdAt: string;
}

export interface WorkflowTask {
  id: string;
  title: string;
  state: TaskState;
  owner?: string;
  deadline?: string;
  blockerReason?: string;
  dependencyIds: string[];
  businessConsequence?: string;
}

// ── Execution Types ──

export enum ActionType {
  SEND_MESSAGE = "send_message",
  CREATE_ENTITY = "create_entity",
  UPDATE_ENTITY = "update_entity",
  UPDATE_STATUS = "update_status",
  SEND_EMAIL = "send_email",
  SEND_NOTIFICATION = "send_notification",
  CALL_API = "call_api",
  GENERATE_DOCUMENT = "generate_document",
  SCHEDULE_EVENT = "schedule_event",
  ARCHIVE_ENTITY = "archive_entity",
  ASSIGN_ENTITY = "assign_entity",
}

export interface Execution {
  id: string;
  actionType: ActionType;
  tenantId: number;
  userId: number;
  entityId?: number;
  decisionId?: string;
  planId?: string;
  workflowId?: string;
  governanceLevel: GovernanceLevel;
  params: Record<string, any>;
  result?: Record<string, any>;
  status: "pending" | "completed" | "failed";
  requestedAt: string;
  completedAt?: string;
  durationMs?: number;
}

// ── Observation Types ──

export interface Observation {
  id: number;
  type: string;
  entityId?: number;
  summary: string;
  expectedOutcome?: string;
  actualOutcome?: string;
  outcomeMatch?: OutcomeComparison;
  createdAt: string;
}

export interface OutcomeComparison {
  match: boolean;
  confidence: "high" | "medium" | "low";
  finding: string;
}

// ── Learning Types ──

export interface LearningProposal {
  id: number;
  title: string;
  description: string;
  recommendation: string;
  type: string;
  confidence: number;
  evidenceCount: number;
  status: "proposed" | "under_review" | "approved" | "rejected" | "needs_more_evidence";
  governance: GovernanceLevel;
  icon: string;
  createdAt: string;
}

// ── Agent Types ──

export enum AgentCapability {
  KNOWLEDGE_QUERY = "knowledge_query",
  SALES_INTELLIGENCE = "sales_intelligence",
  FINANCE_INTELLIGENCE = "finance_intelligence",
  OPERATIONS_INTELLIGENCE = "operations_intelligence",
  CUSTOMER_INTELLIGENCE = "customer_intelligence",
  LEARNING_INTELLIGENCE = "learning_intelligence",
  RISK_ASSESSMENT = "risk_assessment",
}

export interface AgentResult {
  agent: string;
  capability: string;
  confidence: number;
  summary: string;
  details: Record<string, any>;
  nextActions: NextAction[];
  risks: Risk[];
  needsHuman: boolean;
}

// ── Event Types ──

export type ShunyaEvent =
  | { type: "EntityCreated"; payload: { entityId: number; entityType: string; code: string } }
  | { type: "EntityStatusChanged"; payload: { entityId: number; from: string; to: string } }
  | { type: "TaskBlocked"; payload: { taskId: string; workflowId: string; reason: string } }
  | { type: "DecisionMade"; payload: { decisionId: string; subject: string; outcome: string } }
  | { type: "LearningProposed"; payload: { proposalId: number; pattern: string; confidence: number } }
  | { type: "ExecutionCompleted"; payload: { executionId: string; actionType: string; status: string } };

// ── API Types ──

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
  };
}

export interface OrchestrateRequest {
  query: string;
  capabilities?: string[];
  entityId?: number;
}

export interface OrchestrateResponse {
  query: string;
  agentsInvoked: string[];
  results: AgentResult[];
  synthesis: {
    summary: string;
    criticalRisks: Risk[];
    nextActions: NextAction[];
  };
}