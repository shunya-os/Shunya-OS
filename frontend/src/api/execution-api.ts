/**
 * Execution API — Typed client for SHUNYA execution run + task lifecycle endpoints.
 *
 * Every function returns a normalized `{ success, data, error }` envelope so the
 * UI can render meaningful empty/error states instead of throwing. All requests
 * use `credentials: 'include'` to ride the same-origin Flask session cookie.
 */

const BASE = '/api/v1/execution';

// ── Types (mirror app/execution/core_models.py + task_lifecycle.py) ──

export interface ExecutionRun {
  execution_id: string;
  organization_id?: number;
  identity_id?: number | null;
  workspace_id?: number | null;
  run_type: string;
  status: string; // queued | in_progress | completed | failed
  current_phase?: string | null;
  intent: string;
  intent_summary?: string | null;
  used_company_data?: boolean;
  used_internet_data?: boolean;
  used_ai?: boolean;
  started_at?: string | null;
  completed_at?: string | null;
  duration_seconds?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
  result_summary?: string | null;
  error?: string | null;
  error_count?: number;
  correlation_id?: string | null;
  parent_run_id?: string | null;
  source?: string;
  outcome_id?: string | null;
  commitment_id?: string | null;
  commitment_type?: string | null;
}

export interface ExecutionStateTransition {
  id?: number;
  execution_id: string;
  state_before: string;
  state_after: string;
  transitioned_at?: string | null;
  actor?: string;
  reason?: string;
  correlation_id?: string | null;
  metadata?: Record<string, unknown>;
}

export interface TaskPhase {
  phase: string;
  started_at?: string;
  duration?: number;
}

export interface TaskLifecycle {
  task_id: string;
  organization_id?: number;
  identity_id?: number | null;
  execution_run_id?: string | null;
  title: string;
  description?: string;
  status: string; // pending | in_progress | completed | failed | cancelled | blocked
  current_phase?: string | null;
  phase_history?: TaskPhase[];
  created_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  duration_seconds?: number | null;
  result_summary?: string | null;
  result_detail?: unknown;
  outcome?: string | null;
  next_action?: string | null;
  next_action_url?: string | null;
}

/** Full detail — task lifecycle enriched with its execution run + transitions. */
export interface TaskDetail {
  task?: TaskLifecycle | null;
  run?: ExecutionRun | null;
  transitions?: ExecutionStateTransition[];
}

export interface ExecutionApiResult<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

// ── Helpers ────────────────────────────────────────────────────────────

async function getJson<T>(path: string): Promise<ExecutionApiResult<T>> {
  try {
    const r = await fetch(`${BASE}${path}`, { credentials: 'include' });
    if (!r.ok) {
      if (r.status === 401 || r.status === 403) {
        return { success: false, data: null, error: 'Session expired — please sign in again.' };
      }
      if (r.status === 404) {
        return { success: false, data: null, error: 'Not found.' };
      }
      return { success: false, data: null, error: `Request failed (${r.status}).` };
    }
    const json = await r.json();
    // Backend envelope: { success: bool, data: T, error?: string }
    if (json && typeof json === 'object' && 'success' in json) {
      return {
        success: Boolean(json.success),
        data: json.success ? (json.data as T) : null,
        error: json.error || null,
      };
    }
    // Defensive: some endpoints may return the payload directly
    return { success: true, data: json as T, error: null };
  } catch (e) {
    return {
      success: false,
      data: null,
      error: e instanceof Error ? `Could not reach SHUNYA (${e.message}).` : 'Could not reach SHUNYA.',
    };
  }
}

function asArray<T>(data: T[] | null | undefined): T[] {
  return Array.isArray(data) ? data : [];
}

// ── Endpoints ──────────────────────────────────────────────────────────

/** GET /api/v1/execution/tasks/active — live work SHUNYA is performing now. */
export async function fetchActiveTasks(): Promise<ExecutionApiResult<TaskLifecycle[]>> {
  const res = await getJson<TaskLifecycle[]>('/tasks/active');
  return { ...res, data: asArray(res.data) };
}

/** GET /api/v1/execution/tasks — recent task lifecycles (newest first). */
export async function fetchRecentTasks(): Promise<ExecutionApiResult<TaskLifecycle[]>> {
  const res = await getJson<TaskLifecycle[]>('/tasks');
  return { ...res, data: asArray(res.data) };
}

/** GET /api/v1/execution/tasks/attention — tasks needing human intervention. */
export async function fetchAttentionTasks(): Promise<ExecutionApiResult<TaskLifecycle[]>> {
  const res = await getJson<TaskLifecycle[]>('/tasks/attention');
  return { ...res, data: asArray(res.data) };
}

/**
 * GET /api/v1/execution/runs/<execution_id> — full run detail.
 * Accepts a task_id or execution_id; if the raw run lookup 404s we fall back
 * to the task lifecycle endpoint so the detail view always has real content.
 */
export async function fetchTaskDetail(taskId: string): Promise<ExecutionApiResult<TaskDetail>> {
  const id = encodeURIComponent(taskId);
  const runRes = await getJson<ExecutionRun>(`/runs/${id}`);

  if (runRes.success && runRes.data) {
    const transitions = Array.isArray((runRes.data as ExecutionRun & { transitions?: unknown }).transitions)
      ? (runRes.data as ExecutionRun & { transitions: ExecutionStateTransition[] }).transitions
      : [];
    return { success: true, data: { run: runRes.data, transitions }, error: null };
  }

  // Fallback: try the task lifecycle endpoint
  const taskRes = await getJson<TaskLifecycle>(`/tasks/${id}`);
  if (taskRes.success && taskRes.data) {
    return { success: true, data: { task: taskRes.data }, error: null };
  }

  // Neither worked — surface the run error (more likely to be the meaningful one)
  return { success: false, data: null, error: runRes.error || taskRes.error || 'Task not found.' };
}
