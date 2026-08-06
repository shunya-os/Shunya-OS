// SHUNYA Frontend — Core Type System

// ===== Design Tokens =====
export interface ThemeTokens {
  brand: { primary: string; primarySubtle: string; secondary: string };
  surfaces: { primary: string; secondary: string; tertiary: string; raised: string; hover: string };
  text: { primary: string; secondary: string; tertiary: string; link: string; onBrand: string };
  semantic: { success: string; warning: string; error: string; info: string };
}

export type ThemeMode = 'dark' | 'light';

// ===== Navigation =====
export interface WorkspaceDef {
  id: string;
  icon: string;
  name: string;
  order: number;
}

export interface BreadcrumbSegment {
  label: string;
  href?: string;
  icon?: string;
}

export interface NavigationState {
  currentWorkspace: string;
  currentObjectId: string | null;
  activeSection: string;
  history: string[];
  historyIndex: number;
}

// ===== Object Model =====
export interface ObjectData {
  id: string;
  type: string;
  typeIcon: string;
  name: string;
  status: { label: string; class: string };
  confidence?: number;
  summary?: string;
}

export interface SectionDef {
  id: string;
  icon: string;
  label: string;
  count?: number;
}

// ===== AI =====
export interface Suggestion {
  id: string;
  text: string;
  confidence: number;
  sourceCount: number;
  dismissed?: boolean;
}

export interface AIState {
  suggestions: Suggestion[];
  isExpanded: boolean;
  conversation: Array<{ role: 'user' | 'ai'; text: string }>;
}

// ===== Component Props (shared) =====
export type Size = 'sm' | 'md' | 'lg';
export type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

export interface BaseProps {
  className?: string;
  children?: React.ReactNode;
}

// ===== Workspace =====
export interface WorkspaceType {
  id: string;
  name: string;
  workspace_type: 'business' | 'personal' | 'custom';
  icon: string;
  color: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// ===== Events =====
export interface AppEvent {
  type: string;
  payload?: unknown;
  timestamp: number;
}

export type EventHandler = (event: AppEvent) => void;

// ===== API =====
export interface APIResponse<T> {
  data: T | null;
  error: string | null;
  status: number;
}

export interface QueryParams {
  [key: string]: string | number | boolean | undefined;
}

// ===== Overlay =====
export interface OverlayState {
  id: string;
  type: 'dialog' | 'drawer' | 'command' | 'popover' | 'tooltip';
  props?: Record<string, unknown>;
  open: boolean;
}

// ===== Panel =====
export interface PanelState {
  contextPanelOpen: boolean;
  contextPanelWidth: number;
  activePanels: string[];
}

// ===== Selection =====
export interface SelectionState {
  selectedIds: string[];
  lastSelectedId: string | null;
  mode: 'single' | 'multiple' | 'range';
}

// ===== Focus =====
export interface FocusState {
  focusedElementId: string | null;
  focusHistory: string[];
}
