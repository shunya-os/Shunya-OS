/** Workspace Shell — Three-zone layout. */

interface ShellContext {
  workspaceType: string;
  objectId?: string;
  objectType?: string;
}

interface Props {
  context: ShellContext;
  children: React.ReactNode;
}

export function WorkspaceShell({ context, children }: Props) {
  return (
    <div className="wksp-shell" data-workspace-type={context.workspaceType}>
      <div className="wksp-content">
        {children}
      </div>
      <style>{`
.wksp-shell { display: flex; flex-direction: column; flex: 1; overflow: hidden; background: var(--shunya-bg, #0a0a0f); }
.wksp-content { flex: 1; overflow: auto; display: flex; flex-direction: column; }
      `}</style>
    </div>
  );
}