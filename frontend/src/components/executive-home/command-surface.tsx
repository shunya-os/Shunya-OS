/**
 * SHUNYA Command Surface — Persistent, always-available command input.
 *
 * Per Milestone E1 §4:
 *   - Understand natural language
 *   - Accept commands
 *   - Create execution requests
 *   - Navigate existing objects
 *
 * Persists regardless of page scroll. Fixed at the bottom of the viewport.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { useWorkspaceStore } from '../../runtimes/workspace/store';
import { api } from '../../api/client';

interface CommandSuggestion {
  id: string;
  label: string;
  description: string;
  action: () => void;
}

export function CommandSurface() {
  const [input, setInput] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [mode, setMode] = useState<'command' | 'ask' | 'idle'>('idle');
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const open = useWorkspaceStore(s => s.open);

  // Focus input when expanded
  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isExpanded]);

  const handleSubmit = useCallback(async () => {
    if (!input.trim()) return;
    const text = input.trim();

    // Check for navigation commands
    if (text.startsWith('/open ') || text.startsWith('/go ')) {
      const target = text.replace(/^\/(open|go)\s+/, '');
      open(target, 'object', { objectType: 'search', objectId: target.toLowerCase().replace(/\s+/g, '_') });
      setInput('');
      setIsExpanded(false);
      setResponse(null);
      return;
    }

    // Check for creation commands
    if (text.startsWith('/create ') || text.startsWith('/new ')) {
      const parts = text.replace(/^\/(create|new)\s+/, '').split(/\s+/);
      const type = parts[0] || 'Document';
      const name = parts.slice(1).join(' ') || `New ${type}`;
      try {
        setLoading(true);
        const resp = await api.query('/founder/objects', {
          method: 'POST',
          body: JSON.stringify({ name, object_type: type, content: '' }),
        });
        setResponse(`Created ${type}: "${name}"`);
        if (resp.data?.object_id) {
          open(name, 'object', { objectType: type, objectId: resp.data.object_id });
        }
      } catch {
        setResponse(`Could not create ${type}. Try again.`);
      } finally {
        setLoading(false);
      }
      setInput('');
      return;
    }

    // Ask mode — send to AI
    if (mode === 'ask' || text.endsWith('?')) {
      try {
        setLoading(true);
        const resp = await api.query('/founder/executive-home');
        if (resp.data) {
          const summary = `I see ${resp.data.object_summary?.total || 0} objects, ${resp.data.active_commitments?.length || 0} active commitments, and ${resp.data.recent_activity?.length || 0} recent events.`;
          setResponse(summary);
        } else {
          setResponse('SHUNYA is observing your organization. Ask me about your business objects.');
        }
      } catch {
        setResponse('AI analysis is temporarily unavailable.');
      } finally {
        setLoading(false);
      }
      setInput('');
      return;
    }

    // Default: try as a command
    setResponse(`I understood: "${text}". SHUNYA is processing your request.`);
    setInput('');
  }, [input, mode, open]);

  const suggestions: CommandSuggestion[] = [
    {
      id: 'open-home',
      label: '/open Home',
      description: 'Return to Executive Home',
      action: () => {
        const home = useWorkspaceStore.getState().workspaces.find(w => w.identity.type === 'home');
        if (home) useWorkspaceStore.getState().activate(home.identity.id);
        setIsExpanded(false);
      },
    },
    {
      id: 'create-object',
      label: '/create Document',
      description: 'Create a new business object',
      action: () => {
        setInput('/create Document ');
        setMode('command');
        inputRef.current?.focus();
      },
    },
    {
      id: 'ask-shunya',
      label: 'Ask SHUNYA',
      description: 'Ask about your business',
      action: () => {
        setInput('');
        setMode('ask');
        inputRef.current?.focus();
      },
    },
  ];

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
    if (e.key === 'Escape') {
      setIsExpanded(false);
      setResponse(null);
    }
    if (e.key === 'ArrowUp' && !input) {
      // Previous command from history
    }
  };

  return (
    <>
      {/* Persistent trigger bar */}
      {!isExpanded && (
        <button
          className="sh-cmd-trigger"
          onClick={() => setIsExpanded(true)}
          aria-label="Open SHUNYA command surface"
          title="SHUNYA Command (⌘K)"
        >
          <span className="sh-cmd-trigger-icon">शून्य</span>
          <span className="sh-cmd-trigger-text">Ask SHUNYA or type a command…</span>
          <span className="sh-cmd-trigger-shortcut">⌘K</span>
        </button>
      )}

      {/* Expanded command surface */}
      {isExpanded && (
        <div className="sh-cmd-overlay" role="dialog" aria-label="SHUNYA command surface">
          <div className="sh-cmd-backdrop" onClick={() => { setIsExpanded(false); setResponse(null); }} />
          <div className="sh-cmd-panel">
            {/* Mode indicator */}
            <div className="sh-cmd-mode">
              {mode === 'ask' ? 'Ask SHUNYA' : mode === 'command' ? 'Command' : 'SHUNYA'}
            </div>

            {/* Input row */}
            <div className="sh-cmd-input-row">
              <span className="sh-cmd-prompt">{mode === 'ask' ? '?' : '>'}</span>
              <input
                ref={inputRef}
                className="sh-cmd-input"
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  mode === 'ask'
                    ? 'Ask about your business…'
                    : 'Type a command or question…'
                }
                disabled={loading}
              />
              {loading && <span className="sh-cmd-loading" />}
            </div>

            {/* Response */}
            {response && (
              <div className="sh-cmd-response" role="status">
                {response}
              </div>
            )}

            {/* Suggestions */}
            {!input && !response && (
              <div className="sh-cmd-suggestions">
                {suggestions.map(s => (
                  <button
                    key={s.id}
                    className="sh-cmd-suggestion"
                    onClick={s.action}
                  >
                    <span className="sh-cmd-suggestion-label">{s.label}</span>
                    <span className="sh-cmd-suggestion-desc">{s.description}</span>
                  </button>
                ))}
                <div className="sh-cmd-suggestion-hint">
                  Press <kbd>Enter</kbd> to submit · <kbd>Esc</kbd> to close
                </div>
              </div>
            )}

            {/* Mode toggle */}
            {!input && !response && (
              <div className="sh-cmd-footer">
                <button
                  className={`sh-cmd-mode-btn ${mode === 'command' ? 'sh-cmd-mode-active' : ''}`}
                  onClick={() => setMode(mode === 'command' ? 'idle' : 'command')}
                >
                  Command Mode
                </button>
                <button
                  className={`sh-cmd-mode-btn ${mode === 'ask' ? 'sh-cmd-mode-active' : ''}`}
                  onClick={() => setMode(mode === 'ask' ? 'idle' : 'ask')}
                >
                  Ask Mode
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
.sh-cmd-trigger {
  position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
  z-index: 500;
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px;
  background: var(--shunya-surface-2, #1a1a26);
  border: 1px solid var(--shunya-surface-1, #2a2a3a);
  border-radius: 24px;
  color: var(--shunya-text-secondary, #888);
  font-size: var(--shunya-font-size-sm);
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  max-width: 90vw;
}
.sh-cmd-trigger:hover {
  border-color: var(--shunya-color-secondary, #D4A84B);
  color: var(--shunya-text, #e0e0e0);
  background: var(--shunya-surface-1, #22222e);
}
.sh-cmd-trigger-icon { font-size: 14px; color: var(--shunya-color-ai, #D4A84B); }
.sh-cmd-trigger-text { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sh-cmd-trigger-shortcut {
  font-size: 10px; color: var(--shunya-text-secondary, #555);
  background: var(--shunya-surface-0, #141416);
  padding: 2px 6px; border-radius: 4px;
  font-family: monospace;
}

.sh-cmd-overlay {
  position: fixed; inset: 0; z-index: 1000;
  display: flex; align-items: center; justify-content: center;
}
.sh-cmd-backdrop {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.5);
}
.sh-cmd-panel {
  position: relative;
  width: 640px; max-width: 90vw;
  background: var(--shunya-surface-2, #1a1a26);
  border: 1px solid var(--shunya-surface-1, #333);
  border-radius: var(--shunya-radius-lg, 16px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  padding: var(--shunya-spacing-md);
  display: flex; flex-direction: column; gap: var(--shunya-spacing-sm);
}
.sh-cmd-mode {
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--shunya-color-ai, #D4A84B);
  font-weight: 600;
}
.sh-cmd-input-row {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px;
  background: var(--shunya-surface-1, #22222e);
  border: 1px solid var(--shunya-surface-0, #333);
  border-radius: var(--shunya-radius-md, 8px);
}
.sh-cmd-input-row:focus-within { border-color: var(--shunya-color-secondary, #D4A84B); }
.sh-cmd-prompt { font-family: monospace; color: var(--shunya-color-ai, #D4A84B); font-size: 16px; }
.sh-cmd-input {
  flex: 1; border: none; outline: none;
  background: transparent; color: var(--shunya-text, #e0e0e0);
  font-size: var(--shunya-font-size-md); line-height: 1.5;
}
.sh-cmd-input::placeholder { color: var(--shunya-text-secondary, #555); }
.sh-cmd-loading {
  width: 16px; height: 16px;
  border: 2px solid var(--shunya-surface-0, #333);
  border-top-color: var(--shunya-color-ai, #D4A84B);
  border-radius: 50%; animation: sh-cmd-spin 0.6s linear infinite;
}
@keyframes sh-cmd-spin { to { transform: rotate(360deg); } }
.sh-cmd-response {
  padding: var(--shunya-spacing-sm) var(--shunya-spacing-md);
  font-size: var(--shunya-font-size-sm);
  color: var(--shunya-text, #e0e0e0);
  background: var(--shunya-surface-0, #141416);
  border-radius: var(--shunya-radius-sm, 4px);
  line-height: 1.5;
}
.sh-cmd-suggestions {
  display: flex; flex-direction: column; gap: 4px;
}
.sh-cmd-suggestion {
  display: flex; align-items: center; gap: var(--shunya-spacing-sm);
  padding: var(--shunya-spacing-sm) var(--shunya-spacing-md);
  background: transparent; border: 1px solid transparent;
  border-radius: var(--shunya-radius-sm, 4px);
  cursor: pointer; text-align: left; color: inherit;
  transition: background 0.15s;
}
.sh-cmd-suggestion:hover { background: var(--shunya-surface-1, #22222e); border-color: var(--shunya-surface-0, #333); }
.sh-cmd-suggestion-label { font-size: var(--shunya-font-size-sm); font-weight: 500; min-width: 120px; }
.sh-cmd-suggestion-desc { font-size: var(--shunya-font-size-xs); color: var(--shunya-text-secondary, #888); }
.sh-cmd-suggestion-hint {
  text-align: center; font-size: 10px; color: var(--shunya-text-secondary, #555);
  padding: var(--shunya-spacing-sm) 0;
}
.sh-cmd-suggestion-hint kbd {
  background: var(--shunya-surface-0, #141416); padding: 1px 4px; border-radius: 2px;
  font-family: monospace; font-size: 10px;
}
.sh-cmd-footer {
  display: flex; gap: 4px; justify-content: center;
  padding-top: var(--shunya-spacing-sm);
  border-top: 1px solid var(--shunya-surface-1, #22222e);
}
.sh-cmd-mode-btn {
  padding: 4px 12px; border: 1px solid var(--shunya-surface-0, #333);
  border-radius: 12px; background: transparent;
  color: var(--shunya-text-secondary, #888); font-size: 11px;
  cursor: pointer; transition: all 0.15s;
}
.sh-cmd-mode-btn:hover { border-color: var(--shunya-color-secondary, #D4A84B); color: var(--shunya-text, #e0e0e0); }
.sh-cmd-mode-active { background: var(--shunya-color-ai, #D4A84B); color: #0a0a0f; border-color: var(--shunya-color-ai, #D4A84B); }
`}</style>
    </>
  );
}