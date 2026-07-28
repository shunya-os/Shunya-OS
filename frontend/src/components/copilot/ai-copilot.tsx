/**
 * AI Copilot — Understands active context automatically.
 *
 * No repeated prompting. Knows current workspace, object, conversation,
 * commitments, and timeline from the runtime state.
 */

import { useState, useCallback, useEffect } from 'react';
import { InsightCard } from '../executive/index';
import { ModuleRegistry } from '../../runtimes/module-registry';

interface AiCopilotProps {
  context: {
    workspaceType: string;
    objectId?: string;
    objectType?: string;
    conversationId?: string;
    commitmentId?: string;
  };
}

export function AiCopilot({ context }: AiCopilotProps) {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [proactiveInsights, setProactiveInsights] = useState<string[]>([]);

  // Load proactive insights on mount
  useEffect(() => {
    ModuleRegistry.askAll('summarize current state').then(a => {
      if (a) setProactiveInsights(a.split('\n').filter(Boolean));
    }).catch(() => {});
  }, []);

  const ask = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setAnswer(null);
    try {
      const answer = await ModuleRegistry.askAll(query);
      if (answer) {
        setAnswer(answer);
      } else {
        setAnswer(`I'm aware of your context. Ask me about your business.`);
      }
    } catch {
      setAnswer('AI analysis is temporarily unavailable. Try again in a moment.');
    } finally {
      setLoading(false);
    }
  }, [query, context]);

  const contextSummary = [
    context.workspaceType ? `Workspace: ${context.workspaceType}` : '',
    context.objectType ? `Object: ${context.objectType} ${context.objectId ?? ''}` : '',
    context.conversationId ? `Conversation: ${context.conversationId.slice(0, 8)}…` : '',
    context.commitmentId ? `Commitment: ${context.commitmentId.slice(0, 8)}…` : '',
  ].filter(Boolean).join(' · ');

  return (
    <div className="ai-copilot" role="complementary" aria-label="AI assistant">
      <div className="ai-copilot-header">
        <span className="ai-copilot-label">AI Copilot</span>
        <span className="ai-copilot-context" title={contextSummary}>{contextSummary || 'No active context'}</span>
      </div>

      <div className="ai-copilot-body" role="log" aria-live="polite">
        {proactiveInsights.length > 0 && !answer && (
          <div className="ai-copilot-insights">
            {proactiveInsights.map((insight, i) => (
              <div key={i} className="ai-copilot-insight">{insight}</div>
            ))}
          </div>
        )}
        {answer ? (
          <div className="ai-copilot-answer">{answer}</div>
        ) : !proactiveInsights.length ? (
          <InsightCard state={{
            title: 'Context-Aware Assistant',
            body: `I'm aware of your current context. Ask me anything about your business.`,
            confidence: 'high', type: 'summary',
          }} />
        ) : null}
      </div>

      <div className="ai-copilot-input-row">
        <input
          className="ai-copilot-input"
          placeholder="Ask about your business…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !loading) ask(); }}
        />
        <button className="ai-copilot-send" onClick={ask} disabled={loading || !query.trim()}>
          {loading ? '…' : '→'}
        </button>
      </div>
    </div>
  );
}

const styles = `
.ai-copilot { display: flex; flex-direction: column; height: 100%; background: var(--shunya-bg); border-left: 1px solid var(--shunya-surface-1); max-width: 320px; }
.ai-copilot-header { padding: var(--shunya-spacing-sm) var(--shunya-spacing-md); border-bottom: 1px solid var(--shunya-surface-1); display: flex; flex-direction: column; gap: 2px; }
.ai-copilot-label { font-size: var(--shunya-font-size-xs); font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--shunya-color-ai); }
.ai-copilot-context { font-size: 10px; color: var(--shunya-text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ai-copilot-body { flex: 1; overflow-y: auto; padding: var(--shunya-spacing-md); }
.ai-copilot-answer { font-size: var(--shunya-font-size-sm); line-height: 1.6; }
.ai-copilot-input-row { display: flex; gap: var(--shunya-spacing-sm); padding: var(--shunya-spacing-sm) var(--shunya-spacing-md); border-top: 1px solid var(--shunya-surface-1); }
.ai-copilot-input { flex: 1; padding: var(--shunya-spacing-sm) var(--shunya-spacing-md); border: 1px solid var(--shunya-surface-2); border-radius: var(--shunya-radius-sm); font-size: var(--shunya-font-size-sm); background: var(--shunya-surface-1); color: var(--shunya-text); outline: none; }
.ai-copilot-input:focus { border-color: var(--shunya-color-secondary); }
.ai-copilot-send { width: 32px; height: 32px; border-radius: 50%; border: none; background: var(--shunya-color-primary); color: white; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.ai-copilot-send:disabled { opacity: 0.4; cursor: not-allowed; }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  document.head.appendChild(el);
}