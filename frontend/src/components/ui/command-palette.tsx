/**
 * Global Command Palette — Ctrl+K activated.
 *
 * Navigation Canon §6:
 *   Always available, non-modal, fuzzy search, contextual.
 *   Modes: type=search, "/"=commands, ">"=workspace switch, "?"=shortcuts.
 *   Recent objects shown on open.
 *
 * Directive §12:
 *   The command bar is a primary SHUNYA interaction surface.
 *   Not an ordinary search box.
 */

import { useEffect, useState, useRef, useCallback } from 'react';

interface CmdItem {
  id: string;
  label: string;
  type: 'object' | 'command' | 'workspace' | 'action';
  icon?: string;
  onSelect: () => void;
}

interface Props {
  onClose: () => void;
  recentItems?: CmdItem[];
  commands?: CmdItem[];
  workspaces?: CmdItem[];
}

export function CommandPalette({ onClose, recentItems = [], commands = [], workspaces = [] }: Props) {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'search' | 'command' | 'workspace' | 'shortcuts'>('search');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Detect mode from input prefix
  const handleInput = (value: string) => {
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

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { onClose(); return; }
      if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIndex(i => Math.min(i + 1, items.length - 1)); }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIndex(i => Math.max(i - 1, 0)); }
      if (e.key === 'Enter' && items[selectedIndex]) {
        items[selectedIndex].onSelect();
        onClose();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [items, selectedIndex, onClose]);

  return (
    <div className="sh-cmd-overlay" onClick={onClose} role="dialog" aria-label="Command palette">
      <div className="sh-cmd-palette" onClick={e => e.stopPropagation()}>
        {/* Input */}
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
              'Ask SHUNYA…'
            }
            spellCheck={false}
            autoComplete="off"
          />
          <kbd className="sh-cmd-kbd">Esc</kbd>
        </div>

        {/* Mode indicator */}
        {mode !== 'search' && (
          <div className="sh-cmd-mode">
            {mode === 'command' && 'Command mode — type a command'}
            {mode === 'workspace' && 'Workspace mode — switch workspace'}
            {mode === 'shortcuts' && 'Keyboard shortcuts'}
          </div>
        )}

        {/* Results */}
        <div className="sh-cmd-results" ref={listRef} role="listbox">
          {mode === 'shortcuts' ? (
            <div className="sh-cmd-shortcuts">
              <div className="sh-cmd-shortcut"><kbd>Ctrl+K</kbd><span>Command palette</span></div>
              <div className="sh-cmd-shortcut"><kbd>Ctrl+Tab</kbd><span>Next workspace</span></div>
              <div className="sh-cmd-shortcut"><kbd>Ctrl+Shift+Tab</kbd><span>Previous workspace</span></div>
              <div className="sh-cmd-shortcut"><kbd>Ctrl+[1-9]</kbd><span>Switch to workspace</span></div>
              <div className="sh-cmd-shortcut"><kbd>/</kbd><span>Command mode</span></div>
              <div className="sh-cmd-shortcut"><kbd>&gt;</kbd><span>Workspace mode</span></div>
              <div className="sh-cmd-shortcut"><kbd>?</kbd><span>This help</span></div>
              <div className="sh-cmd-shortcut"><kbd>Esc</kbd><span>Dismiss</span></div>
            </div>
          ) : items.length === 0 ? (
            <div className="sh-cmd-empty">
              {query ? 'No results found' : 'Type to search or use / for commands'}
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
  max-height: 320px;
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