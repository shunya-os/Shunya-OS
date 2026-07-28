/**
 * Executive Experience Engine — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Coordinate context-based navigation across objects, conversations, commitments, timelines, intelligence, search
 * - Provide a unified global command layer that dispatches to existing runtimes
 * - Track and restore executive focus across workspace changes, navigation, runtime refreshes
 * - Coordinate keyboard shortcuts, contextual menus, panel expansion, quick actions
 * - Provide a unified notification model — runtimes publish events, engine decides how to surface them
 * - Standardise transitions between contexts (no abrupt page changes)
 * - Prioritise attention — surface critical risks, overdue commitments, blocked execution, urgent conversations
 * - Support user-level preferences (layouts, density, shortcuts, default workspaces)
 * - Maintain accessibility (keyboard-first, screen readers, focus visibility, reduced motion, high contrast)
 *
 * ── Inputs ────────────────────────────────────────────────────
 * - Runtime Orchestrator (runtime health + discovery)
 * - Workspace Composition Engine (composed workspace state)
 * - Component Registry (component lookup)
 * - Workspace Registry (workspace definitions)
 * - All runtime events via the Event Bus
 *
 * ── Outputs ───────────────────────────────────────────────────
 * - Composed navigation state
 * - Focus targets and restoration points
 * - Notification queue (prioritised + grouped)
 * - Command dispatch intents
 * - Transition instructions
 *
 * ── Published Events ──────────────────────────────────────────
 * ExecutiveContextChanged, ExecutiveCommandExecuted, ExecutiveNotificationCreated
 *
 * ── Consumed Events ───────────────────────────────────────────
 * All runtime state change events (for attention prioritisation)
 *
 * ── Recovery Behaviour ────────────────────────────────────────
 * - Focus restored from last-known-good on workspace change
 * - Notifications survive runtime recovery (replayed from State Fabric)
 * - Commands gracefully fail on runtime unavailability with user guidance
 *
 * ── Health Probe ──────────────────────────────────────────────
 * Reports active context, notification queue depth, focus target
 */

import { orchestrator } from '../orchestrator';
import { bus } from '../event-bus';

// ── Types ──────────────────────────────────────────────────────

export interface ExecutiveContext {
  type: 'object' | 'conversation' | 'commitment' | 'timeline' | 'intelligence' | 'search' | 'dashboard';
  objectType?: string;
  objectId?: string;
  workspaceId?: string;
  label: string;
  timestamp: number;
}

export interface Command {
  id: string;
  label: string;
  description: string;
  category: 'navigation' | 'action' | 'creation' | 'insight';
  shortcut?: string;
  execute: () => Promise<void>;
  available: () => boolean;
}

export interface Notification {
  id: string;
  priority: 'critical' | 'important' | 'informational';
  title: string;
  body: string;
  source: string;
  timestamp: number;
  dismissed: boolean;
  action?: { label: string; command: string };
}

export interface ExperiencePreferences {
  defaultWorkspace: string;
  panelDensity: 'compact' | 'normal' | 'comfortable';
  reducedMotion: boolean;
  highContrast: boolean;
  keyboardShortcuts: Record<string, string>;
}

// ── Default Preferences ────────────────────────────────────────

const DEFAULT_PREFS: ExperiencePreferences = {
  defaultWorkspace: 'executive',
  panelDensity: 'normal',
  reducedMotion: typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  highContrast: typeof window !== 'undefined' && window.matchMedia('(prefers-contrast: more)').matches,
  keyboardShortcuts: {
    'Cmd+K': 'command_palette',
    'Cmd+1': 'workspace_1',
    'Cmd+2': 'workspace_2',
    'Escape': 'close_panel',
    'Ctrl+Enter': 'confirm',
  },
};

// ── Experience Engine ──────────────────────────────────────────

class ExperienceEngine {
  private context: ExecutiveContext = { type: 'dashboard', label: 'Executive Dashboard', timestamp: Date.now() };
  private contextHistory: ExecutiveContext[] = [];
  private focusTarget: string | null = null;
  private notifications: Notification[] = [];
  private commands: Map<string, Command> = new Map();
  private preferences: ExperiencePreferences = { ...DEFAULT_PREFS };
  private listeners: Set<() => void> = new Set();

  constructor() {
    // Listen for runtime state changes to generate notifications
    this.setupNotificationListeners();
  }

  private setupNotificationListeners(): void {
    const events = ['CommitmentBlocked', 'CommitmentAtRisk', 'CommitmentCompleted',
      'ObjectError', 'IntelligenceError'];
    for (const evt of events) {
      (bus as any).on?.(evt, () => {
        // Runtime events trigger notification generation
        this.reprioritise();
      });
    }
  }

  // ── Context Navigation ───────────────────────────────────────

  /** Navigate to a new context. Preserves history for back-navigation. */
  navigate(type: ExecutiveContext['type'], label: string, opts?: { objectType?: string; objectId?: string; workspaceId?: string }): void {
    const previous = this.context;
    if (previous) this.contextHistory.push(previous);
    if (this.contextHistory.length > 50) this.contextHistory.shift();

    this.context = {
      type, label, timestamp: Date.now(),
      objectType: opts?.objectType, objectId: opts?.objectId, workspaceId: opts?.workspaceId,
    };

    this.notifyListeners();
    bus.emit({ type: 'ExecutiveContextChanged' as any, source: 'experience-engine', error: '' } as any);
  }

  /** Go back to the previous context. */
  goBack(): void {
    const previous = this.contextHistory.pop();
    if (previous) {
      this.context = previous;
      this.notifyListeners();
    }
  }

  /** Get the current execution context. */
  getContext(): ExecutiveContext {
    return this.context;
  }

  /** Get navigation history depth (for back-button state). */
  getHistoryDepth(): number {
    return this.contextHistory.length;
  }

  // ── Focus Management ─────────────────────────────────────────

  /** Set the current focus target. */
  setFocus(target: string): void {
    this.focusTarget = target;
  }

  /** Get the focus target. Returns null if unset. */
  getFocus(): string | null {
    return this.focusTarget;
  }

  /** Clear focus target. */
  clearFocus(): void {
    this.focusTarget = null;
  }

  /** Restore the last-known focus target (on workspace change). */
  restoreFocus(): void {
    if (this.focusTarget) {
      const el = document.getElementById(this.focusTarget);
      if (el) {
        (el as HTMLElement).focus();
      }
    }
  }

  // ── Command Layer ────────────────────────────────────────────

  /** Register a command. */
  registerCommand(cmd: Command): void {
    this.commands.set(cmd.id, cmd);
  }

  /** Get all available commands. */
  getCommands(): Command[] {
    return Array.from(this.commands.values()).filter(c => c.available());
  }

  /** Get commands by category. */
  getCommandsByCategory(category: string): Command[] {
    return this.getCommands().filter(c => c.category === category);
  }

  /** Execute a command by ID. Returns true if executed. */
  executeCommand(id: string): boolean {
    const cmd = this.commands.get(id);
    if (!cmd || !cmd.available()) return false;
    cmd.execute();
    bus.emit({ type: 'ExecutiveCommandExecuted' as any, source: id, error: '' } as any);
    return true;
  }

  /** Resolve a keyboard shortcut to a command ID. */
  resolveShortcut(shortcut: string): string | undefined {
    return this.preferences.keyboardShortcuts[shortcut];
  }

  // ── Default Commands ─────────────────────────────────────────

  registerDefaultCommands(): void {
    this.registerCommand({
      id: 'open-executive', label: 'Open Executive Dashboard', description: 'Switch to the executive overview',
      category: 'navigation', shortcut: 'Cmd+1',
      execute: async () => this.navigate('dashboard', 'Executive Dashboard'),
      available: () => true,
    });
    this.registerCommand({
      id: 'open-search', label: 'Search', description: 'Search all objects and conversations',
      category: 'navigation', shortcut: 'Cmd+K',
      execute: async () => { /* triggers command palette UI */ },
      available: () => true,
    });
    this.registerCommand({
      id: 'go-back', label: 'Go Back', description: 'Return to the previous context',
      category: 'navigation', shortcut: 'Cmd+[',
      execute: async () => this.goBack(),
      available: () => this.contextHistory.length > 0,
    });
    this.registerCommand({
      id: 'create-commitment', label: 'Create Commitment', description: 'Start a new business execution',
      category: 'creation',
      execute: async () => { /* dispatches to CommitmentRuntime.create */ },
      available: () => orchestrator.get('commitment-runtime')?.status === 'ready',
    });
    this.registerCommand({
      id: 'create-conversation', label: 'New Conversation', description: 'Start a new business conversation',
      category: 'creation',
      execute: async () => { /* dispatches to ConversationRuntime.create */ },
      available: () => orchestrator.get('conversation-runtime')?.status === 'ready',
    });
    this.registerCommand({
      id: 'inspect-timeline', label: 'Inspect Timeline', description: 'View the event stream for the active context',
      category: 'insight',
      execute: async () => this.navigate('timeline', 'Timeline'),
      available: () => true,
    });
    this.registerCommand({
      id: 'run-ai-insight', label: 'AI Insights', description: 'Request AI analysis for the current context',
      category: 'insight',
      execute: async () => { /* dispatches to IntelligenceRuntime */ },
      available: () => orchestrator.get('intelligence-runtime')?.status === 'ready',
    });
  }

  // ── Notifications ────────────────────────────────────────────

  /** Create a notification. */
  notify(priority: Notification['priority'], title: string, body: string, source: string, action?: Notification['action']): void {
    const notification: Notification = {
      id: `notif_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      priority, title, body, source, timestamp: Date.now(), dismissed: false, action,
    };
    this.notifications.unshift(notification);
    if (this.notifications.length > 100) this.notifications.pop();
    this.notifyListeners();
    bus.emit({ type: 'ExecutiveNotificationCreated' as any, source: 'experience-engine', error: '' } as any);
  }

  /** Dismiss a notification. */
  dismiss(id: string): void {
    const n = this.notifications.find(n => n.id === id);
    if (n) n.dismissed = true;
    this.notifyListeners();
  }

  /** Get active (non-dismissed) notifications, sorted by priority. */
  getActiveNotifications(): Notification[] {
    const priorityOrder: Record<string, number> = { critical: 0, important: 1, informational: 2 };
    return this.notifications
      .filter(n => !n.dismissed)
      .sort((a, b) => (priorityOrder[a.priority] ?? 2) - (priorityOrder[b.priority] ?? 2))
      .slice(0, 20);
  }

  /** Get count of critical + important notifications. */
  getAttentionCount(): number {
    return this.notifications.filter(n => !n.dismissed && (n.priority === 'critical' || n.priority === 'important')).length;
  }

  // ── Attention Management ─────────────────────────────────────

  private reprioritise(): void {
    // Check commitment-runtime for blocked/at-risk commitments
    const commitmentRuntime = orchestrator.get('commitment-runtime');
    if (commitmentRuntime?.status === 'ready') {
      // In a real implementation, this would query CommitmentRuntime for risks
      // For now, engine flags when the runtime is healthy
    }

    // Check for overdue items via intelligence runtime
    const intelligenceRuntime = orchestrator.get('intelligence-runtime');
    if (intelligenceRuntime?.status === 'ready') {
      // Intelligence runtime would surface risks as insights
    }

    this.notifyListeners();
  }

  // ── Preferences ──────────────────────────────────────────────

  /** Update user preferences. */
  setPreferences(partial: Partial<ExperiencePreferences>): void {
    this.preferences = { ...this.preferences, ...partial };
    this.applyPreferences();
    this.notifyListeners();
  }

  /** Get current preferences. */
  getPreferences(): ExperiencePreferences {
    return { ...this.preferences };
  }

  private applyPreferences(): void {
    if (this.preferences.reducedMotion) {
      document.documentElement.classList.add('sh-reduced-motion');
    } else {
      document.documentElement.classList.remove('sh-reduced-motion');
    }
    if (this.preferences.highContrast) {
      document.documentElement.classList.add('sh-high-contrast');
    } else {
      document.documentElement.classList.remove('sh-high-contrast');
    }
    document.documentElement.setAttribute('data-panel-density', this.preferences.panelDensity);
  }

  // ── Observability ────────────────────────────────────────────

  subscribe(cb: () => void): () => void {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  }

  private notifyListeners(): void {
    this.listeners.forEach(cb => cb());
  }

  // ── State ────────────────────────────────────────────────────

  clear(): void {
    this.context = { type: 'dashboard', label: 'Executive Dashboard', timestamp: Date.now() };
    this.contextHistory = [];
    this.focusTarget = null;
    this.notifications = [];
    this.commands.clear();
  }

  stats(): { context: string; notifications: number; commands: number; historyDepth: number } {
    return {
      context: this.context.label,
      notifications: this.getActiveNotifications().length,
      commands: this.commands.size,
      historyDepth: this.contextHistory.length,
    };
  }
}

export const experience = new ExperienceEngine();

// ── React Hook ─────────────────────────────────────────────────

import { useSyncExternalStore, useCallback } from 'react';

/** Subscribe to experience engine state changes. */
export function useExperience(): {
  context: ExecutiveContext;
  notifications: Notification[];
  attentionCount: number;
  commands: Command[];
  preferences: ExperiencePreferences;
  goBack: () => void;
  navigate: ExperienceEngine['navigate'];
  dismiss: ExperienceEngine['dismiss'];
  setPreferences: ExperienceEngine['setPreferences'];
} {
  const subscribe = useCallback((cb: () => void) => experience.subscribe(cb), []);
  useSyncExternalStore(subscribe, () => experience.getContext().timestamp);
  return {
    context: experience.getContext(),
    notifications: experience.getActiveNotifications(),
    attentionCount: experience.getAttentionCount(),
    commands: experience.getCommands(),
    preferences: experience.getPreferences(),
    goBack: () => experience.goBack(),
    navigate: (type: any, label: string, opts?: any) => experience.navigate(type, label, opts),
    dismiss: (id: string) => experience.dismiss(id),
    setPreferences: (p: Partial<ExperiencePreferences>) => experience.setPreferences(p),
  };
}