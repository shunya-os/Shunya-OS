/**
 * Workspace Composition Engine — Dynamically assembles workspaces from runtime state + components + layouts.
 */

import { orchestrator } from '../orchestrator';
import { getLayout, fitPanels } from '../layout/engine';
import { getComponent } from '../../components/registry';
import type { ComponentType } from 'react';

// ── Types ──────────────────────────────────────────────────────

export interface PanelComposition {
  componentId: string;
  propsResolver: (state: Record<string, unknown>) => Record<string, unknown>;
  dependsOn: string[];
  critical?: boolean;
  label?: string;
}

export interface WorkspaceDefinition {
  id: string;
  name: string;
  description: string;
  supportedObjectTypes: string[];
  requiredRuntimes: string[];
  layoutTemplate: string;
  panels: PanelComposition[];
}

// ── Registry ──────────────────────────────────────────────────

const registry = new Map<string, WorkspaceDefinition>();

export const WorkspaceRegistry = {
  register(def: WorkspaceDefinition): void { registry.set(def.id, def); },
  get(id: string): WorkspaceDefinition | undefined { return registry.get(id); },
  getAll(): WorkspaceDefinition[] { return Array.from(registry.values()); },
  clear(): void { registry.clear(); },
};

// ── Default Workspaces ────────────────────────────────────────

export function registerDefaultWorkspaces(): void {
  // Workspace registration moved to modules. See api/modules/.
}

// ── Composition ────────────────────────────────────────────────

export interface ComposedPanel {
  id: string;
  componentId: string;
  Component: ComponentType<any> | undefined;
  props: Record<string, unknown>;
  loading: boolean;
  error?: string;
  label?: string;
}

export interface ComposedWorkspace {
  definition: WorkspaceDefinition;
  panels: ComposedPanel[];
  ready: boolean;
}

function checkRuntime(id: string): boolean {
  return orchestrator.get(id)?.status === 'ready';
}

export const CompositionEngine = {
  compose(defId: string, availableWidth: number, runtimeStates: Record<string, Record<string, unknown>>): ComposedWorkspace {
    const def = WorkspaceRegistry.get(defId);
    if (!def) throw new Error(`Unknown workspace: ${defId}`);

    const layout = getLayout(def.layoutTemplate);
    const panelSlots = fitPanels(layout, availableWidth);
    const panelMap = new Map(def.panels.map(p => [p.componentId, p]));

    const panels: ComposedPanel[] = panelSlots.map(slot => {
      const comp = panelMap.get(slot.id);
      if (!comp) return { id: slot.id, componentId: slot.id, Component: undefined, props: {}, loading: true, error: `No composition for ${slot.id}` };

      const meta = getComponent(comp.componentId);
      if (!meta) return { id: slot.id, componentId: comp.componentId, Component: undefined, props: {}, loading: true, error: `Unknown component: ${comp.componentId}` };

      const failed = comp.dependsOn.some(d => orchestrator.get(d)?.status === 'failed');
      if (failed) {
        return { id: slot.id, componentId: comp.componentId, Component: meta.component as ComponentType<any>, props: {}, loading: false, error: `${comp.label || comp.componentId} unavailable`, label: comp.label };
      }

      const state = comp.dependsOn.reduce((acc, dep) => Object.assign(acc, runtimeStates[dep] ?? {}), {} as Record<string, unknown>);
      const props = comp.propsResolver(state);
      const loading = (comp.critical ?? false) && comp.dependsOn.some(d => !checkRuntime(d));

      return { id: slot.id, componentId: comp.componentId, Component: meta.component as ComponentType<any>, props, loading, label: comp.label };
    });

    return { definition: def, panels, ready: panels.every(p => !p.loading || !!p.error) };
  },

  isAvailable(defId: string): boolean {
    const def = WorkspaceRegistry.get(defId);
    return def ? def.requiredRuntimes.every(r => checkRuntime(r)) : false;
  },
};