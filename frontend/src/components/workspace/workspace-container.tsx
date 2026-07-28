import { useRef, useEffect, useState } from 'react';
import { useActiveWorkspace } from '../../hooks/workspace-hooks';
import { useRuntimeHealth } from '../../hooks/runtime-hooks';
import { CompositionEngine } from '../../runtimes/composition/engine';
import { ModuleRegistry } from '../../runtimes/module-registry';
import { AiCopilot } from '../copilot/ai-copilot';
import { Panel } from '../executive/index';

export function WorkspaceContainer() {
  const active = useActiveWorkspace();
  const health = useRuntimeHealth();
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1200);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  if (health.total > 0 && health.ready < health.total) {
    return (
      <div className="wksp-boot" role="status" aria-label="Platform starting">
        <div className="wksp-boot-spinner" />
        <div className="wksp-boot-text">Initialising… ({health.ready}/{health.total})</div>
        {health.failed > 0 && <div className="wksp-boot-error">{health.failed} runtime(s) failed</div>}
      </div>
    );
  }

  if (!ModuleRegistry.hasModules && !active) {
    return (
      <div className="wksp-empty" role="status">
        <div className="wksp-empty-zero">शून्य</div>
        <h2 className="wksp-empty-title">Welcome to SHUNYA</h2>
        <p className="wksp-empty-desc">One Operating System for Your Business.</p>
        <div className="wksp-empty-actions">
          <button className="wksp-empty-btn" onClick={() => {
            window.open('/api/v1/founder/seed', '_blank')?.focus();
          }}>
            Load Demo Data
          </button>
          <button className="wksp-empty-btn wksp-empty-btn-secondary" onClick={() => {
            window.open('https://shunyaos.com', '_blank')?.focus();
          }}>
            Learn More
          </button>
        </div>
        <div className="wksp-empty-hint">Press <kbd>⌘K</kbd> to search · <kbd>⌘1</kbd>–<kbd>⌘9</kbd> workspaces</div>
      </div>
    );
  }

  const workspaceType = active?.layout ?? 'executive';
  const composed = CompositionEngine.compose(workspaceType, width, {});

  return (
    <div className={active ? 'wksp-with-copilot' : ''} ref={ref}>
      <div className="wksp-area">
        {composed.panels.map(p => (
          <Panel key={p.id} id={p.id} name={p.label ?? p.componentId} loading={p.loading} error={p.error}>
            {p.Component && <p.Component state={p.props} loading={p.loading} error={p.error} />}
          </Panel>
        ))}
      </div>
      {active && (
        <AiCopilot context={{
          workspaceType: active.layout,
          objectId: active.identity.objectId,
          objectType: active.identity.objectType,
        }} />
      )}
    </div>
  );
}

const styles = `
.wksp-area { display: flex; gap: var(--shunya-spacing-md); padding: var(--shunya-spacing-md); flex: 1; overflow: auto; align-items: stretch; container-type: inline-size; }
.wksp-with-copilot { display: flex; height: 100%; }
.wksp-with-copilot > .wksp-area { overflow-y: auto; }
.wksp-boot { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: var(--shunya-bg); gap: var(--shunya-spacing-md); }
.wksp-boot-spinner { width: 32px; height: 32px; border: 3px solid var(--shunya-color-primary); border-top-color: var(--shunya-color-secondary); border-radius: 50%; animation: wksp-spin 0.8s linear infinite; }
@keyframes wksp-spin { to { transform: rotate(360deg); } }
.wksp-boot-text { font-size: var(--shunya-font-size-lg); color: var(--shunya-text-secondary); }
.wksp-boot-error { font-size: var(--shunya-font-size-sm); color: var(--shunya-color-danger); }
.wksp-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--shunya-text-secondary); gap: var(--shunya-spacing-md); text-align: center; padding: var(--shunya-spacing-3xl); }
.wksp-empty-zero { font-size: clamp(3rem, 8vw, 5rem); color: #fff; font-weight: 300; opacity: 0.8; }
.wksp-empty-title { font-size: var(--shunya-font-size-xl); color: var(--shunya-text); margin: 0; }
.wksp-empty-desc { font-size: var(--shunya-font-size-md); color: var(--shunya-text-secondary); max-width: 400px; }
.wksp-empty-actions { display: flex; gap: var(--shunya-spacing-sm); margin-top: var(--shunya-spacing-sm); }
.wksp-empty-btn { padding: var(--shunya-spacing-sm) var(--shunya-spacing-lg); border-radius: var(--shunya-radius-sm); font-size: var(--shunya-font-size-sm); cursor: pointer; border: none; background: var(--shunya-color-primary, #555); color: #fff; }
.wksp-empty-btn-secondary { background: transparent; border: 1px solid var(--shunya-color-primary, #444); color: var(--shunya-text-secondary); }
.wksp-empty-btn:hover { opacity: 0.85; }
.wksp-empty-hint { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); padding: var(--shunya-spacing-sm); margin-top: var(--shunya-spacing-lg); }
.wksp-empty-hint kbd { padding: 1px 4px; border: 1px solid var(--shunya-color-primary); border-radius: 3px; font-family: monospace; }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  document.head.appendChild(el);
}