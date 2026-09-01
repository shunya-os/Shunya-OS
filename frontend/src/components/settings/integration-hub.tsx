/**
 * Integration Hub — Real backend API integration.
 *
 * Fetches providers and configs from /api/v1/integration/* instead of
 * mock localStorage. Handles loading, empty, error, and disconnected states.
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

interface Provider {
  id: string;
  name: string;
  type: string;
  icon: string;
  description: string;
  free: boolean;
  category: string;
  docs_url: string;
}

interface Config {
  id: number;
  identity_id: string;
  provider: string;
  label: string;
  is_active: boolean;
  has_config: boolean;
  created_at: string | null;
  updated_at: string | null;
}

// ── API helpers (follow api.client.ts pattern) ──

const BASE = '/api/v1/integration';

async function apiReq<T>(path: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts?.headers },
    credentials: 'include',
    ...opts,
  });
  if (r.status >= 500) {
    throw new Error(`Server error (${r.status}). Please try again.`);
  }
  return r.json() as Promise<T>;
}

async function fetchProviders(): Promise<Provider[]> {
  const res = await apiReq<{ success: boolean; data: Provider[] }>('/providers');
  return res.data ?? [];
}

async function fetchConfigs(): Promise<Config[]> {
  const res = await apiReq<{ success: boolean; data: Config[] }>('/configs');
  return res.data ?? [];
}

async function connectProvider(provider: string): Promise<Config> {
  const res = await apiReq<{ success: boolean; data: Config }>(
    `/configs/${encodeURIComponent(provider)}`,
    {
      method: 'PUT',
      body: JSON.stringify({
        config_value: 'connected_via_hub',
        label: provider,
      }),
    },
  );
  return res.data;
}

async function disconnectProvider(provider: string): Promise<void> {
  await apiReq<{ success: boolean }>(
    `/configs/${encodeURIComponent(provider)}`,
    { method: 'DELETE' },
  );
}

async function syncProvider(): Promise<void> {
  // Trigger sync via the integrations v2 endpoint
  await apiReq<{ results: unknown[] }>('/../integrations/sync', {
    method: 'POST',
  });
}

// ── Constants ──

const CATEGORIES = ['All', 'Media & Design', 'AI & Content', 'Developer Tools', 'Data & Analytics', 'Communication', 'Productivity', 'Finance', 'Other'];

// ── Helpers ──

function formatTimeAgo(isoStr: string | null | undefined): string {
  if (!isoStr) return 'never';
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

function getCategory(providerType: string): string {
  const mapping: Record<string, string> = {
    stock_media: 'Media & Design',
    ai_content: 'AI & Content',
    developer_tools: 'Developer Tools',
    data_analytics: 'Data & Analytics',
    communication: 'Communication',
    productivity: 'Productivity',
    finance: 'Finance',
  };
  return mapping[providerType] || 'Other';
}

function getProviderIcon(icon: string): string {
  // Backend returns emoji icons, use as-is
  return icon || '🔌';
}

// ── Main Component ──

export function IntegrationHub() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [configs, setConfigs] = useState<Config[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [actionProvider, setActionProvider] = useState<string | null>(null);
  const [syncProviderId, setSyncProviderId] = useState<string | null>(null);

  // Build a lookup map: provider id -> Config
  const configMap = new Map<string, Config>();
  configs.forEach(c => configMap.set(c.provider, c));

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [prov, confs] = await Promise.all([
        fetchProviders(),
        fetchConfigs(),
      ]);
      setProviders(prov);
      setConfigs(confs);
    } catch (err: any) {
      setError(err?.message || 'Failed to load integrations');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleConnect = useCallback(async (providerId: string) => {
    setActionProvider(providerId);
    try {
      const cfg = await connectProvider(providerId);
      setConfigs(prev => {
        const next = prev.filter(c => c.provider !== providerId);
        next.push(cfg);
        return next;
      });
    } catch (err: any) {
      setError(err?.message || 'Failed to connect');
    } finally {
      setActionProvider(null);
    }
  }, []);

  const handleDisconnect = useCallback(async (providerId: string) => {
    setActionProvider(providerId);
    try {
      await disconnectProvider(providerId);
      setConfigs(prev => prev.filter(c => c.provider !== providerId));
    } catch (err: any) {
      setError(err?.message || 'Failed to disconnect');
    } finally {
      setActionProvider(null);
    }
  }, []);

  const handleSync = useCallback(async () => {
    // Use the provider that triggered the sync
    setSyncProviderId(actionProvider);
    try {
      await syncProvider();
      // Refresh configs to get updated timestamps
      const confs = await fetchConfigs();
      setConfigs(confs);
    } catch (err: any) {
      setError(err?.message || 'Failed to sync');
    } finally {
      setSyncProviderId(null);
    }
  }, []);

  // Filter and merge providers with config status
  const filteredProviders = providers.filter(p => {
    const matchCategory = filter === 'All' || getCategory(p.type) === filter || p.category === filter;
    const matchSearch = !searchQuery.trim()
      || p.name.toLowerCase().includes(searchQuery.toLowerCase())
      || p.description.toLowerCase().includes(searchQuery.toLowerCase())
      || p.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCategory && matchSearch;
  });

  const connectedCount = configs.filter(c => c.is_active).length;
  const errorState = error !== null;

  return (
    <div className="ih2-container">
      {/* Header */}
      <div className="ih2-header">
        <div className="ih2-header-left">
          <div className="ih2-header-icon">
            <Zap size={18} />
          </div>
          <div>
            <div className="ih2-header-title">Integration Hub</div>
            <div className="ih2-header-sub">Connect your favorite tools and services</div>
          </div>
        </div>
        <div className="ih2-header-badges">
          <span className="ih2-badge ih2-badge-connected">
            <Plug size={10} /> {connectedCount} Connected
          </span>
          {errorState && (
            <span className="ih2-badge ih2-badge-error">
              <AlertCircle size={10} /> Error
            </span>
          )}
          <span className="ih2-badge ih2-badge-total">
            {providers.length} Available
          </span>
          <button className="ih2-refresh-btn" onClick={loadData} disabled={loading} title="Refresh">
            <RefreshCw size={12} className={loading ? 'ih2-spin' : ''} />
          </button>
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

      {/* Loading */}
      {loading && (
        <div className="ih2-status-block">
          <div className="ih2-loading-spinner" />
          <span className="ih2-status-text">Loading integrations...</span>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="ih2-status-block">
          <AlertCircle size={20} style={{ color: '#B91C1C', opacity: 0.6 }} />
          <span className="ih2-status-text" style={{ color: '#B91C1C' }}>{error}</span>
          <button className="ih2-retry-btn" onClick={loadData}>Retry</button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && filteredProviders.length === 0 && (
        <div className="ih2-empty">
          <Search size={28} style={{ opacity: 0.2, color: '#1A1C1D' }} />
          <span className="ih2-empty-text">
            {providers.length === 0
              ? 'No integrations available from the backend.'
              : 'No connectors match your criteria.'}
          </span>
          {providers.length === 0 && (
            <button className="ih2-empty-btn" onClick={loadData}>Try Again</button>
          )}
          {providers.length > 0 && (
            <button className="ih2-empty-btn" onClick={() => { setFilter('All'); setSearchQuery(''); }}>
              Clear Filters
            </button>
          )}
        </div>
      )}

      {/* Grid */}
      {!loading && !error && filteredProviders.length > 0 && (
        <div className="ih2-grid">
          {filteredProviders.map(prov => {
            const cfg = configMap.get(prov.id);
            const isConnected = cfg?.is_active ?? false;
            const isBusy = actionProvider === prov.id;
            const isSyncing = syncProviderId === prov.id;
            const lastSync = cfg?.updated_at ?? cfg?.created_at ?? null;

            return (
              <div key={prov.id} className={`ih2-card ${isConnected ? 'ih2-card-connected' : ''}`}>
                <div className="ih2-card-top">
                  <span className="ih2-card-emoji">{getProviderIcon(prov.icon)}</span>
                  <div className="ih2-card-info">
                    <span className="ih2-card-name">{prov.name}</span>
                    <span className="ih2-card-desc">{prov.description}</span>
                    {prov.free && <span className="ih2-card-free-badge">Free</span>}
                  </div>
                </div>

                {/* Status + Category */}
                <div className="ih2-card-status-row">
                  {isConnected ? (
                    <span className="ih2-status ih2-status-connected">
                      <CheckCircle2 size={12} /> Connected
                    </span>
                  ) : (
                    <span className="ih2-status ih2-status-disconnected">
                      <XCircle size={12} /> Disconnected
                    </span>
                  )}
                  <span className="ih2-card-cat-badge">{getCategory(prov.type)}</span>
                </div>

                {/* Last sync */}
                {isConnected && lastSync && (
                  <div className="ih2-card-sync">
                    <Clock size={10} />
                    <span>Synced {formatTimeAgo(lastSync)}</span>
                  </div>
                )}

                {/* Actions */}
                <div className="ih2-card-actions">
                  {isConnected ? (
                    <>
                      <button
                        className="ih2-btn ih2-btn-sync"
                        onClick={() => handleSync()}
                        disabled={isBusy || isSyncing}
                      >
                        <RefreshCw size={12} className={isSyncing ? 'ih2-spin' : ''} />
                        {isSyncing ? 'Syncing...' : 'Sync'}
                      </button>
                      <button
                        className="ih2-btn ih2-btn-disconnect"
                        onClick={() => handleDisconnect(prov.id)}
                        disabled={isBusy || isSyncing}
                      >
                        <Unplug size={12} />
                        {isBusy ? 'Disconnecting...' : 'Disconnect'}
                      </button>
                    </>
                  ) : (
                    <button
                      className="ih2-btn ih2-btn-connect"
                      onClick={() => handleConnect(prov.id)}
                      disabled={isBusy || isSyncing}
                    >
                      <ExternalLink size={12} />
                      {isBusy ? 'Connecting...' : 'Connect'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

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
.ih2-header-badges { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.ih2-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 20px; font-size: 10px; font-weight: 500; }
.ih2-badge-connected { background: rgba(45,106,79,0.08); color: #2D6A4F; }
.ih2-badge-error { background: rgba(185,28,28,0.08); color: #B91C1C; }
.ih2-badge-total { background: rgba(26,28,29,0.04); color: rgba(26,28,29,0.5); }
.ih2-refresh-btn { display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 8px; border: 1px solid rgba(26,28,29,0.08); background: transparent; color: rgba(26,28,29,0.45); cursor: pointer; font-family: inherit; transition: all 0.15s; padding: 0; }
.ih2-refresh-btn:hover { color: #1A1C1D; border-color: rgba(26,28,29,0.15); }
.ih2-refresh-btn:disabled { opacity: 0.5; cursor: default; }

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

/* Loading / Error blocks */
.ih2-status-block { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 48px 20px; }
.ih2-loading-spinner { width: 28px; height: 28px; border: 3px solid rgba(108,74,226,0.12); border-top-color: #6C4AE2; border-radius: 50%; animation: ih2-rotate 0.7s linear infinite; }
.ih2-status-text { font-size: 13px; color: rgba(26,28,29,0.55); }
.ih2-retry-btn { padding: 6px 14px; border: 1px solid rgba(108,74,226,0.2); border-radius: 8px; background: rgba(108,74,226,0.04); font-size: 11px; font-weight: 500; color: #6C4AE2; cursor: pointer; font-family: inherit; }
.ih2-retry-btn:hover { background: rgba(108,74,226,0.1); }

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
.ih2-card-free-badge { font-size: 9px; font-weight: 600; color: #2D6A4F; background: rgba(45,106,79,0.08); padding: 1px 6px; border-radius: 4px; display: inline-block; width: fit-content; margin-top: 2px; }

.ih2-card-status-row { display: flex; align-items: center; gap: 8px; }
.ih2-status { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 20px; font-size: 10px; font-weight: 500; }
.ih2-status-connected { background: rgba(45,106,79,0.08); color: #2D6A4F; }
.ih2-status-error { background: rgba(185,28,28,0.08); color: #B91C1C; }
.ih2-status-disconnected { background: rgba(26,28,29,0.04); color: rgba(26,28,29,0.4); }
.ih2-card-cat-badge { font-size: 9px; font-weight: 500; color: rgba(26,28,29,0.35); padding: 2px 6px; border-radius: 4px; background: rgba(26,28,29,0.03); margin-left: auto; }

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

/* Empty */
.ih2-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 48px 20px; }
.ih2-empty-text { font-size: 13px; color: rgba(26,28,29,0.3); }
.ih2-empty-btn { padding: 6px 14px; border: 1px solid rgba(108,74,226,0.2); border-radius: 8px; background: rgba(108,74,226,0.04); font-size: 11px; font-weight: 500; color: #6C4AE2; cursor: pointer; font-family: inherit; }
.ih2-empty-btn:hover { background: rgba(108,74,226,0.1); }

@media (max-width: 768px) {
  .ih2-grid { grid-template-columns: 1fr; }
  .ih2-header { flex-direction: column; align-items: flex-start; }
}
`;