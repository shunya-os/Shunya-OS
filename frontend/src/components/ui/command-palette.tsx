/**
 * Global Command Palette — Ctrl+K activated.
 *
 * Navigation Canon §6:
 *   Always available, non-modal, fuzzy search, contextual.
 *   Modes: type=search -> Ask SHUNYA (IntelligenceRuntime),
 *          "/"=commands, ">"=workspace switch, "?"=shortcuts.
 *   Recent objects shown on open.
 *
 * Directive §12:
 *   The command bar is a primary SHUNYA interaction surface.
 *   Not an ordinary search box.
 *
 * G3 Phase 6.2: Wired to IntelligenceRuntime's ask() via POST /api/v1/ai/chat.
 *   Search mode now sends the query to the canonical chat endpoint and
 *   displays the AI response inline before navigating away.
 */
import { useEffect, useState, useRef, useCallback } from 'react';
import { aiChat } from '../../api/ai-chat';

interface CmdItem {
  id: string;
  label: string;
  type: 'object' | 'command' | 'workspace' | 'action';
  icon?: string;
  onSelect: () => void;
}

type AskResult = { content: string; error?: string } | null;

interface Props {
  onClose: () => void;
  recentItems?: CmdItem[];
  commands?: CmdItem[];
  workspaces?: CmdItem[];
  /** Optional workspace/object context passed to the AI. */
  workspaceContext?: string;
  /** Callback when the AI returns an answer the surface should display. */
  onAskResult?: (query: string, result: AskResult) => void;
}

export function CommandPalette({ onClose, recentItems = [], commands = [], workspaces = [], workspaceContext, onAskResult }: Props) {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'search' | 'command' | 'workspace' | 'shortcuts' | 'ai-result'>('search');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [aiResult, setAiResult] = useState<AskResult>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Detect mode from input prefix
  const handleInput = (value: string) => {
    if (mode === 'ai-result') return; // Don't change mode while showing result
    setQuery(value);
    setSelectedIndex(0);
    if (value.startsWith('/')) setMode('command');
    else if (value.startsWith('>')) setMode('workspace');
    else if (value === '?') setMode('shortcuts');
    else setMode('search');
  };

  const filteredItems = useCallback(() => {
    const q = query.replace(/^[/>?]/, '').toLowerCase();
    let items: CmdItem[] = [];

    switch (mode) {
      case 'command':
        items = commands.filter(c => c.label.toLowerCase().includes(q));
        break;
      case 'workspace':
        items = workspaces.filter(w => w.label.toLowerCase().includes(q));
        break;
      case 'shortcuts':
      case 'ai-result':
        items = [];
        break;
      default:
        // Search: show recent items first, then filter
        if (!q) items = recentItems.slice(0, 5);
        else items = [...recentItems, ...commands, ...workspaces]
          .filter(i => i.label.toLowerCase().includes(q));
    }
    return items;
  }, [query, mode, recentItems, commands, workspaces]);

  const items = filteredItems();

  // ── Ask SHUNYA via IntelligenceRuntime chat endpoint ───────
  const askShunya = useCallback(async (question: string) => {
    setAiLoading(true);
    setAiError(null);
    setAiResult(null);
    try {
      const messages: { role: 'system' | 'user'; content: string }[] = [{ role: 'user', content: question }];
      if (workspaceContext) {
        messages.unshift({ role: 'system', content: `Current workspace context: ${workspaceContext}. Answer based on the user's organization data when possible.` });
      }
      const resp = await aiChat(messages, { max_tokens: 512 });
      if (resp.error) {
        setAiError(resp.error);
        setAiResult({ content: '', error: resp.error });
        return;
      }
      const result: AskResult = { content: resp.content };
      setAiResult(result);
      setMode('ai-result');
      onAskResult?.(question, result);
    } catch (err: any) {
      const msg = err?.message || 'SHUNYA could not answer that.';
      setAiError(msg);
      setAiResult({ content: '', error: msg });
    } finally {
      setAiLoading(false);
    }
  }, [workspaceContext, onAskResult]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (mode === 'ai-result') {
          setMode('search');
          setAiResult(null);
          setAiError(null);
          return;
        }
        onClose();
        return;
      }
      if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIndex(i => Math.min(i + 1, items.length - 1)); }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIndex(i => Math.max(i - 1, 0)); }
      if (e.key === 'Enter') {
        if (mode === 'ai-result') { onClose(); return; }
        // In search mode with text, ask SHUNYA instead of navigating
        if (mode === 'search' && query.trim() && !query.startsWith('/') && !query.startsWith('>')) {
          e.preventDefault();
          askShunya(query.trim());
          return;
        }
        if (items[selectedIndex]) {
          items[selectedIndex].onSelect();
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [items, selectedIndex, onClose, mode, query, askShunya]);

  return (
    <div className="sh-cmd-overlay" onClick={onClose} role="dialog" aria-label="Command palette">
      <div className="sh-cmd-palette" onClick={e => e.stopPropagation()}>
        {/* Input (hidden when showing AI result — replaced by the result view) */}
        {mode !== 'ai-result' && (
          <div className="sh-cmd-input-wrap">
            <svg className="sh-cmd-search-icon" width="18" height="18" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="1.5"
              strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              ref={inputRef}
              className="sh-cmd-input"
              type="text"
              value={query}
              onChange={e => handleInput(e.target.value)}
              placeholder={
                mode === 'command' ? 'Type a command…' :
                mode === 'workspace' ? 'Switch to workspace…' :
                mode === 'shortcuts' ? 'Keyboard shortcuts' :
                'Ask SHUNYA or type / for commands…'
              }
              spellCheck={false}
              autoComplete="off"
            />
            <kbd className="sh-cmd-kbd">Esc</kbd>
          </div>
        )}

        {/* Mode indicator */}
        {mode !== 'search' && mode !== 'ai-result' && (
          <div className="sh-cmd-mode">
            {mode === 'command' && 'Command mode — type a command'}
            {mode === 'workspace' && 'Workspace mode — switch workspace'}
            {mode === 'shortcuts' && 'Keyboard shortcuts'}
          </div>
        )}

        {/* Results */}
        <div className="sh-cmd-results" ref={listRef} role="listbox">
          {mode === 'ai-result' && aiResult ? (
            <div className="sh-cmd-ai-result">
              <div className="sh-cmd-ai-header">
                <span className="sh-cmd-ai-icon">◈</span>
                <span className="sh-cmd-ai-label">SHUNYA</span>
              </div>
              <p className="sh-cmd-ai-content">{aiResult.content}</p>
              <p className="sh-cmd-ai-hint">Press Enter to close, or Esc to go back</p>
            </div>
          ) : mode === 'shortcuts' ? (
            <div className="sh-cmd-shortcuts">
              <div className="sh-cmd-shortcut"><kbd>Ctrl+K</kbd><span>Command palette</span></div>
              <div className="sh-cmd-shortcut"><kbd>Ctrl+Tab</kbd><span>Next workspace</span></div>
              <div className="sh-cmd-shortcut"><kbd>Ctrl+Shift+Tab</kbd><span>Previous workspace</span></div>
              <div className="sh-cmd-shortcut"><kbd>Ctrl+[1-9]</kbd><span>Switch to workspace</span></div>
              <div className="sh-cmd-shortcut"><kbd>/</kbd><span>Command mode</span></div>
              <div className="sh-cmd-shortcut"><kbd>&gt;</kbd><span>Workspace mode</span></div>
              <div className="sh-cmd-shortcut"><kbd>?</kbd><span>This help</span></div>
              <div className="sh-cmd-shortcut"><kbd>Enter</kbd><span>Ask SHUNYA or select item</span></div>
              <div className="sh-cmd-shortcut"><kbd>Esc</kbd><span>Dismiss</span></div>
            </div>
          ) : aiLoading ? (
            <div className="sh-cmd-ai-loading">
              <span className="sh-cmd-ai-loading-dot" />
              <span className="sh-cmd-ai-loading-dot" />
              <span className="sh-cmd-ai-loading-dot" />
              <span className="sh-cmd-ai-loading-text">SHUNYA is thinking…</span>
            </div>
          ) : aiError ? (
            <div className="sh-cmd-empty sh-cmd-error" role="alert">
              <p>{aiError}</p>
              <button className="sh-cmd-retry-btn" onClick={() => { setAiError(null); setMode('search'); }}>
                Try again
              </button>
            </div>
          ) : items.length === 0 ? (
            <div className="sh-cmd-empty">
              {query
                ? 'No results found — press Enter to ask SHUNYA'
                : 'Type to search, or use / for commands, > for workspace switch, ? for shortcuts'}
            </div>
          ) : (
            items.map((item, i) => (
              <div
                key={item.id}
                className={`sh-cmd-item${i === selectedIndex ? ' sh-cmd-item--selected' : ''}`}
                role="option"
                aria-selected={i === selectedIndex}
                onClick={() => { item.onSelect(); onClose(); }}
                onMouseEnter={() => setSelectedIndex(i)}
              >
                <span className={`sh-cmd-item-type sh-cmd-type--${item.type}`}>
                  {item.type === 'object' ? '●' : item.type === 'command' ? '/' : item.type === 'workspace' ? '>' : '→'}
                </span>
                <span className="sh-cmd-item-label">{item.label}</span>
              </div>
            ))
          )}
        </div>
      </div>

      <style>{`
.sh-cmd-overlay {
  position: fixed; inset: 0;
  z-index: 1000;
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 120px;
  background: rgba(251,248,245,0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.sh-cmd-palette {
  width: 100%; max-width: 600px;
  background: var(--shunya-surface, #FFFFFF);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-md, 16px);
  box-shadow: var(--shunya-shadow-xl, 0 8px 40px rgba(26,28,29,0.08));
  overflow: hidden;
}
.sh-cmd-input-wrap {
  display: flex; align-items: center;
  gap: 10px; padding: 16px 20px;
  border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.sh-cmd-search-icon {
  flex-shrink: 0;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
}
.sh-cmd-input {
  flex: 1; border: none; outline: none;
  font-size: var(--shunya-text-md, 16px);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  background: transparent;
  color: var(--shunya-text, #1A1C1D);
}
.sh-cmd-input::placeholder {
  color: var(--shunya-text-faint, rgba(26,28,29,0.15));
}
.sh-cmd-kbd {
  font-size: 10px; font-family: var(--shunya-font-mono, monospace);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  background: var(--shunya-bg, #FBF8F5);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.sh-cmd-mode {
  padding: 8px 20px;
  font-size: var(--shunya-text-xs, 10px);
  font-weight: 600;
  letter-spacing: var(--shunya-tracking-wider, 0.06em);
  text-transform: uppercase;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  background: var(--shunya-bg, #FBF8F5);
  border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
}
.sh-cmd-results {
  max-height: 400px;
  overflow-y: auto;
  padding: 4px;
}
.sh-cmd-item {
  display: flex; align-items: center;
  gap: 10px; padding: 10px 16px;
  border-radius: var(--shunya-radius-sm, 10px);
  cursor: pointer;
  transition: background var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}
.sh-cmd-item--selected {
  background: var(--shunya-border, rgba(26,28,29,0.07));
}
.sh-cmd-item-type {
  width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
}
.sh-cmd-type--object { color: var(--shunya-gold, #A4865F); }
.sh-cmd-type--command { font-family: var(--shunya-font-mono, monospace); }
.sh-cmd-type--workspace { color: var(--shunya-text-secondary, rgba(26,28,29,0.55)); }
.sh-cmd-item-label {
  font-size: var(--shunya-text-base, 14px);
  color: var(--shunya-text, #1A1C1D);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sh-cmd-empty {
  padding: 32px 20px;
  text-align: center;
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
}
.sh-cmd-error {
  color: #B91C1C;
}
.sh-cmd-retry-btn {
  margin-top: 8px;
  padding: 6px 16px;
  font-size: var(--shunya-text-sm, 12px);
  color: #6C4AE2;
  background: transparent;
  border: 1px solid rgba(108,74,226,0.2);
  border-radius: 6px;
  cursor: pointer;
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
}
.sh-cmd-shortcuts {
  padding: 12px 16px;
  display: flex; flex-direction: column; gap: 6px;
}
.sh-cmd-shortcut {
  display: flex; align-items: center; gap: 12px;
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
}
.sh-cmd-shortcut kbd {
  width: 100px;
  font-family: var(--shunya-font-mono, monospace);
  font-size: 10px;
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  background: var(--shunya-bg, #FBF8F5);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  text-align: center;
}
.sh-cmd-ai-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 40px 20px;
}
.sh-cmd-ai-loading-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #6C4AE2;
  animation: sh-cmd-bounce 1.4s ease-in-out infinite both;
}
.sh-cmd-ai-loading-dot:nth-child(1) { animation-delay: -0.32s; }
.sh-cmd-ai-loading-dot:nth-child(2) { animation-delay: -0.16s; }
.sh-cmd-ai-loading-dot:nth-child(3) { animation-delay: 0s; }
.sh-cmd-ai-loading-text {
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  margin-left: 8px;
}
@keyframes sh-cmd-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
.sh-cmd-ai-result {
  padding: 20px;
}
.sh-cmd-ai-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.sh-cmd-ai-icon {
  font-size: 18px;
  color: #6C4AE2;
}
.sh-cmd-ai-label {
  font-size: var(--shunya-text-sm, 12px);
  font-weight: 600;
  color: #6C4AE2;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.sh-cmd-ai-content {
  font-size: var(--shunya-text-base, 14px);
  line-height: 1.6;
  color: var(--shunya-text, #1A1C1D);
  white-space: pre-wrap;
}
.sh-cmd-ai-hint {
  margin-top: 16px;
  font-size: var(--shunya-text-xs, 10px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  text-align: center;
}
@media (max-width: 480px) {
  .sh-cmd-overlay { padding-top: 60px; }
  .sh-cmd-palette { max-width: 100%; margin: 0 12px; border-radius: var(--shunya-radius-sm, 10px); }
}
      `}</style>
    </div>
  );
}

// ── Hook: Global Ctrl+K handler ─────────────────────────────────

export function useCommandPalette(open: boolean, onOpen?: () => void, onClose?: () => void) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (open) onClose?.();
        else onOpen?.();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onOpen, onClose]);
}