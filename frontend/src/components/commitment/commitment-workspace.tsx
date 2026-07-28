/**
 * Commitment Workspace — Execution tracking with full UI states.
 * Answers: What's promised? Blocked? Overdue? Next? Evidence? Confidence?
 */

import { Panel, ProgressBar, ConfidenceMeter, BlockerList, NextBestAction } from '../executive/index';

interface CommitmentWorkspaceProps {
  commitment?: {
    id: string; title: string; objective: string; status: string;
    progress: number; confidence: number; owner: string;
    risks: { description: string; severity: string }[];
    evidenceCount: number; relatedObjects: { id: string; name: string; type: string }[];
    deadline?: number;
  };
  loading?: boolean; error?: string;
}

function LoadingState() {
  return (
    <div className="cmt-workspace" aria-busy="true">
      <div className="cmt-primary">
        <div className="sh-skel-line w-40" style={{ margin: 16 }} />
        <div className="sh-skel-line w-32" style={{ margin: '8px 16px' }} />
        <div className="sh-skel-line w-full" style={{ margin: 16, height: 80 }} />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="cmt-empty-state" role="status">
      <p>No commitment selected.</p>
      <p className="cmt-empty-sub">Create a commitment to track business execution.</p>
    </div>
  );
}

export function CommitmentWorkspace({ commitment, loading, error }: CommitmentWorkspaceProps) {
  if (error) return <div className="cmt-error" role="alert">{error}</div>;
  if (loading) return <LoadingState />;
  if (!commitment) return <EmptyState />;

  return (
    <div className="cmt-workspace">
      <div className="cmt-primary">
        <div className="cmt-header">
          <h2 className="cmt-title">{commitment.title}</h2>
          {commitment.objective && <div className="cmt-objective">{commitment.objective}</div>}
          <div className="cmt-meta">
            <span>Owner: {commitment.owner || 'Unassigned'}</span>
            {commitment.deadline && <span> · Due: {new Date(commitment.deadline).toLocaleDateString()}</span>}
            <span> · Status: {commitment.status}</span>
          </div>
        </div>

        <div className="cmt-section">
          <div className="cmt-section-title">Related Objects</div>
          {commitment.relatedObjects?.length > 0
            ? commitment.relatedObjects.map((o, i) => (
                <div key={i} className="cmt-related-obj">
                  <span className="cmt-related-type">{o.type}</span>
                  <span className="cmt-related-name">{o.name}</span>
                </div>
              ))
            : <div className="cmt-empty">No related objects</div>}
        </div>

        <div className="cmt-section">
          <div className="cmt-section-title">Next Best Action</div>
          <NextBestAction state={{
            action: (commitment.progress ?? 0) < 1 ? 'Move commitment forward' : 'Verify completion',
            reason: `Progress is ${Math.round((commitment.progress ?? 0) * 100)}% with ${commitment.evidenceCount ?? 0} evidence items.`,
            confidence: (commitment.confidence ?? 0) >= 0.7 ? 'high' : (commitment.confidence ?? 0) >= 0.4 ? 'medium' : 'low',
          }} />
        </div>

        <div className="cmt-section">
          <div className="cmt-section-title">Blockers</div>
          <BlockerList state={{ blockers: (commitment.risks ?? []).map(r => ({ ...r, detected: Date.now() })) }} />
        </div>
      </div>

      <div className="cmt-sidebar" role="complementary" aria-label="Commitment metrics">
        <Panel id="progress" name="Progress">
          <ProgressBar state={{ value: commitment.progress ?? 0, label: 'Commitment progress' }} />
        </Panel>
        <Panel id="confidence" name="Confidence">
          <ConfidenceMeter state={{
            score: commitment.confidence ?? 0,
            factors: [`${Math.round((commitment.progress ?? 0) * 100)}% progress`, `${commitment.evidenceCount ?? 0} evidence items`],
          }} />
        </Panel>
      </div>
    </div>
  );
}

const styles = `
.cmt-workspace { display: flex; height: 100%; gap: var(--shunya-spacing-md); }
.cmt-primary { flex: 1; display: flex; flex-direction: column; gap: var(--shunya-spacing-md); overflow-y: auto; padding: var(--shunya-spacing-md); }
.cmt-sidebar { width: 260px; display: flex; flex-direction: column; gap: var(--shunya-spacing-md); overflow-y: auto; }
.cmt-title { font-size: var(--shunya-font-size-lg); font-weight: 500; margin: 0; }
.cmt-objective { font-size: var(--shunya-font-size-sm); color: var(--shunya-text-secondary); margin-top: 4px; }
.cmt-meta { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); margin-top: 8px; display: flex; gap: 4px; flex-wrap: wrap; }
.cmt-section-title { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: var(--shunya-spacing-sm); }
.cmt-related-obj { display: flex; gap: var(--shunya-spacing-sm); padding: var(--shunya-spacing-xs) 0; align-items: center; }
.cmt-related-type { font-size: 10px; text-transform: uppercase; background: var(--shunya-surface-1); padding: 1px 4px; border-radius: 2px; }
.cmt-related-name { font-size: var(--shunya-font-size-sm); }
.cmt-empty { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary); font-style: italic; }
.cmt-empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--shunya-text-secondary); gap: 8px; }
.cmt-empty-sub { font-size: var(--shunya-font-size-sm); }
.cmt-error { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--shunya-color-danger); }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  document.head.appendChild(el);
}