/**
 * AI Resident Panel — Lives in Zone Right (Intelligence Pane).
 *
 * Presence Canon §3: Four presence modes.
 * AI Collaboration Canon §4: Three AI surfaces — Executive Summary,
 * AI Resident Panel, AI-Enhanced Content Sections.
 *
 * Panel shows:
 *   Ambient (default): Gold dot + "SHUNYA is present" — calm, quiet
 *   Attentive: Subtle glow + brief context awareness
 *   Suggestive: 1-3 actionable suggestions with confidence
 *   Conversational: Full conversation panel
 */

import { useState } from 'react';
import { ShunyaPresence } from '../ui/shunya-presence';

type PresenceMode = 'idle' | 'ambient' | 'active' | 'attention' | 'attentive' | 'processing' | 'success' | 'error' | 'recovery' | 'suggestive' | 'conversational';

interface Suggestion {
  id: string;
  text: string;
  confidence: number;
  sourceCount: number;
  onAct: () => void;
}

interface Props {
  initialMode?: PresenceMode;
  objectContext?: string;
  suggestions?: Suggestion[];
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

async function apiPost(path: string, body: Record<string, string>): Promise<{ success: boolean; data?: any; answer?: string; error?: string }> {
  try {
    const r = await fetch(path, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return await r.json();
  } catch {
    return { success: false, error: 'Network error' };
  }
}

export function AIResidentPanel({ initialMode = 'ambient', objectContext, suggestions = [] }: Props) {
  const [mode, setMode] = useState<PresenceMode>(initialMode);
  // A conversational surface must OPEN conversational. This previously defaulted
  // to false, so routing "Ask SHUNYA" here landed the human on a collapsed panel
  // with no input: the affordance still did not present an ask surface.
  const [expanded, setExpanded] = useState(initialMode === 'conversational');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  const handleChatSend = async () => {
    if (!chatInput.trim() || chatSending) return;
    const text = chatInput.trim();
    setChatInput('');
    setChatSending(true);
    setChatError(null);
    setChatMessages(prev => [...prev, { role: 'user', content: text }]);
    try {
      // Canonical company-first ask pipeline (tenant identity → company evidence
      // → internet where required → reasoning). There is no ambient endpoint;
      // this is the real one.
      const result = await apiPost('/api/v1/intelligence/ask', { question: text });
      const answer = result.data?.answer ?? result.answer;
      if (result.success && answer) {
        setChatMessages(prev => [...prev, { role: 'assistant', content: answer }]);
      } else {
        // Never fabricate an answer. Report the truthful failure and offer retry.
        setChatError(result.error || 'SHUNYA could not answer that. The intelligence service did not respond.');
      }
    } catch {
      setChatError('SHUNYA could not reach the intelligence service. Your message was not processed.');
    }
    setChatSending(false);
  };

  const retryLast = () => {
    const lastUser = [...chatMessages].reverse().find(m => m.role === 'user');
    if (!lastUser) return;
    setChatInput(lastUser.content);
    setChatError(null);
  };

  const handleActivate = () => {
    if (mode === 'idle' || mode === 'ambient') {
      setMode(suggestions.length > 0 ? 'attentive' : 'ambient');
    } else if (mode === 'active' || mode === 'attention') {
      setMode(suggestions.length > 0 ? 'attentive' : 'ambient');
    } else if (mode === 'attentive') { setMode('suggestive'); setExpanded(true); }
    else if (mode === 'suggestive') { setMode('conversational'); setExpanded(true); }
    else { setMode('ambient'); }
  };

  return (
    <div className="sh-ai-resident">
      {/* Header */}
      <div className="sh-ai-header">
        <ShunyaPresence mode={mode} suggestionCount={suggestions.length} onActivate={handleActivate} />
        <span className="sh-ai-label">SHUNYA</span>
        <button
          className="sh-ai-toggle"
          onClick={() => setExpanded(!expanded)}
          aria-label={expanded ? 'Collapse' : 'Expand'}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
            style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
            <polyline points="4 5 7 8 10 5" />
          </svg>
        </button>
      </div>

      {/* Context Awareness (Attentive/Suggestive/Conversational) */}
      {mode !== 'ambient' && objectContext && (
        <div className="sh-ai-context">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"
            stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="7" cy="7" r="6" />
            <line x1="7" y1="7" x2="7" y2="10" />
            <circle cx="7" cy="4.5" r="0.5" fill="currentColor" stroke="none" />
          </svg>
          <span>{objectContext}</span>
        </div>
      )}

      {/* Suggestions (Suggestive mode) */}
      {expanded && mode === 'suggestive' && suggestions.length > 0 && (
        <div className="sh-ai-suggestions">
          {suggestions.map(s => (
            <div key={s.id} className="sh-ai-suggestion">
              <div className="sh-ai-sugg-text">{s.text}</div>
              <div className="sh-ai-sugg-meta">
                <span className="sh-ai-sugg-conf">
                  Confidence: {Math.round(s.confidence * 100)}%
                </span>
                <span className="sh-ai-sugg-source">
                  Based on {s.sourceCount} source{s.sourceCount !== 1 ? 's' : ''}
                </span>
              </div>
              <button className="sh-ai-sugg-act" onClick={s.onAct}>Apply</button>
            </div>
          ))}
        </div>
      )}

      {/* Conversation (Conversational mode) */}
      {expanded && mode === 'conversational' && (
        <div className="sh-ai-conversation">
          {chatMessages.length === 0 && !chatError && (
            <p className="sh-ai-chat-empty">
              Ask SHUNYA about your organization. Answers come from your company
              data first; the internet is used only when your data cannot answer.
            </p>
          )}
          {chatError && (
            <div className="sh-ai-chat-error" role="alert">
              <p>{chatError}</p>
              <button className="sh-ai-sugg-act" onClick={retryLast}>Try again</button>
            </div>
          )}
          <div className="sh-ai-chat-messages" id="sh-ai-msg-list">
            {chatMessages.map((m, i) => (
              <div key={i} className={`sh-ai-chat-msg sh-ai-chat-msg-${m.role}`}>
                {m.content}
              </div>
            ))}
            {chatSending && <div className="sh-ai-chat-typing">Request in progress…</div>}
          </div>
          <div className="sh-ai-chat-input-row">
            <input
              type="text"
              placeholder="Ask anything…"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && chatInput.trim() && !chatSending) handleChatSend();
              }}
              disabled={chatSending}
            />
            <button
              className="sh-ai-chat-send"
              onClick={handleChatSend}
              disabled={!chatInput.trim() || chatSending}
            >
              {chatSending ? '…' : '→'}
            </button>
          </div>
        </div>
      )}

      {/* Collapsed idle state (ambient/idle, not expanded) */}
      {!expanded && (mode === 'ambient' || mode === 'idle') && (
        <div className="sh-ai-idle">
          <p>{mode === 'idle' ? 'Everything is calm.' : 'I\'m here when you need me.'}</p>
        </div>
      )}

      <style>{`
.sh-ai-resident {
  display: flex; flex-direction: column;
}
.sh-ai-header {
  display: flex; align-items: center;
  gap: 8px; padding: 16px;
  border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.sh-ai-label {
  font-size: var(--shunya-text-sm, 12px);
  font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  font-family: var(--shunya-font-display, 'Playfair Display', serif);
  flex: 1;
}
.sh-ai-toggle {
  display: flex; align-items: center; justify-content: center;
  width: 24px; height: 24px;
  background: transparent;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 50%;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  cursor: pointer;
  transition: color var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-ai-toggle:hover {
  color: var(--shunya-text, #1A1C1D);
}
.sh-ai-context {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 12px 16px;
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  line-height: 1.5;
}
.sh-ai-context svg {
  margin-top: 2px; flex-shrink: 0;
  color: var(--shunya-gold, #A4865F);
}
.sh-ai-suggestions {
  display: flex; flex-direction: column;
  padding: 8px 16px;
  gap: 8px;
}
.sh-ai-suggestion {
  padding: 12px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-sm, 10px);
  background: var(--shunya-surface, #FFFFFF);
  display: flex; flex-direction: column; gap: 6px;
}
.sh-ai-sugg-text {
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text, #1A1C1D);
  line-height: 1.5;
}
.sh-ai-sugg-meta {
  display: flex; gap: 12px;
  font-size: var(--shunya-text-xs, 10px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
}
.sh-ai-sugg-act {
  align-self: flex-start;
  padding: 4px 12px;
  background: var(--shunya-text, #1A1C1D);
  color: var(--shunya-surface, #FFFFFF);
  border: none;
  border-radius: var(--shunya-radius-sm, 10px);
  font-size: var(--shunya-text-xs, 10px);
  font-weight: 500;
  cursor: pointer;
  transition: opacity var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-ai-sugg-act:hover { opacity: 0.85; }
.sh-ai-chat-empty {
  color: var(--shunya-color-text-secondary, #6b6b6b);
  font-size: 12px; line-height: 1.5; margin: 0 0 4px;
}
.sh-ai-chat-error {
  color: var(--shunya-color-danger, #b3261e);
  background: var(--shunya-color-danger-subtle, rgba(179, 38, 30, 0.06));
  border-radius: var(--shunya-radius-sm, 10px);
  padding: 8px 10px;
  font-size: 12px; line-height: 1.5;
}
.sh-ai-chat-error p { margin: 0 0 6px; }
.sh-ai-conversation {
  display: flex; flex-direction: column;
  padding: 12px 16px;
  gap: 8px;
}
.sh-ai-chat-messages {
  display: flex; flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
  padding: 8px 0;
}
.sh-ai-chat-msg {
  padding: 8px 12px;
  border-radius: 10px;
  font-size: var(--shunya-text-sm, 12px);
  line-height: 1.5;
  max-width: 85%;
}
.sh-ai-chat-msg-user {
  align-self: flex-end;
  background: var(--shunya-gold, #A4865F);
  color: #fff;
}
.sh-ai-chat-msg-assistant {
  align-self: flex-start;
  background: var(--shunya-surface, #FFFFFF);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  color: var(--shunya-text, #1A1C1D);
}
.sh-ai-chat-typing {
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  font-style: italic;
  padding: 4px 0;
}
.sh-ai-chat-input-row {
  display: flex;
  gap: 6px;
  align-items: center;
}
.sh-ai-chat-input-row input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-sm, 10px);
  background: var(--shunya-surface, #FFFFFF);
  color: var(--shunya-text, #1A1C1D);
  font-size: var(--shunya-text-sm, 12px);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  outline: none;
}
.sh-ai-chat-input-row input:focus {
  border-color: var(--shunya-border-focus, #A4865F);
}
.sh-ai-chat-input-row input::placeholder {
  color: var(--shunya-text-faint, rgba(26,28,29,0.15));
}
.sh-ai-chat-send {
  padding: 8px 14px;
  background: var(--shunya-text, #1A1C1D);
  color: var(--shunya-surface, #FFFFFF);
  border: none;
  border-radius: var(--shunya-radius-sm, 10px);
  font-size: var(--shunya-text-sm, 12px);
  cursor: pointer;
  transition: opacity var(--shunya-duration-fast, 200ms);
}
.sh-ai-chat-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.sh-ai-chat-send:hover:not(:disabled) {
  opacity: 0.85;
}
.sh-ai-idle {
  padding: 24px 16px;
  text-align: center;
}
.sh-ai-idle p {
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  font-style: italic;
  line-height: 1.5;
  margin: 0;
}
      `}</style>
    </div>
  );
}