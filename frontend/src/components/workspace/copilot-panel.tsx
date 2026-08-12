/**
 * FDA18 — AI Contextual Copilot Panel
 *
 * Continuously available SHUNYA intelligence in the workspace.
 * Understands the current object and answers contextual questions.
 */
import { useState, type FC } from 'react';
import { copilotAsk } from '../../api/workspace-api';

interface Props {
  objectType: string;
  objectId: string;
  relationshipId?: number;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  confidence?: string;
  intent?: string;
}

const quickQuestions = [
  'What is happening?',
  'What was promised?',
  'What is overdue?',
  'What should I do next?',
];

export const CopilotPanel: FC<Props> = ({ objectType, objectId, relationshipId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const ask = async (q: string) => {
    if (!q.trim() || loading) return;
    const userMsg: Message = { role: 'user', content: q };
    setMessages((prev) => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const resp = await copilotAsk(q, objectType, objectId, relationshipId);
      if (resp.success && resp.data) {
        const d = resp.data;
        const assistantMsg: Message = {
          role: 'assistant',
          content: d.answer || 'No answer available.',
          confidence: d.confidence,
          intent: d.intent,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: resp.error || 'Cannot answer right now.' }]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Network error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="wksp-copilot">
      <div className="wksp-copilot-header">
        <span className="wksp-copilot-title">Ask SHUNYA</span>
        <span className="wksp-copilot-subtitle">Contextual intelligence</span>
      </div>

      <div className="wksp-copilot-messages">
        {messages.length === 0 && (
          <div className="wksp-copilot-greeting">
            <p>Ask me anything about this object. For example:</p>
            <div className="wksp-copilot-quick-questions">
              {quickQuestions.map((q) => (
                <button key={q} className="wksp-copilot-quick-btn" onClick={() => ask(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`wksp-copilot-msg wksp-copilot-msg-${m.role}`}>
            <div className="wksp-copilot-msg-label">{m.role === 'user' ? 'You' : 'SHUNYA'}</div>
            <div className="wksp-copilot-msg-content">{m.content}</div>
            {m.confidence && (
              <div className="wksp-copilot-msg-meta">
                Confidence: {m.confidence} | Intent: {m.intent || '—'}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="wksp-copilot-msg wksp-copilot-msg-assistant">
            <div className="wksp-copilot-msg-label">SHUNYA</div>
            <div className="wksp-copilot-msg-content wksp-copilot-thinking">Thinking…</div>
          </div>
        )}
      </div>

      <div className="wksp-copilot-input">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask(query)}
          placeholder="Ask SHUNYA…"
          disabled={loading}
          className="wksp-copilot-input-field"
        />
        <button
          className="wksp-copilot-send"
          onClick={() => ask(query)}
          disabled={loading || !query.trim()}
        >→</button>
      </div>

      <style>{`
.wksp-copilot { display: flex; flex-direction: column; background: var(--shunya-surface-2, #1a1a26); border: 1px solid var(--shunya-surface-1, #22222e); border-radius: var(--shunya-radius-md, 8px); height: 100%; overflow: hidden; }
.wksp-copilot-header { padding: 12px 14px; border-bottom: 1px solid var(--shunya-surface-1, #22222e); display: flex; flex-direction: column; gap: 2px; }
.wksp-copilot-title { font-size: 13px; font-weight: 600; color: var(--shunya-text, #e0e0e0); }
.wksp-copilot-subtitle { font-size: 11px; color: var(--shunya-text-secondary, #888); }
.wksp-copilot-messages { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
.wksp-copilot-greeting { font-size: 13px; color: var(--shunya-text-secondary, #888); }
.wksp-copilot-quick-questions { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
.wksp-copilot-quick-btn { text-align: left; padding: 6px 10px; background: var(--shunya-surface-3, #2a2a3a); border: 1px solid var(--shunya-surface-1, #222); border-radius: 6px; color: var(--shunya-text, #ccc); cursor: pointer; font-size: 12px; transition: background 0.15s; }
.wksp-copilot-quick-btn:hover { background: var(--shunya-surface-4, #333350); }
.wksp-copilot-msg { display: flex; flex-direction: column; gap: 4px; }
.wksp-copilot-msg-label { font-size: 10px; font-weight: 600; color: var(--shunya-text-secondary, #888); text-transform: uppercase; }
.wksp-copilot-msg-content { font-size: 13px; line-height: 1.5; color: var(--shunya-text, #e0e0e0); white-space: pre-wrap; }
.wksp-copilot-msg-meta { font-size: 10px; color: var(--shunya-text-secondary, #666); margin-top: 2px; }
.wksp-copilot-thinking { color: var(--shunya-text-secondary, #888); font-style: italic; }
.wksp-copilot-input { display: flex; border-top: 1px solid var(--shunya-surface-1, #22222e); padding: 8px; gap: 6px; }
.wksp-copilot-input-field { flex: 1; padding: 8px 10px; background: var(--shunya-surface-3, #2a2a3a); border: 1px solid var(--shunya-surface-1, #222); border-radius: 6px; color: var(--shunya-text, #e0e0e0); font-size: 13px; outline: none; }
.wksp-copilot-input-field:focus { border-color: var(--shunya-color-primary, #555); }
.wksp-copilot-send { padding: 8px 14px; background: var(--shunya-color-primary, #555); border: none; border-radius: 6px; color: #fff; cursor: pointer; font-size: 16px; transition: background 0.15s; }
.wksp-copilot-send:disabled { opacity: 0.4; cursor: default; }
.wksp-copilot-send:hover:not(:disabled) { background: var(--shunya-color-primary-hover, #777); }
      `}</style>
    </div>
  );
};