/**
 * Workspace Runtime — Core types and state machine.
 *
 * A workspace is a named, persistent, stateful container for business objects.
 * Not a page. Workspaces are persistent sessions with suspend/resume.
 */

export type WorkspaceStatus = 'creating' | 'loading' | 'hydrating' | 'active' | 'suspended' | 'archived';
export type WorkspaceType = 'object' | 'dashboard' | 'conversation' | 'approval' | 'search' | 'document' | 'comparison' | 'commitment';

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
}

export interface WorkspaceStore {
  workspaces: WorkspaceState[];
  activeId: string | null;
  maxWorkspaces: number;
}

const VALID_TRANSITIONS: Record<WorkspaceStatus, WorkspaceStatus[]> = {
  creating: ['loading'],
  loading: ['hydrating', 'active'],
  hydrating: ['active', 'suspended'],
  active: ['suspended', 'archived', 'loading'],
  suspended: ['active', 'archived'],
  archived: [],
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
    layout: type === 'dashboard' ? 'executive' : type === 'object' ? 'object' : type,
  };
}