/**
 * Workspace Container — Zone 3 content area.
 *
 * Renders the active workspace inside the three-zone shell.
 * Progressive rendering: the shell is always rendered, content fills in.
 * No boot spinner, no loading screen — the shell itself is the loading indicator.
 *
 * Handles all workspace states:
 *   loading → skeleton
 *   error   → error state with retry
 *   active  → ObjectWorkspaceViewer or composed panels
 *   null    → Home workspace
 *   empty   → no modules, no data
 */

import { useRef, useEffect, useState } from 'react';
import { useActiveWorkspace } from '../../hooks/workspace-hooks';
import { useRuntimeHealth } from '../../hooks/runtime-hooks';
import { useWorkspaceStore } from '../../runtimes/workspace/store';
import { CompositionEngine } from '../../runtimes/composition/engine';
import { ModuleRegistry } from '../../runtimes/module-registry';
import { Panel } from '../executive/index';
import { WorkspaceShell } from './workspace-shell';
import { ExecutiveHome } from '../executive-home/executive-home';
import { ObjectWorkspaceViewer } from './object-workspace-viewer';
import { bus } from '../../runtimes/event-bus';

function WorkspaceErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="wksp-error" role="alert">
      <div className="wksp-error-icon">⚠</div>
      <div className="wksp-error-title">Workspace Error</div>
      <div className="wksp-error-message">{error}</div>
      <button className="wksp-error-retry" onClick={onRetry}>Retry</button>
    </div>
  );
}

function WorkspaceLoadingState() {
  return (
    <div className="wksp-loading" aria-busy="true">
      <div className="wksp-loading-shimmer" />
      <div className="wksp-panels-skeleton">
        <div className="wksp-skel-panel"><div className="sh-skel-line w-32" /><div className="sh-skel-line w-48" /><div className="sh-skel-line w-24" /></div>
        <div className="wksp-skel-panel"><div className="sh-skel-line w-24" /><div className="sh-skel-line w-40" /><div className="sh-skel-line w-36" /></div>
      </div>
    </div>
  );
}

export function WorkspaceContainer() {
  const active = useActiveWorkspace();
  const health = useRuntimeHealth();
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1200);
  const [runtimesReady, setRuntimesReady] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (health.total > 0 && health.ready >= health.total) {
      setRuntimesReady(true);
    }
  }, [health]);

  // Emit workspace lifecycle events when object workspace is active
  useEffect(() => {
    if (!active || active.identity.type !== 'object') return;
    const oid = active.identity.objectId;
    const otype = active.identity.objectType;
    if (oid && otype && active.status === 'loading') {
      bus.emit({ type: 'ObjectLoaded', objectType: otype, objectId: oid, data: {} });
    }
  }, [active?.identity.id, active?.identity.objectId, active?.identity.type, active?.status]);

  const shellContext = active ? {
    workspaceType: active.layout,
    objectId: active.identity.objectId,
    objectType: active.identity.objectType,
  } : { workspaceType: 'home' };

  function renderContent() {
    // While booting, render the Home workspace with skeleton loading
    if (health.total > 0 && !runtimesReady) {
      return <ExecutiveHome loading={true} />;
    }

    // Empty state — no modules, no active workspace
    if (!ModuleRegistry.hasModules && !active) {
      return <ExecutiveHome />;
    }

    // No active workspace — show Executive Home
    if (!active) {
      return <ExecutiveHome />;
    }

    // Error state (from workspace status)
    if (active.status === 'error') {
      return (
        <WorkspaceErrorState
          error={active.error ?? 'Unknown error'}
          onRetry={() => {
            useWorkspaceStore.getState().transitionTo(active.identity.id, 'loading');
          }}
        />
      );
    }

    // Loading state
    if (active.status === 'loading') {
      return <WorkspaceLoadingState />;
    }

    // Object workspace — render the unified object viewer
    if (active.identity.type === 'object' && active.identity.objectId) {
      return (
        <div className="wksp-panels" ref={ref}>
          <ObjectWorkspaceViewer
            objectId={active.identity.objectId}
            objectType={active.identity.objectType}
          />
        </div>
      );
    }

    // Active workspace — compose panels via composition engine
    if (active.status === 'active' || active.status === 'hydrating') {
      const workspaceType = active.layout ?? 'home';
      let composed;
      try {
        composed = CompositionEngine.compose(workspaceType, width, {});
      } catch {
        return <ExecutiveHome />;
      }

      return (
        <div className="wksp-panels" ref={ref}>
          {composed.panels.map(p => {
            if (p.error) {
              return (
                <div key={p.id} className="wksp-panel-error">
                  <div className="wksp-panel-error-label">{p.label ?? p.componentId}</div>
                  <div className="wksp-panel-error-msg">{p.error}</div>
                </div>
              );
            }
            return (
              <Panel key={p.id} id={p.id} name={p.label ?? p.componentId} loading={p.loading} error={p.error}>
                {p.Component && <p.Component state={p.props} loading={p.loading} error={p.error} />}
              </Panel>
            );
          })}
        </div>
      );
    }

    // Fallback
    return <ExecutiveHome />;
  }

  return (
    <WorkspaceShell context={shellContext}>
      {renderContent()}
    </WorkspaceShell>
  );
}

const styles = `
.wksp-panels { display: flex; gap: var(--shunya-spacing-md); padding: var(--shunya-spacing-md); flex: 1; overflow: auto; align-items: stretch; container-type: inline-size; }
.wksp-loading { display: flex; flex-direction: column; gap: var(--shunya-spacing-md); padding: var(--shunya-spacing-lg); flex: 1; }
.wksp-loading-shimmer { height: 4px; background: linear-gradient(90deg, var(--shunya-surface-1, #22222e) 0%, var(--shunya-surface-2, #2a2a3a) 50%, var(--shunya-surface-1, #22222e) 100%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 2px; }
.wksp-panels-skeleton { display: flex; gap: var(--shunya-spacing-md); flex: 1; }
.wksp-skel-panel { flex: 1; background: var(--shunya-surface-2, #1a1a26); border: 1px solid var(--shunya-surface-1, #22222e); border-radius: var(--shunya-radius-md); padding: var(--shunya-spacing-md); display: flex; flex-direction: column; gap: var(--shunya-spacing-sm); }
.wksp-error { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--shunya-spacing-md); padding: var(--shunya-spacing-xl); flex: 1; text-align: center; }
.wksp-error-icon { font-size: 2rem; }
.wksp-error-title { font-size: var(--shunya-font-size-lg); font-weight: 500; color: var(--shunya-text, #e0e0e0); }
.wksp-error-message { font-size: var(--shunya-font-size-sm); color: var(--shunya-text-secondary, #888); max-width: 400px; }
.wksp-error-retry { padding: var(--shunya-spacing-sm) var(--shunya-spacing-lg); background: var(--shunya-color-primary, #555); color: #fff; border: none; border-radius: var(--shunya-radius-sm); cursor: pointer; }
.wksp-panel-error { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background: var(--shunya-surface-2, #1a1a26); border: 1px solid rgba(255,85,85,0.3); border-radius: var(--shunya-radius-md); padding: var(--shunya-spacing-md); }
.wksp-panel-error-label { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary, #888); font-weight: 600; text-transform: uppercase; }
.wksp-panel-error-msg { font-size: var(--shunya-font-size-sm); color: #f88; margin-top: 4px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  document.head.appendChild(el);
}