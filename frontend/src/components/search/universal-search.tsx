/**
 * Universal Search — Keyboard-first search across all object types.
 *
 * Results open through the Composition Engine — no object-specific pages.
 * Queries the real backend. No fake data. No hardcoded results.
 *
 * Uses Mantine Highlight for search term highlighting and Kbd for
 * keyboard shortcut hints.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Highlight, Kbd } from '@mantine/core';
import { useOpenWorkspace } from '../../hooks/workspace-hooks';
import { ModuleRegistry } from '../../runtimes/module-registry';

interface SearchResult {
  id: string;
  type: string;
  title: string;
  subtitle: string;
  status?: string;
}

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [idx, setIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const openWorkspace = useOpenWorkspace();

  // ── Keyboard shortcut ──────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(true);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
      if (e.key === 'Escape' && open) {
        setOpen(false);
        setQuery('');
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);

  // ── Search ─────────────────────────────────────────────
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const hits = await ModuleRegistry.searchAll(query);
        setResults(hits.slice(0, 20));
      } catch {
        setResults([]);
      } finally {
        setIdx(0);
        setLoading(false);
      }
    }, 200);
    return () => clearTimeout(t);
  }, [query]);

  // ── Keyboard navigation ────────────────────────────────
  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setIdx((i) => Math.min(i + 1, results.length - 1));
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setIdx((i) => Math.max(i - 1, 0));
      }
      if (e.key === 'Enter' && results[idx]) {
        const r = results[idx];
        setOpen(false);
        setQuery('');
        openWorkspace(r.title, r.type as any, { objectType: r.type, objectId: r.id });
      }
    },
    [results, idx, openWorkspace],
  );

  if (!open) return null;

  return (
    <div className="sh-search-overlay" onClick={() => setOpen(false)} role="dialog" aria-label="Search">
      <div className="sh-search-panel" onClick={(e) => e.stopPropagation()} role="searchbox">
        <div className="sh-search-input-wrap">
          <span className="sh-search-icon">⌕</span>
          <input
            ref={inputRef}
            className="sh-search-input"
            placeholder="Search your business…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            autoComplete="off"
            spellCheck={false}
          />
          <Kbd style={{ opacity: 0.35 }}>⌘K</Kbd>
          {loading && <span className="sh-search-spin" />}
        </div>
        {results.length > 0 && (
          <div className="sh-search-results">
            {results.map((r, i) => (
              <div
                key={`${r.type}-${r.id}`}
                className={`sh-search-item ${i === idx ? 'sh-search-focused' : ''}`}
                role="option"
                aria-selected={i === idx}
                onMouseEnter={() => setIdx(i)}
                onClick={() => {
                  setOpen(false);
                  setQuery('');
                  openWorkspace(r.title, r.type as any, { objectType: r.type, objectId: r.id });
                }}
              >
                <span className="sh-search-item-type">{r.type[0].toUpperCase()}</span>
                <div className="sh-search-item-body">
                  <div className="sh-search-item-title">
                    <Highlight highlight={query} size="sm">
                      {r.title}
                    </Highlight>
                  </div>
                  <div className="sh-search-item-sub">
                    <Highlight highlight={query} size="xs">
                      {r.subtitle}
                    </Highlight>
                  </div>
                </div>
                {r.status && <span className="sh-search-item-status">{r.status}</span>}
              </div>
            ))}
          </div>
        )}
        {query && !loading && results.length === 0 && (
          <div className="sh-search-empty">
            No results for "<Highlight highlight={query} size="sm">{query}</Highlight>"
          </div>
        )}
      </div>
    </div>
  );
}

const styles = `
.sh-search-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: flex-start; justify-content: center; padding-top: 15vh; z-index: 999; }
.sh-search-panel { width: 100%; max-width: 560px; background: var(--sh-surface); border-radius: var(--sh-radius-lg); box-shadow: var(--sh-shadow-xl); overflow: hidden; }
.sh-search-input-wrap { display: flex; align-items: center; padding: var(--sh-space-2) var(--sh-space-4); gap: var(--sh-space-2); border-bottom: 1px solid var(--sh-border); }
.sh-search-icon { font-size: 20px; color: var(--sh-text-secondary); }
.sh-search-input { flex: 1; border: none; outline: none; font-size: var(--sh-text-lg); background: transparent; color: var(--sh-text); font-family: var(--sh-font-body); }
.sh-search-input::placeholder { color: var(--sh-text-secondary); }
.sh-search-spin { width: 16px; height: 16px; border: 2px solid var(--sh-border, rgba(26,28,29,0.08)); border-top-color: var(--sh-gold); border-radius: 50%; animation: sh-spin 0.6s linear infinite; }
.sh-search-results { max-height: 360px; overflow-y: auto; }
.sh-search-item { display: flex; align-items: center; gap: var(--sh-space-2); padding: var(--sh-space-2) var(--sh-space-4); cursor: pointer; transition: background var(--sh-timing-fast); }
.sh-search-item:hover, .sh-search-focused { background: var(--sh-border); }
.sh-search-item-type { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: var(--sh-radius-sm); background: var(--sh-gold, #A4865F); color: white; font-size: 12px; font-weight: 600; text-transform: uppercase; flex-shrink: 0; }
.sh-search-item-body { flex: 1; min-width: 0; }
.sh-search-item-title { font-size: var(--sh-text-sm); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sh-search-item-sub { font-size: var(--sh-text-xs); color: var(--sh-text-secondary); }
.sh-search-item-status { font-size: 10px; color: var(--sh-text-secondary); text-transform: uppercase; flex-shrink: 0; }
.sh-search-empty { padding: var(--sh-space-8); text-align: center; color: var(--sh-text-secondary); font-size: var(--sh-text-sm); }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  document.head.appendChild(el);
}
