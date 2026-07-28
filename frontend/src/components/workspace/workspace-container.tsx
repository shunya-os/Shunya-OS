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
 *   active  → composed panels
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
import { HomeWorkspace } from './home-workspace';
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
  const [objectData, setObjectData] = useState<Record<string, unknown> | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

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

  // Fetch object data when an object workspace becomes active
  // Dependencies include active identity id so effect re-fires on workspace
  // activation (tab click) even when objectId/type are unchanged from hydration
  useEffect(() => {
    if (!active || active.identity.type !== 'object' || !active.identity.objectId) {
      setObjectData(null);
      setLoadError(null);
      setIsLoading(false);
      return;
    }
    let cancelled = false;
    const oid = active.identity.objectId;
    setIsLoading(true);
    setLoadError(null);

    fetch(`/api/v1/founder/objects/${oid}`, { credentials: 'include' })
      .then(r => {
        if (!r.ok) {
          if (r.status === 404) throw new Error(`Object not found or has been deleted`);
          if (r.status === 401 || r.status === 403) throw new Error(`You don't have permission to view this object`);
          throw new Error(`Server error (${r.status})`);
        }
        return r.json();
      })
      .then(d => {
        if (!cancelled) {
          if (!d.data) throw new Error('Object data is empty');
          setObjectData(d.data ?? null);
          setLoadError(null);
          setIsLoading(false);
          // Emit ObjectLoaded to transition workspace from loading → hydrating
          bus.emit({ type: 'ObjectLoaded', objectType: active.identity.objectType!, objectId: oid, data: d.data });
          // Emit TimelineLoaded to transition from hydrating → active
          bus.emit({ type: 'TimelineLoaded', objectType: active.identity.objectType!, objectId: oid, events: [] });
        }
      })
      .catch(err => {
        if (!cancelled) {
          setLoadError(err.message);
          setObjectData(null);
          setIsLoading(false);
          useWorkspaceStore.getState().markError(active.identity.id, err.message);
        }
      });
    return () => { cancelled = true; };
  }, [active?.identity.id, active?.identity.objectId, active?.identity.type]);

  const shellContext = active ? {
    workspaceType: active.layout,
    objectId: active.identity.objectId,
    objectType: active.identity.objectType,
  } : { workspaceType: 'home' };

  const runtimeStates: Record<string, Record<string, unknown>> = objectData
    ? { object: objectData as Record<string, unknown> }
    : {};

  function renderContent() {
    // While booting, render the Home workspace with skeleton loading
    if (health.total > 0 && !runtimesReady) {
      return <HomeWorkspace loading={true} />;
    }

    // Empty state — no modules, no active workspace
    if (!ModuleRegistry.hasModules && !active) {
      return <HomeWorkspace />;
    }

    // No active workspace — show Home workspace
    if (!active) {
      return <HomeWorkspace />;
    }

    // Error state (from local fetch or workspace status)
    if (loadError || active.status === 'error') {
      return (
        <WorkspaceErrorState
          error={loadError ?? active.error ?? 'Unknown error'}
          onRetry={() => {
            setLoadError(null);
            setObjectData(null);
            setIsLoading(true);
          }}
        />
      );
    }

    // Loading state (local fetch or workspace still initializing)
    if (isLoading && !objectData) {
      return <WorkspaceLoadingState />;
    }

    // Active workspace — compose panels (even if workspace status is still transitioning)
    // The local objectData is the source of truth for rendering
    if (objectData) {
      const workspaceType = active.layout ?? 'home';
      let composed;
      try {
        composed = CompositionEngine.compose(workspaceType, width, runtimeStates);
      } catch {
        return <HomeWorkspace />;
      }

      return (
        <div className="wksp-panels" ref={ref}>
          {composed.panels.map(p => {
            // Error state for individual panels
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

    // Fallback: no object data, no active workspace
    return <HomeWorkspace />;
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