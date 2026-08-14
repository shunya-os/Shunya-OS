/**
 * Integration Hub 2.0 — Integration Hub
 *
 * 12 mock service connectors with connect/disconnect, localStorage state,
 * mock OAuth flow popup, and last sync timestamp.
 * Warm glass-morphism design matching the SHUNYA OS aesthetic.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Zap,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ExternalLink,
  Unplug,
  Plug,
  Clock,
  Search,
} from 'lucide-react';

// ── Types ──

interface ConnectorState {
  connected: boolean;
  error: boolean;
  lastSync: string; // ISO timestamp
}

interface Connector {
  id: string;
  name: string;
  description: string;
  emoji: string;
  category: string;
}

// ── Constants ──

const CONNECTORS: Connector[] = [
  { id: 'gmail', name: 'Gmail', description: 'Send and read emails via Gmail API', emoji: '📧', category: 'Communication' },
  { id: 'google-calendar', name: 'Google Calendar', description: 'Sync events, meetings, and reminders', emoji: '📅', category: 'Productivity' },
  { id: 'slack', name: 'Slack', description: 'Post messages and notifications to channels', emoji: '💬', category: 'Communication' },
  { id: 'notion', name: 'Notion', description: 'Sync pages, databases, and notes', emoji: '📝', category: 'Productivity' },
  { id: 'trello', name: 'Trello', description: 'Manage boards, cards, and workflows', emoji: '📋', category: 'Productivity' },
  { id: 'github', name: 'GitHub', description: 'Track issues, PRs, and commits', emoji: '🐙', category: 'Dev Tools' },
  { id: 'stripe', name: 'Stripe', description: 'Process payments and view transactions', emoji: '💳', category: 'Finance' },
  { id: 'paypal', name: 'PayPal', description: 'Send invoices and manage payments', emoji: '🅿️', category: 'Finance' },
  { id: 'shopify', name: 'Shopify', description: 'Manage products, orders, and inventory', emoji: '🛍️', category: 'E-Commerce' },
  { id: 'twitter', name: 'Twitter / X', description: 'Post tweets and monitor mentions', emoji: '🐦', category: 'Social' },
  { id: 'linkedin', name: 'LinkedIn', description: 'Share posts and manage your network', emoji: '💼', category: 'Social' },
  { id: 'whatsapp', name: 'WhatsApp', description: 'Send messages and media via WhatsApp', emoji: '📱', category: 'Communication' },
];

const STORAGE_KEY = 'shunya_connectors';

const CATEGORIES = ['All', 'Communication', 'Productivity', 'Dev Tools', 'Finance', 'E-Commerce', 'Social'];

function formatTimeAgo(isoStr: string): string {
  try {
    const diff = Date.now() - new Date(isoStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  } catch {
    return 'unknown';
  }
}

function loadStates(): Record<string, ConnectorState> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Record<string, ConnectorState>;
  } catch { /* ignore */ }
  return {};
}

function saveStates(states: Record<string, ConnectorState>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(states));
  } catch { /* ignore */ }
}

// ── Mock OAuth Popup ──

function MockOAuthPopup({ connector, onDone, onCancel }: {
  connector: Connector;
  onDone: () => void;
  onCancel: () => void;
}) {
  // Auto-proceed after a short delay to simulate OAuth flow
  useEffect(() => {
    const t = setTimeout(onDone, 1800);
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <div className="ih-oauth-overlay">
      <div className="ih-oauth-panel">
        <div className="ih-oauth-header">
          <span className="ih-oauth-emoji">{connector.emoji}</span>
          <span className="ih-oauth-title">Connect {connector.name}</span>
          <button className="ih-oauth-close" onClick={onCancel} aria-label="Cancel">
            <XCircle size={16} />
          </button>
        </div>
        <div className="ih-oauth-body">
          <div className="ih-oauth-spinner" />
          <span className="ih-oauth-text">Authenticating with {connector.name}...</span>
        </div>
        <div className="ih-oauth-footer">
          <span className="ih-oauth-hint">This is a mock OAuth flow for demonstration.</span>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ──

export function IntegrationHub() {
  const [states, setStates] = useState<Record<string, ConnectorState>>(() => loadStates());
  const [filter, setFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [connectingId, setConnectingId] = useState<string | null>(null);
  const [showOAuth, setShowOAuth] = useState<string | null>(null);

  // Persist state changes
  useEffect(() => {
    saveStates(states);
  }, [states]);

  const handleConnect = useCallback((id: string) => {
    setShowOAuth(id);
  }, []);

  const handleOAuthDone = useCallback(() => {
    if (!showOAuth) return;
    setStates(prev => ({
      ...prev,
      [showOAuth]: {
        connected: true,
        error: false,
        lastSync: new Date().toISOString(),
      },
    }));
    setShowOAuth(null);
    setConnectingId(null);
  }, [showOAuth]);

  const handleOAuthCancel = useCallback(() => {
    setShowOAuth(null);
    setConnectingId(null);
  }, []);

  const handleDisconnect = useCallback((id: string) => {
    setStates(prev => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  }, []);

  const handleSync = useCallback((id: string) => {
    setConnectingId(id);
    setTimeout(() => {
      setStates(prev => ({
        ...prev,
        [id]: {
          ...prev[id],
          lastSync: new Date().toISOString(),
        },
      }));
      setConnectingId(null);
    }, 800);
  }, []);

  const filteredConnectors = CONNECTORS.filter(c => {
    const matchCategory = filter === 'All' || c.category === filter;
    const matchSearch = !searchQuery.trim() || c.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCategory && matchSearch;
  });

  const connectedCount = CONNECTORS.filter(c => states[c.id]?.connected).length;
  const errorCount = CONNECTORS.filter(c => states[c.id]?.error).length;

  return (
    <div className="ih2-container">
      {/* Header */}
      <div className="ih2-header">
        <div className="ih2-header-left">
          <div className="ih2-header-icon">
            <Zap size={18} />
          </div>
          <div>
            <div className="ih2-header-title">Integration Hub 2.0</div>
            <div className="ih2-header-sub">Connect your favorite tools and services</div>
          </div>
        </div>
        <div className="ih2-header-badges">
          <span className="ih2-badge ih2-badge-connected">
            <Plug size={10} /> {connectedCount} Connected
          </span>
          {errorCount > 0 && (
            <span className="ih2-badge ih2-badge-error">
              <AlertCircle size={10} /> {errorCount} Error
            </span>
          )}
          <span className="ih2-badge ih2-badge-total">
            {CONNECTORS.length} Total
          </span>
        </div>
      </div>

      {/* Search + Categories */}
      <div className="ih2-toolbar">
        <div className="ih2-search">
          <Search size={13} className="ih2-search-icon" />
          <input
            className="ih2-search-input"
            placeholder="Search connectors..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="ih2-categories">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              className={`ih2-cat-btn ${filter === cat ? 'ih2-cat-active' : ''}`}
              onClick={() => setFilter(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div className="ih2-grid">
        {filteredConnectors.map(conn => {
          const state = states[conn.id];
          const isConnected = state?.connected ?? false;
          const isError = state?.error ?? false;
          const isConnecting = connectingId === conn.id;
          const showOAuthNow = showOAuth === conn.id;

          return (
            <div key={conn.id} className={`ih2-card ${isConnected ? 'ih2-card-connected' : ''}`}>
              <div className="ih2-card-top">
                <span className="ih2-card-emoji">{conn.emoji}</span>
                <div className="ih2-card-info">
                  <span className="ih2-card-name">{conn.name}</span>
                  <span className="ih2-card-desc">{conn.description}</span>
                </div>
              </div>

              {/* Status */}
              <div className="ih2-card-status-row">
                {isConnected ? (
                  <span className="ih2-status ih2-status-connected">
                    <CheckCircle2 size={12} /> Connected
                  </span>
                ) : isError ? (
                  <span className="ih2-status ih2-status-error">
                    <AlertCircle size={12} /> Error
                  </span>
                ) : (
                  <span className="ih2-status ih2-status-disconnected">
                    <XCircle size={12} /> Disconnected
                  </span>
                )}
              </div>

              {/* Last sync */}
              {isConnected && state?.lastSync && (
                <div className="ih2-card-sync">
                  <Clock size={10} />
                  <span>Synced {formatTimeAgo(state.lastSync)}</span>
                </div>
              )}

              {/* Actions */}
              <div className="ih2-card-actions">
                {isConnected ? (
                  <>
                    <button
                      className="ih2-btn ih2-btn-sync"
                      onClick={() => handleSync(conn.id)}
                      disabled={isConnecting}
                    >
                      <RefreshCw size={12} className={isConnecting ? 'ih2-spin' : ''} />
                      {isConnecting ? 'Syncing...' : 'Sync'}
                    </button>
                    <button
                      className="ih2-btn ih2-btn-disconnect"
                      onClick={() => handleDisconnect(conn.id)}
                    >
                      <Unplug size={12} /> Disconnect
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      className="ih2-btn ih2-btn-connect"
                      onClick={() => handleConnect(conn.id)}
                    >
                      <ExternalLink size={12} /> Connect
                    </button>
                  </>
                )}
              </div>

              {/* Mock OAuth popup */}
              {showOAuthNow && (
                <MockOAuthPopup
                  connector={conn}
                  onDone={handleOAuthDone}
                  onCancel={handleOAuthCancel}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Empty */}
      {filteredConnectors.length === 0 && (
        <div className="ih2-empty">
          <Search size={28} style={{ opacity: 0.2, color: '#1A1C1D' }} />
          <span className="ih2-empty-text">No connectors match your criteria.</span>
          <button className="ih2-empty-btn" onClick={() => { setFilter('All'); setSearchQuery(''); }}>
            Clear Filters
          </button>
        </div>
      )}

      {/* Simulated connections disclaimer */}
      <div className="ih2-simulated-note">
        ⚡ All connections are simulated for demonstration. Real API integrations coming soon.
      </div>

      <style>{ih2Css}</style>
    </div>
  );
}

// ── Styles ──

const ih2Css = `
.ih2-container { display: flex; flex-direction: column; width: 100%; gap: 14px; padding: 18px; }

/* Header */
.ih2-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.ih2-header-left { display: flex; align-items: center; gap: 10px; }
.ih2-header-icon { width: 36px; height: 36px; border-radius: 10px; background: rgba(164,134,95,0.10); color: #A4865F; display: flex; align-items: center; justify-content: center; }
.ih2-header-title { font-size: 15px; font-weight: 600; color: #1A1C1D; }
.ih2-header-sub { font-size: 11px; color: rgba(26,28,29,0.45); margin-top: 1px; }
.ih2-header-badges { display: flex; gap: 6px; flex-wrap: wrap; }
.ih2-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 20px; font-size: 10px; font-weight: 500; }
.ih2-badge-connected { background: rgba(45,106,79,0.08); color: #2D6A4F; }
.ih2-badge-error { background: rgba(185,28,28,0.08); color: #B91C1C; }
.ih2-badge-total { background: rgba(26,28,29,0.04); color: rgba(26,28,29,0.5); }

/* Toolbar */
.ih2-toolbar { display: flex; flex-direction: column; gap: 8px; }
.ih2-search { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(255,255,255,0.5); border: 1px solid rgba(26,28,29,0.06); border-radius: 10px; }
.ih2-search-icon { color: rgba(26,28,29,0.25); flex-shrink: 0; }
.ih2-search-input { flex: 1; border: none; outline: none; background: transparent; font-size: 13px; color: #1A1C1D; font-family: inherit; }
.ih2-search-input::placeholder { color: rgba(26,28,29,0.25); }
.ih2-categories { display: flex; gap: 4px; flex-wrap: wrap; }
.ih2-cat-btn { padding: 5px 10px; border-radius: 8px; border: 1px solid transparent; background: transparent; font-size: 11px; font-family: inherit; color: rgba(26,28,29,0.45); cursor: pointer; transition: all 0.15s; }
.ih2-cat-btn:hover { border-color: rgba(26,28,29,0.06); background: rgba(255,255,255,0.4); color: #1A1C1D; }
.ih2-cat-active { background: rgba(108,74,226,0.06) !important; border-color: rgba(108,74,226,0.15) !important; color: #6C4AE2 !important; }

/* Grid */
.ih2-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px; }
.ih2-card { display: flex; flex-direction: column; gap: 10px; padding: 14px; background: rgba(255,255,255,0.5); backdrop-filter: blur(4px); border: 1px solid rgba(26,28,29,0.04); border-radius: 14px; transition: all 0.15s; position: relative; }
.ih2-card:hover { background: rgba(255,255,255,0.7); border-color: rgba(26,28,29,0.08); box-shadow: 0 2px 12px rgba(26,28,29,0.04); }
.ih2-card-connected { border-left: 3px solid #2D6A4F; }

.ih2-card-top { display: flex; gap: 10px; align-items: flex-start; }
.ih2-card-emoji { font-size: 28px; line-height: 1; flex-shrink: 0; }
.ih2-card-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.ih2-card-name { font-size: 13px; font-weight: 600; color: #1A1C1D; }
.ih2-card-desc { font-size: 10px; color: rgba(26,28,29,0.45); line-height: 1.4; }

.ih2-card-status-row { display: flex; align-items: center; gap: 8px; }
.ih2-status { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 20px; font-size: 10px; font-weight: 500; }
.ih2-status-connected { background: rgba(45,106,79,0.08); color: #2D6A4F; }
.ih2-status-error { background: rgba(185,28,28,0.08); color: #B91C1C; }
.ih2-status-disconnected { background: rgba(26,28,29,0.04); color: rgba(26,28,29,0.4); }

.ih2-card-sync { display: flex; align-items: center; gap: 5px; font-size: 10px; color: rgba(26,28,29,0.35); }

.ih2-card-actions { display: flex; gap: 6px; margin-top: auto; flex-wrap: wrap; }
.ih2-btn { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 8px; font-size: 10px; font-weight: 600; cursor: pointer; border: 1px solid; font-family: inherit; transition: all 0.15s; }
.ih2-btn:disabled { opacity: 0.5; cursor: default; }
.ih2-btn-connect { border-color: rgba(108,74,226,0.2); background: rgba(108,74,226,0.06); color: #6C4AE2; }
.ih2-btn-connect:hover:not(:disabled) { background: rgba(108,74,226,0.12); border-color: #6C4AE2; }
.ih2-btn-disconnect { border-color: rgba(185,28,28,0.15); background: rgba(185,28,28,0.04); color: #B91C1C; }
.ih2-btn-disconnect:hover:not(:disabled) { background: rgba(185,28,28,0.08); border-color: #B91C1C; }
.ih2-btn-sync { border-color: rgba(26,28,29,0.08); background: rgba(255,255,255,0.4); color: rgba(26,28,29,0.5); }
.ih2-btn-sync:hover:not(:disabled) { color: #1A1C1D; border-color: rgba(26,28,29,0.15); }

.ih2-spin { animation: ih2-rotate 0.8s linear infinite; }
@keyframes ih2-rotate { to { transform: rotate(360deg); } }

/* OAuth Popup */
.ih-oauth-overlay { position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.2); backdrop-filter: blur(2px); display: flex; align-items: center; justify-content: center; }
.ih-oauth-panel { width: 340px; background: rgba(255,255,255,0.95); backdrop-filter: blur(16px); border: 1px solid rgba(26,28,29,0.06); border-radius: 16px; box-shadow: 0 8px 40px rgba(0,0,0,0.08); display: flex; flex-direction: column; overflow: hidden; }
.ih-oauth-header { display: flex; align-items: center; gap: 8px; padding: 14px 16px; border-bottom: 1px solid rgba(26,28,29,0.04); }
.ih-oauth-emoji { font-size: 22px; }
.ih-oauth-title { font-size: 14px; font-weight: 600; color: #1A1C1D; flex: 1; }
.ih-oauth-close { background: transparent; border: none; cursor: pointer; color: rgba(26,28,29,0.3); padding: 4px; border-radius: 6px; display: flex; }
.ih-oauth-close:hover { color: #B91C1C; background: rgba(185,28,28,0.06); }
.ih-oauth-body { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 32px 16px; }
.ih-oauth-spinner { width: 28px; height: 28px; border: 3px solid rgba(108,74,226,0.12); border-top-color: #6C4AE2; border-radius: 50%; animation: ih2-rotate 0.7s linear infinite; }
.ih-oauth-text { font-size: 13px; color: rgba(26,28,29,0.6); font-weight: 500; }
.ih-oauth-footer { padding: 10px 16px; border-top: 1px solid rgba(26,28,29,0.04); display: flex; justify-content: center; }
.ih-oauth-hint { font-size: 10px; color: rgba(26,28,29,0.3); }

/* Empty */
.ih2-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 48px 20px; }
.ih2-empty-text { font-size: 13px; color: rgba(26,28,29,0.3); }
.ih2-empty-btn { padding: 6px 14px; border: 1px solid rgba(108,74,226,0.2); border-radius: 8px; background: rgba(108,74,226,0.04); font-size: 11px; font-weight: 500; color: #6C4AE2; cursor: pointer; font-family: inherit; }
.ih2-empty-btn:hover { background: rgba(108,74,226,0.1); }

.ih2-simulated-note { font-size: 11px; color: rgba(26,28,29,0.3); text-align: center; padding: 6px; border-top: 1px solid rgba(26,28,29,0.04); margin-top: 4px; }

@media (max-width: 768px) {
  .ih2-grid { grid-template-columns: 1fr; }
  .ih2-header { flex-direction: column; align-items: flex-start; }
}
`;