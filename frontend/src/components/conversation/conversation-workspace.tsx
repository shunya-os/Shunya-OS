/**
 * Conversation Workspace — Business execution context with full UI states.
 * Wired to /api/v1/founder/ai/chat/:convId for real AI responses.
 */

import { useState, useCallback, type FC } from 'react';
import { Panel, Metric, InsightCard, StatusDot } from '../executive/index';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

interface ConversationWorkspaceProps {
  conversation?: {
    id: string;
    title: string;
    intent: string;
    status: string;
    participants: string[];
    objectIds: string[];
    commitmentIds: string[];
  };
  loading?: boolean;
  error?: string;
}

function LoadingState() {
  return (
    <div className="conv-workspace" aria-busy="true">
      <div className="conv-primary">
        <div className="sh-skel-line w-40" style={{ margin: 16 }} />
        <div className="sh-skel-line w-24" style={{ margin: '8px 16px' }} />
        <div className="sh-skel-line w-full" style={{ margin: 16, height: 200 }} />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="conv-empty-state" role="status">
      <p>No conversation selected.</p>
      <p className="conv-empty-sub">Open a conversation from search or create a new one.</p>
    </div>
  );
}

async function apiPost(path: string, body: Record<string, string>): Promise<{ success: boolean; data?: any; error?: string }> {
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

async function apiGet(path: string): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    return await r.json();
  } catch {
    return { success: false, error: 'Network error' };
  }
}

export const ConversationWorkspace: FC<ConversationWorkspaceProps> = ({ conversation, loading, error }) => {
  const [msg, setMsg] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [sending, setSending] = useState(false);
  const [apiError, setApiError] = useState('');

  // Load messages when conversation changes
  const loadMessages = useCallback(async () => {
    if (!conversation?.id) return;
    const result = await apiGet(`/api/v1/founder/conversations/${conversation.id}/messages`);
    if (result.success && result.data?.messages) {
      setMessages(result.data.messages);
    } else {
      // Try the object-scoped conversation endpoint
      const objId = conversation.objectIds?.[0];
      if (objId) {
        const r2 = await apiGet(`/api/v1/founder/objects/${objId}/conversation`);
        if (r2.success && r2.data?.messages) {
          setMessages(r2.data.messages);
        }
      }
    }
    // Load any existing messages
    const convId = conversation.id;
    const r3 = await apiGet(`/api/v1/founder/ai/chat/${convId}`);
    if (r3.success && r3.data) {
      // already loaded from conversation endpoint
    }
  }, [conversation?.id, conversation?.objectIds]);

  // Load initial messages
  useState(() => { loadMessages(); });

  const handleSend = useCallback(async () => {
    if (!msg.trim() || !conversation?.id || sending) return;
    setSending(true);
    setApiError('');

    // Add user message optimistically
    const userMsg: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: msg.trim(),
    };
    setMessages(prev => [...prev, userMsg]);
    setMsg('');

    try {
      // Send to AI chat endpoint
      const result = await apiPost(`/api/v1/founder/ai/chat/${conversation.id}`, { content: msg.trim() });

      if (result.success && result.data) {
        const aiMsg: Message = {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: result.data.response || 'I processed your request.',
          created_at: new Date().toISOString(),
        };
        setMessages(prev => [...prev, aiMsg]);
      } else if (result.data?.error) {
        setApiError(result.data.error);
        // Try the conversation messages endpoint as fallback
        const fallback = await apiPost(`/api/v1/founder/conversations/${conversation.id}/messages`, { content: msg.trim() });
        if (fallback.success && fallback.data) {
          const aiMsg: Message = {
            id: `ai-${Date.now()}`,
            role: 'assistant',
            content: fallback.data.response || fallback.data.assistant?.content || 'Understood.',
            created_at: new Date().toISOString(),
          };
          setMessages(prev => [...prev, aiMsg]);
        }
      } else {
        setApiError('No response from AI. Please try again.');
      }
    } catch {
      setApiError('Failed to send message.');
    }
    setSending(false);
  }, [msg, conversation?.id, sending]);

  if (error)
    return (
      <div className="conv-error" role="alert">
        {error}
      </div>
    );
  if (loading) return <LoadingState />;
  if (!conversation) return <EmptyState />;

  return (
    <div className="conv-workspace">
      <div className="conv-primary">
        <div className="conv-header">
          <div className="conv-title-row">
            <StatusDot state={{ status: conversation.status }} />
            <h2 className="conv-title">{conversation.title}</h2>
          </div>
          {conversation.intent && <div className="conv-intent">Focus: {conversation.intent}</div>}
        </div>

        <div className="conv-messages" role="log" aria-label="Conversation messages">
          {messages.length === 0 && (
            <div className="conv-placeholder">
              <p>Messages appear here as the conversation progresses.</p>
              <p className="conv-placeholder-sub">Ask SHUNYA anything about this context.</p>
            </div>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`conv-msg conv-msg-${m.role}`}>
              <div className="conv-msg-role">{m.role === 'user' ? 'You' : 'SHUNYA'}</div>
              <div className="conv-msg-content">{m.content}</div>
              {m.created_at && (
                <div className="conv-msg-time">{new Date(m.created_at).toLocaleTimeString()}</div>
              )}
            </div>
          ))}
          {sending && <div className="conv-typing">SHUNYA is thinking…</div>}
          {apiError && <div className="conv-error-msg">{apiError}</div>}
        </div>

        <div className="conv-input-row">
          <input
            className="conv-input"
            placeholder={sending ? 'Waiting for response…' : 'Type a message…'}
            value={msg}
            onChange={(e) => setMsg(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && msg.trim() && !sending) handleSend();
            }}
            disabled={sending}
            aria-label="Message input"
          />
          <button className="conv-send" onClick={handleSend} disabled={!msg.trim() || sending} aria-label="Send message">
            {sending ? '…' : 'Send'}
          </button>
        </div>
      </div>

      <div className="conv-sidebar" role="complementary" aria-label="Conversation context">
        <Panel id="participants" name="People">
          {conversation.participants?.length > 0 ? (
            conversation.participants.map((p, i) => (
              <div key={i} className="conv-participant">
                {p}
              </div>
            ))
          ) : (
            <div className="conv-empty">No participants yet</div>
          )}
        </Panel>
        <Panel id="context" name="Context">
          <Metric
            state={{
              value: (conversation.objectIds?.length ?? 0) + (conversation.commitmentIds?.length ?? 0),
              subtitle: 'Linked items',
            }}
          />
        </Panel>
        <Panel id="ai" name="AI Context">
          <InsightCard
            state={{
              title: 'Conversation Analysis',
              body: messages.length > 0
                ? `${messages.length} message${messages.length > 1 ? 's' : ''} exchanged. Ask SHUNYA anything about this context.`
                : 'AI insights appear as the conversation develops.',
              confidence: 'medium',
              type: 'observation',
            }}
          />
        </Panel>
      </div>

      <style>{`
.conv-workspace { display: flex; height: 100%; gap: var(--sh-space-4); }
.conv-primary { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.conv-sidebar { width: 260px; display: flex; flex-direction: column; gap: var(--sh-space-4); overflow-y: auto; }
.conv-header { padding: var(--sh-space-4); border-bottom: 1px solid var(--sh-border); }
.conv-title-row { display: flex; align-items: center; gap: var(--sh-space-2); }
.conv-title { font-size: var(--sh-text-lg); font-weight: 500; margin: 0; }
.conv-intent { font-size: var(--sh-text-sm); color: var(--sh-text-secondary); margin-top: 4px; }
.conv-messages { flex: 1; overflow-y: auto; padding: var(--sh-space-4); display: flex; flex-direction: column; gap: var(--sh-space-3); }
.conv-placeholder { text-align: center; color: var(--sh-text-secondary); padding: var(--sh-space-12); }
.conv-placeholder-sub { font-size: var(--sh-text-sm); margin-top: 4px; }
.conv-msg { padding: var(--sh-space-3) var(--sh-space-4); border-radius: var(--sh-radius-md); max-width: 80%; }
.conv-msg-user { align-self: flex-end; background: var(--sh-gold, #a4865f); color: #fff; }
.conv-msg-assistant { align-self: flex-start; background: var(--sh-surface, #fff); border: 1px solid var(--sh-border); color: var(--sh-text); }
.conv-msg-role { font-size: var(--sh-text-xs); font-weight: 600; margin-bottom: 4px; opacity: 0.7; }
.conv-msg-content { font-size: var(--sh-text-md); line-height: 1.5; white-space: pre-wrap; }
.conv-msg-time { font-size: var(--sh-text-xs); color: var(--sh-text-secondary); margin-top: 4px; text-align: right; opacity: 0.6; }
.conv-typing { padding: var(--sh-space-3) var(--sh-space-4); font-size: var(--sh-text-sm); color: var(--sh-text-secondary); font-style: italic; align-self: flex-start; }
.conv-error-msg { padding: var(--sh-space-2) var(--sh-space-4); font-size: var(--sh-text-sm); color: var(--sh-danger); background: rgba(209,69,59,0.08); border-radius: var(--sh-radius-sm); margin: var(--sh-space-2) 0; }
.conv-input-row { display: flex; gap: var(--sh-space-2); padding: var(--sh-space-2) var(--sh-space-4); border-top: 1px solid var(--sh-border); }
.conv-input { flex: 1; padding: var(--sh-space-2) var(--sh-space-4); border: 1px solid var(--sh-surface); border-radius: var(--sh-radius-sm); font-size: var(--sh-text-md); background: var(--sh-bg); color: var(--sh-text); outline: none; }
.conv-input:focus { border-color: var(--sh-gold); }
.conv-send { padding: var(--sh-space-2) var(--sh-space-6); background: var(--sh-text, #1A1C1D); color: var(--sh-surface, #FFFFFF); border: none; border-radius: var(--sh-radius-sm); font-size: var(--sh-text-sm); cursor: pointer; }
.conv-send:disabled { opacity: 0.4; cursor: not-allowed; }
.conv-participant { padding: var(--sh-space-1) 0; font-size: var(--sh-text-sm); }
.conv-empty { font-size: var(--sh-text-xs); color: var(--sh-text-secondary); font-style: italic; padding: var(--sh-space-2) 0; }
.conv-empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--sh-text-secondary); gap: 8px; }
.conv-empty-sub { font-size: var(--sh-text-sm); }
.conv-error { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--sh-danger); }
      `}</style>
    </div>
  );
};