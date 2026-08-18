/**
 * Three-Zone Workspace Shell — Canonical SHUNYA workspace layout.
 *
 * Visual Design Bible §4.5:
 *   Zone 1: Identity Strip (44px)
 *   Zone Left (280px): Navigation, search, graph
 *   Zone Center (flex:1): Primary object workspace
 *   Zone Right (340px): Intelligence pane
 *
 * Navigation Canon §2:
 *   Zone 1 always visible, fixed, glass effect, 56px height
 *   Contains: [Logo/Home] [Workspace Switcher] [Breadcrumb] [Search] [Notifications] [User Menu]
 */

import { type ReactNode } from 'react';
import { WorkspaceBar } from './workspace-bar';

interface ShellProps {
  leftPanel?: ReactNode;
  centerPanel: ReactNode;
  rightPanel?: ReactNode;
  showRightPanel?: boolean;
  breadcrumb?: string;
}

export function ThreeZoneShell({ leftPanel, centerPanel, rightPanel, showRightPanel = true, breadcrumb }: ShellProps) {
  return (
    <div className="shunya-workspace">
      {/* Zone 1: Identity Strip */}
      <header className="shunya-zone1" role="banner">
        <div className="shunya-zone1-left">
          <a href="/" className="shunya-logo" aria-label="SHUNYA Home">
            <span className="shunya-logo-dot" aria-hidden="true" />
            <span className="shunya-logo-text">SHUNYA</span>
          </a>
          <WorkspaceBar />
          {breadcrumb && (
            <nav className="shunya-breadcrumb" aria-label="Breadcrumb">
              <span className="shunya-breadcrumb-sep">/</span>
              <span className="shunya-breadcrumb-current">{breadcrumb}</span>
            </nav>
          )}
        </div>
        <div className="shunya-zone1-right">
          <button className="shunya-cmd-btn" onClick={() => {/* Ctrl+K handler */}}
            aria-label="Command palette (Ctrl+K)" title="Command palette (Ctrl+K)">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="6.5" cy="6.5" r="4.5" />
              <line x1="10" y1="10" x2="14" y2="14" />
            </svg>
          </button>
          <div className="shunya-user-menu">
            <button className="shunya-user-avatar" aria-label="User menu">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="10" cy="7" r="3" />
                <path d="M4 17c0-3.3 2.7-6 6-6s6 2.7 6 6" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Zone 2+3: Three-column content */}
      <div className="shunya-zone23">
        {/* Zone Left: Context Panel (280px) */}
        {leftPanel && (
          <aside className="shunya-zone-left" aria-label="Context panel">
            {leftPanel}
          </aside>
        )}

        {/* Zone Center: Primary Content (flex:1) */}
        <main className="shunya-zone-center" role="main">
          {centerPanel}
        </main>

        {/* Zone Right: Intelligence Pane (340px) */}
        {showRightPanel && rightPanel && (
          <aside className="shunya-zone-right" aria-label="Intelligence pane">
            {rightPanel}
          </aside>
        )}
      </div>

      <style>{`
/* ── SHUNYA Canonical Workspace Shell ─────────────────────── */

.shunya-workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--shunya-bg, #FBF8F5);
  color: var(--shunya-text, #1A1C1D);
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  font-size: var(--shunya-text-base, 14px);
  line-height: 1.5;
}

/* ── Zone 1: Identity Strip ──────────────────────────────── */

.shunya-zone1 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 16px;
  background: var(--shunya-bar-bg, #FAF9F8);
  border-bottom: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  flex-shrink: 0;
  z-index: 100;
  gap: 8px;
}

.shunya-zone1-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.shunya-zone1-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.shunya-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--shunya-text, #1A1C1D);
  flex-shrink: 0;
}

.shunya-logo-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--shunya-gold, #A4865F);
}

.shunya-logo-text {
  font-family: var(--shunya-font-display, 'Playfair Display', serif);
  font-size: var(--shunya-text-lg, 18px);
  font-weight: 400;
  letter-spacing: var(--shunya-tracking-wide, 0.02em);
  color: var(--shunya-text, #1A1C1D);
}

.shunya-breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--shunya-text-sm, 12px);
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  min-width: 0;
}

.shunya-breadcrumb-sep {
  color: var(--shunya-text-tertiary, rgba(26,28,29,0.35));
  margin: 0 4px;
}

.shunya-breadcrumb-current {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
}

.shunya-cmd-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: var(--shunya-radius-sm, 10px);
  background: var(--shunya-surface, #FFFFFF);
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  cursor: pointer;
  transition: color var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}

.shunya-cmd-btn:hover {
  color: var(--shunya-text, #1A1C1D);
  border-color: var(--shunya-border-hover, rgba(26,28,29,0.14));
}

.shunya-user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--shunya-surface, #FFFFFF);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  cursor: pointer;
  transition: color var(--shunya-duration-fast, 200ms) var(--shunya-ease, cubic-bezier(0.22,1,0.36,1));
}

.shunya-user-avatar:hover {
  color: var(--shunya-text, #1A1C1D);
  border-color: var(--shunya-border-hover, rgba(26,28,29,0.14));
}

/* ── Zone 2+3: Content Area ───────────────────────────────── */

.shunya-zone23 {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ── Zone Left (Context Panel) ────────────────────────────── */

.shunya-zone-left {
  width: 280px;
  min-width: 280px;
  background: var(--shunya-zone-left, #F3F2F2);
  border-right: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  overflow-y: auto;
  flex-shrink: 0;
}

/* ── Zone Center (Primary Content) ────────────────────────── */

.shunya-zone-center {
  flex: 1;
  min-width: 0;
  background: var(--shunya-zone-center, #FAFAF8);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* ── Zone Right (Intelligence Pane) ───────────────────────── */

.shunya-zone-right {
  width: 340px;
  min-width: 340px;
  background: var(--shunya-zone-right, #EBEBEA);
  border-left: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  overflow-y: auto;
  flex-shrink: 0;
}

/* ── Responsive ──────────────────────────────────────────── */

@media (max-width: 1024px) {
  .shunya-zone-right { display: none; }
  .shunya-zone-left { width: 220px; min-width: 220px; }
}

@media (max-width: 768px) {
  .shunya-zone-left { display: none; }
  .shunya-zone1 { height: 48px; padding: 0 12px; }
}
      `}</style>
    </div>
  );
}