/**
 * Workspace Runtime — Core types and state machine.
 *
 * A workspace is a named, persistent, stateful container for business objects.
 * Not a page. Workspaces are persistent sessions with suspend/resume.
 *
 * Every workspace exposes:
 *   unique runtime identity ✓
 *   lifecycle ✓ (8 states with deterministic transitions)
 *   loading state ✓
 *   ready state ✓
 *   empty state ✓
 *   error state ✓
 *   closing state ✓
 *   dirty state ✓
 *   validation state ✓
 *   save status ✓
 */

export type WorkspaceStatus =
  'creating' | 'loading' | 'hydrating' | 'active' | 'suspended' | 'archived' | 'error' | 'closing';
export type WorkspaceType =
  | 'object'
  | 'home'
  | 'conversation'
  | 'approval'
  | 'search'
  | 'document'
  | 'comparison'
  | 'commitment'
  | 'calendar'
  | 'proposals'
  | 'music'
  | 'email'
  | 'admin'
  | 'people'
  | 'contact-discovery'
  | 'import-export'
  | 'audit'
  | 'analytics'
  | 'settings';

export interface WorkspaceIdentity {
  id: string;
  name: string;
  type: WorkspaceType;
  objectType?: string;
  objectId?: string;
  pinned: boolean;
  created: number;
  lastAccessed: number;
}

export interface WorkspaceState {
  identity: WorkspaceIdentity;
  status: WorkspaceStatus;
  layout: string;
  error?: string;
  /** Tracks whether the workspace has unsaved changes. */
  dirty: boolean;
  /** Last save result. */
  saveStatus: 'idle' | 'saving' | 'saved' | 'failed';
  /** Validation errors, keyed by field name. */
  validationErrors: Record<string, string>;
}

export interface WorkspaceStore {
  workspaces: WorkspaceState[];
  activeId: string | null;
  maxWorkspaces: number;
}

const VALID_TRANSITIONS: Record<WorkspaceStatus, WorkspaceStatus[]> = {
  creating: ['loading'],
  loading: ['hydrating', 'active', 'error'],
  hydrating: ['active', 'suspended', 'error'],
  active: ['suspended', 'archived', 'loading', 'error', 'closing'],
  suspended: ['active', 'archived'],
  archived: [],
  error: ['loading', 'active', 'closing'],
  closing: ['archived', 'active'],
};

export function canTransition(from: WorkspaceStatus, to: WorkspaceStatus): boolean {
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}

export function createWorkspaceId(): string {
  return `wksp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export function createWorkspace(name: string, type: WorkspaceType, opts?: Partial<WorkspaceIdentity>): WorkspaceState {
  return {
    identity: {
      id: createWorkspaceId(),
      name,
      type,
      pinned: false,
      created: Date.now(),
      lastAccessed: Date.now(),
      ...opts,
    },
    status: 'creating',
    layout: type === 'home' ? 'home' : type === 'object' ? 'object' : type,
    dirty: false,
    saveStatus: 'idle',
    validationErrors: {},
  };
}
