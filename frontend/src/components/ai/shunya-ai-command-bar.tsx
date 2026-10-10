/**
 * ShunyaAICommandBar — Reusable AI command bar for EVERY surface.
 *
 * G3 Phase 6.5: A consistent command bar added to every main surface
 * (Home, Relationships, Documents, Commercial, Content Studio) so
 * users can ask SHUNYA from anywhere without switching context.
 *
 * G3 Phase 6.6: Cross-surface context continuity — the active context
 * (workspace, object_type, object_id) is passed to the AI chat so
 * the conversation remains continuous across navigation.
 *
 * Uses the canonical POST /api/v1/ai/chat endpoint (IntelligenceRuntime's ask).
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import { aiChat, type AIChatMessage } from '../../api/ai-chat';

// ── Types ─────────────────────────────────────────────────────

export interface SurfaceContext {
  surface: string;
  objectType?: string;
  objectId?: string;
  label?: string;
}

interface ChatEntry {
  role: 'user' | 'assistant';
  content: string;
}

interface Props {
  /** Context describing which surface the command bar is embedded in. */
  surfaceContext?: SurfaceContext;
  /** Placeholder text for the input. */
  placeholder?: string;
  /** If true, expands the command bar on mount. */
  expanded?: boolean;
  /** Callback when the user asks a question. */
  onAsk?: (query: string, response: string) => void;
  /** Optional extra system prompt directives. */
  systemPrompt?: string;
}

// ── Main Component ────────────────────────────────────────────

export function ShunyaAICommandBar({
  surfaceContext,
  placeholder = 'Ask SHUNYA…',
  expanded: initialExpanded = false,
  onAsk,
  systemPrompt,
}: Props) {
  const [expanded, setExpanded] = useState(initialExpanded);
  const [input, setInput] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatEntry[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Keep a stable context key across renders
  const contextKey = surfaceContext
    ? `${surfaceContext.surface}:${surfaceContext.objectType || ''}:${surfaceContext.objectId || ''}`
    : 'default';

  // Track previous context for continuity notifications
  const prevContextRef = useRef(contextKey);

  useEffect(() => {
    if (expanded && inputRef.current) inputRef.current.focus();
  }, [expanded]);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Context change notification
  useEffect(() => {
    if (prevContextRef.current !== contextKey && chatHistory.length > 0) {
      // Append a system message noting the context change for continuity
      setChatHistory(prev => [
        ...prev,
        {
          role: 'assistant',
          content: surfaceContext
            ? `[Now viewing: ${surfaceContext.label || surfaceContext.surface}${surfaceContext.objectType ? ` · ${surfaceContext.objectType}` : ''}]`
            : '[Surface changed]',
        },
      ]);
    }
    prevContextRef.current = contextKey;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contextKey]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput('');
    setSending(true);
    setError(null);
    setChatHistory(prev => [...prev, { role: 'user', content: text }]);

    try {
      // Build messages with context awareness
      const messages: AIChatMessage[] = [];

      // System prompt with surface context
      let systemText = 'You are SHUNYA, the operating intelligence for this organization.';
      if (surfaceContext) {
        systemText += ` The user is currently on the ${surfaceContext.label || surfaceContext.surface} surface.`;
        if (surfaceContext.objectType) {
          systemText += ` Active object type: ${surfaceContext.objectType}.`;
        }
        if (surfaceContext.objectId) {
          systemText += ` Active object ID: ${surfaceContext.objectId}.`;
        }
      }
      if (systemPrompt) {
        systemText += ` ${systemPrompt}`;
      }
      messages.push({ role: 'system', content: systemText });

      // Include chat history for continuity
      const recentHistory = chatHistory.slice(-6); // Last 3 turns
      for (const entry of recentHistory) {
        messages.push({ role: entry.role, content: entry.content });
      }

      messages.push({ role: 'user', content: text });

      const resp = await aiChat(messages, { max_tokens: 512, webSearch: true });
      const answer = resp.content || '(empty response)';

      setChatHistory(prev => [...prev, { role: 'assistant', content: answer }]);
      onAsk?.(text, answer);
    } catch (err: any) {
      const msg = err?.message || 'Network error';
      setError(msg);
      setChatHistory(prev => [...prev, { role: 'assistant', content: `Error: ${msg}` }]);
    } finally {
      setSending(false);
    }
  }, [input, sending, surfaceContext, systemPrompt, chatHistory, onAsk]);

  return (
    <div className={`sacb-bar ${expanded ? 'sacb-expanded' : ''}`}>
      {!expanded ? (
        <button
          className="sacb-trigger"
          onClick={() => setExpanded(true)}
          aria-label="Ask SHUNYA"
        >
          <span className="sacb-trigger-icon">◈</span>
          <span className="sacb-trigger-text">{surfaceContext?.label || 'Ask SHUNYA'}</span>
          <span className="sacb-trigger-hint">Ctrl+Shift+A</span>
        </button>
      ) : (
        <div className="sacb-panel">
          {/* Header */}
          <div className="sacb-header">
            <span className="sacb-header-icon">◈</span>
            <span className="sacb-header-label">
              {surfaceContext?.label
                ? `Ask SHUNYA · ${surfaceContext.label}`
                : 'Ask SHUNYA'}
            </span>
            <button
              className="sacb-close"
              onClick={() => setExpanded(false)}
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          {/* Context indicator */}
          {surfaceContext && (
            <div className="sacb-context">
              <span className="sacb-context-surface">{surfaceContext.surface}</span>
              {surfaceContext.objectType && (
                <span className="sacb-context-type">{surfaceContext.objectType}</span>
              )}
            </div>
          )}

          {/* Chat history */}
          {chatHistory.length > 0 && (
            <div className="sacb-messages">
              {chatHistory.map((entry, i) => (
                <div key={i} className={`sacb-msg sacb-msg-${entry.role}`}>
                  <span className="sacb-msg-role">
                    {entry.role === 'user' ? 'You' : 'SHUNYA'}
                  </span>
                  <p className="sacb-msg-content">{entry.content}</p>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="sacb-error" role="alert">
              {error}
            </div>
          )}

          {/* Input */}
          <div className="sacb-input-row">
            <input
              ref={inputRef}
              className="sacb-input"
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') handleSend();
                if (e.key === 'Escape') { setExpanded(false); setInput(''); }
              }}
              placeholder={placeholder}
              disabled={sending}
              spellCheck={false}
              autoComplete="off"
            />
            <button
              className="sacb-send"
              onClick={handleSend}
              disabled={!input.trim() || sending}
              aria-label="Send"
            >
              {sending ? '…' : '→'}
            </button>
          </div>
        </div>
      )}

      <style>{`
.sacb-bar {
  width: 100%;
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
}
.sacb-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: var(--shunya-surface, #FFFFFF);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-sm, 10px);
  cursor: pointer;
  transition: all var(--shunya-duration-fast, 200ms) ease;
  font-family: inherit;
}
.sacb-trigger:hover {
  border-color: rgba(108,74,226,0.3);
  background: rgba(108,74,226,0.02);
}
.sacb-trigger-icon {
  font-size: 16px;
  color: #6C4AE2;
}
.sacb-trigger-text {
  flex: 1;
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  text-align: left;
}
.sacb-trigger-hint {
  font-size: 9px;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  background: var(--shunya-bg, #FBF8F5);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.sacb-panel {
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-sm, 10px);
  overflow: hidden;
  background: var(--shunya-surface, #FFFFFF);
}
.sacb-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.sacb-header-icon {
  font-size: 14px;
  color: #6C4AE2;
}
.sacb-header-label {
  flex: 1;
  font-size: var(--shunya-text-xs, 10px);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6C4AE2;
}
.sacb-close {
  background: none;
  border: none;
  font-size: 12px;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}
.sacb-context {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: var(--shunya-bg, #FBF8F5);
  border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.sacb-context-surface {
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6C4AE2;
  background: rgba(108,74,226,0.08);
  padding: 1px 6px;
  border-radius: 3px;
}
.sacb-context-type {
  font-size: 9px;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  background: var(--shunya-bg, #FBF8F5);
  padding: 1px 6px;
  border-radius: 3px;
}
.sacb-messages {
  max-height: 240px;
  overflow-y: auto;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sacb-msg {
  padding: 6px 10px;
  border-radius: 8px;
  max-width: 85%;
}
.sacb-msg-user {
  align-self: flex-end;
  background: rgba(108,74,226,0.08);
  border-bottom-right-radius: 2px;
}
.sacb-msg-assistant {
  align-self: flex-start;
  background: var(--shunya-bg, #FBF8F5);
  border-bottom-left-radius: 2px;
}
.sacb-msg-role {
  font-size: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  display: block;
  margin-bottom: 2px;
}
.sacb-msg-content {
  font-size: var(--shunya-text-sm, 12px);
  line-height: 1.5;
  color: var(--shunya-text, #1A1C1D);
  white-space: pre-wrap;
  word-break: break-word;
}
.sacb-error {
  padding: 6px 12px;
  font-size: var(--shunya-text-xs, 10px);
  color: #B91C1C;
  background: rgba(185,28,28,0.05);
  border-top: 1px solid rgba(185,28,28,0.1);
}
.sacb-input-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border-top: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.sacb-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: var(--shunya-text-sm, 12px);
  font-family: inherit;
  color: var(--shunya-text, #1A1C1D);
  background: transparent;
}
.sacb-input::placeholder {
  color: var(--shunya-text-faint, rgba(26,28,29,0.15));
}
.sacb-send {
  background: #6C4AE2;
  color: #FFFFFF;
  border: none;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 13px;
  cursor: pointer;
  transition: opacity var(--shunya-duration-fast, 200ms) ease;
  font-family: inherit;
  line-height: 1.4;
}
.sacb-send:disabled {
  opacity: 0.4;
  cursor: default;
}
.sacb-send:not(:disabled):hover {
  opacity: 0.85;
}
      `}</style>
    </div>
  );
}

// ── Hook: Ctrl+Shift+A to toggle the command bar ──────────────

export function useShunyaAICommandBar(
  containerRef: React.RefObject<HTMLElement | null>,
  onToggle?: (open: boolean) => void,
) {
  useEffect(() => {
    const handler = (e: Event) => {
      const ke = e as KeyboardEvent;
      if ((ke.metaKey || ke.ctrlKey) && ke.shiftKey && ke.key === 'a') {
        e.preventDefault();
        onToggle?.(true);
      }
    };
    const el = containerRef?.current || window;
    el.addEventListener('keydown', handler as EventListener);
    return () => el.removeEventListener('keydown', handler as EventListener);
  }, [containerRef, onToggle]);
}