/**
 * @shunya/foundation — Core types and utilities for Shunya OS.
 *
 * Every package in the monorepo builds on these primitives.
 * This is the shared language between all intelligence layers.
 *
 * ── Contents ──
 * 1. Result<T> — success/failure wrapper (the universal return type)
 * 2. Priority — LOW | MEDIUM | HIGH | CRITICAL
 * 3. Action & NextAction — structured next-best-action system
 * 4. Decision — reasoned decision with evidence
 * 5. Outcome — generic outcome from any intelligence layer
 * 6. PipelineResult — what the knowledge/reasoning/planning pipeline produces
 * 7. Validation utilities
 * 8. Type Guards
 */

// ============================================================================
// Result<T> — Universal Return Type
// ============================================================================

export interface SuccessResult<T = any> {
  success: true;
  data: T;
  error?: undefined;
}

export interface FailureResult {
  success: false;
  data?: undefined;
  error: string;
  errorCode?: string;
  details?: unknown;
}

export type Result<T = any> = SuccessResult<T> | FailureResult;

export function ok<T>(data: T): SuccessResult<T> {
  return { success: true, data };
}

export function fail(error: string, errorCode?: string, details?: unknown): FailureResult {
  return { success: false, error, errorCode, details };
}

export function isOk<T>(result: Result<T>): result is SuccessResult<T> {
  return result.success === true;
}

export function isFail<T>(result: Result<T>): result is FailureResult {
  return result.success === false;
}

export function unwrap<T>(result: Result<T>): T {
  if (result.success) return result.data;
  throw new Error(result.error);
}

export function unwrapOr<T>(result: Result<T>, fallback: T): T {
  return result.success ? result.data : fallback;
}

// ============================================================================
// Priority
// ============================================================================

export enum Priority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export function priorityWeight(p: Priority): number {
  const weights: Record<Priority, number> = {
    [Priority.LOW]: 0,
    [Priority.MEDIUM]: 1,
    [Priority.HIGH]: 2,
    [Priority.CRITICAL]: 3,
  };
  return weights[p];
}

export function comparePriority(a: Priority, b: Priority): number {
  return priorityWeight(a) - priorityWeight(b);
}

// ============================================================================
// Action & NextAction
// ============================================================================

export interface Action {
  label: string;           // "Send follow-up message"
  description?: string;    // Why this action makes sense
  icon?: string;           // Emoji for UI
  priority: Priority;      // How important this is
  target?: string;         // URL or route to execute
  params?: Record<string, unknown>;  // Parameters for execution
  expiresAt?: string;      // ISO timestamp — action is only relevant until this time
  source?: string;         // Which agent/engine proposed this
}

export interface NextAction {
  primary: Action;         // The single most important thing to do right now
  alternatives: Action[];  // Other viable options
  reason: string;          // Why this action was chosen over alternatives
  confidence: number;      // 0-1 how sure we are this is the right next action
  context?: string;        // Natural language explanation
}

export function createNextAction(
  primary: Action,
  reason: string,
  confidence: number,
  alternatives: Action[] = [],
): NextAction {
  return { primary, alternatives, reason, confidence };
}

export function sortByPriority(actions: Action[]): Action[] {
  return [...actions].sort((a, b) => comparePriority(b.priority, a.priority));
}

export function filterExpired(actions: Action[]): Action[] {
  const now = new Date().toISOString();
  return actions.filter(a => !a.expiresAt || a.expiresAt > now);
}

// ============================================================================
// Decision — structured reasoned decision
// ============================================================================

export type DecisionStatus = "pending" | "made" | "executed" | "superseded";

export interface Evidence {
  fact: string;            // What was observed
  source: string;          // Where this fact came from
  confidence: number;      // 0-1 how reliable this evidence is
  timestamp: string;       // When this evidence was gathered
}

export interface TradeOff {
  factor: string;          // What's being traded off
  impact: string;          // Effect of this trade-off
  severity: "low" | "medium" | "high";
}

export interface Decision {
  id: string;              // Unique decision ID
  title: string;           // "Move lead to proposal stage"
  decision: string;        // The actual decision text
  status: DecisionStatus;
  confidence: number;      // 0-1
  evidence: Evidence[];    // Supporting facts
  tradeOffs: TradeOff[];   // What was sacrificed
  alternatives: { label: string; reason: string }[];
  madeBy: string;          // "ai" | user email | "system"
  madeAt: string;          // ISO timestamp
  executedAt?: string;
  supersededBy?: string;   // Decision that replaced this one
  tags: string[];
}

// ============================================================================
// Outcome — generic result from any intelligence layer
// ============================================================================

export type OutcomeStatus =
  | "resolved"      // Successfully answered / completed
  | "partial"       // Partially answered, needs follow-up
  | "ambiguous"     // Multiple interpretations need human clarification
  | "needs_human"   // Cannot resolve — needs human intervention
  | "failed";       // Error occurred

export interface Outcome {
  status: OutcomeStatus;
  summary: string;
  details?: Record<string, unknown>;
  nextActions: NextAction[];
  risks: Risk[];
  decisions: Decision[];
  confidence: number;
  durationMs?: number;
  pipeline?: string[];  // Trace of which layers were invoked
}

export interface Risk {
  type: string;            // "deadline_miss", "budget_overrun", etc.
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  probability: number;     // 0-1
  mitigation?: string;     // How to reduce this risk
  owner?: string;          // Who should address this
}

// ============================================================================
// PipelineResult — staged intelligence pipeline output
// ============================================================================

export type PipelineStage =
  | "knowledge"      // Internal data + web search
  | "reasoning"      // Producing decisions/recommendations
  | "planning"       // Multi-step action plan
  | "governance"     // Authority check (draft/auto/govern)
  | "orchestration"  // Multi-agent coordination
  | "execution";     // Performing the action

export interface PipelineResult {
  query: string;
  stages: PipelineStage[];
  currentStage: PipelineStage;
  result: Outcome;
  trace: StageTrace[];
  complete: boolean;
}

export interface StageTrace {
  stage: PipelineStage;
  startedAt: string;
  completedAt?: string;
  durationMs?: number;
  status: "pending" | "running" | "complete" | "skipped" | "error";
  error?: string;
  result?: unknown;
}

// ============================================================================
// Validation Utilities
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

export function validateRequired(value: unknown, fieldName: string): ValidationError | null {
  if (value === undefined || value === null || value === "") {
    return { field: fieldName, message: `${fieldName} is required` };
  }
  return null;
}

export function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function validatePhone(phone: string): boolean {
  return /^[+]?[\d\s-]{7,20}$/.test(phone);
}

export function validateResult<T>(validations: ValidationError[]): Result<T> {
  if (validations.length > 0) {
    return fail(
      validations.map(v => v.message).join("; "),
      "VALIDATION_ERROR",
      validations,
    );
  }
  return ok(true as unknown as T);
}

// ============================================================================
// Type Guards
// ============================================================================

export function isAction(value: unknown): value is Action {
  if (typeof value !== "object" || value === null) return false;
  const a = value as Record<string, unknown>;
  return typeof a.label === "string" && typeof a.priority === "string";
}

export function isDecision(value: unknown): value is Decision {
  if (typeof value !== "object" || value === null) return false;
  const d = value as Record<string, unknown>;
  return typeof d.id === "string" && typeof d.decision === "string";
}

export function isRisk(value: unknown): value is Risk {
  if (typeof value !== "object" || value === null) return false;
  const r = value as Record<string, unknown>;
  return typeof r.type === "string" && typeof r.severity === "string";
}

// ============================================================================
// Constants
// ============================================================================

export const SHUNYA_VERSION = "0.1.0";
export const SHUNYA_CODENAME = "Nakshatra";

export const GOVERNANCE_LABELS = {
  draft: "📝 Draft — AI proposes, user confirms",
  auto: "⚡ Auto — executes immediately, reversible",
  govern: "🔐 Govern — needs admin/manager approval",
} as const;

export const DEFAULT_STATUS_FLOWS: Record<string, string[]> = {
  lead: ["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"],
  patient: ["registered", "checked_in", "in_consultation", "diagnosed", "treatment", "discharged", "follow_up"],
  order: ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"],
  project: ["draft", "active", "in_review", "completed", "archived"],
  task: ["todo", "in_progress", "in_review", "done", "blocked"],
};