import { useState, useCallback, useEffect } from 'react';
import {
  IconPalette, IconSparkles, IconClipboard,
  IconAlertTriangle, IconX, IconSpeakerphone, IconArchive, IconTrash,
  IconDownload, IconInfoCircle, IconRestore, IconDotsVertical,
} from '@tabler/icons-react';

export type MediaRuntimeState =
  | 'idle'
  | 'preparing_brief'
  | 'generating'
  | 'generated'
  | 'description_only'
  | 'provider_unavailable'
  | 'failed';

export type MediaResultKind =
  | 'generated_image'
  | 'visual_concept'
  | 'provider_unavailable'
  | 'error';

export type AspectRatio = '1:1' | '4:5' | '9:16' | '16:9' | '3:2' | '4:3';
export type VisualStyle = 'realistic' | 'illustration' | 'cinematic' | 'minimalist' | 'corporate' | 'artistic';

export interface MediaAsset {
  id: number;
  identity_id: string;
  organization_id: number;
  workspace_id: string;
  runtime_state: MediaRuntimeState;
  result_kind: MediaResultKind;
  raw_prompt: string;
  visual_brief?: string;
  asset_url?: string;
  description?: string;
  platform?: string;
  aspect_ratio: string;
  visual_style: string;
  provider?: string;
  generation_job_id?: string;
  failure_reason?: string;
  campaign_id?: number;
  lifecycle_status: string;
  business_context?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
  deleted_at?: string;
  deleted_by?: string;
  archived_at?: string;
  archived_by?: string;
  restored_at?: string;
  restored_by?: string;
}

interface ProviderStatus {
  huggingface: { available: boolean; model?: string; error?: string };
}

// ── API calls ──

async function apiGenerateMedia(params: {
  prompt: string; aspect_ratio: string; visual_style: string;
  business_context?: Record<string, unknown>;
}): Promise<MediaAsset> {
  const resp = await fetch('/api/v1/media/generate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(params),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }));
    throw new Error(err.error || 'Media generation failed');
  }
  const body = await resp.json();
  if (!body.success || !body.data) throw new Error(body.error || 'Generation returned no data');
  return body.data;
}

async function apiGetAssets(): Promise<MediaAsset[]> {
  try {
    const resp = await fetch('/api/v1/media/assets', { credentials: 'include' });
    if (!resp.ok) return [];
    const body = await resp.json();
    if (!body.success) return [];
    return body.data;
  } catch { return []; }
}

async function apiLifecycleAction(assetId: number, action: string): Promise<{ ok: boolean; error?: string }> {
  try {
    const method = action === 'permanent_delete' ? 'DELETE' : 'POST';
    const resp = await fetch(`/api/v1/media/assets/${assetId}/${action}`, { method, credentials: 'include' });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }));
      return { ok: false, error: err.error };
    }
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : 'Network error' };
  }
}

async function apiGetProviderStatus(): Promise<ProviderStatus | null> {
  try {
    const resp = await fetch('/api/v1/media/status', { credentials: 'include' });
    if (!resp.ok) return null;
    const body = await resp.json();
    return body.providers;
  } catch { return null; }
}

// ── Helpers ──

function stateLabel(state: MediaRuntimeState): string {
  const labels: Record<MediaRuntimeState, string> = {
    idle: 'Ready', preparing_brief: 'Preparing…', generating: 'Generating…',
    generated: 'Generated', description_only: 'Visual concept',
    provider_unavailable: 'Unavailable', failed: 'Failed',
  };
  return labels[state];
}

// ── Main Component ──

export function MediaGenerator({ onAddToCampaign }: { onAddToCampaign?: (asset: MediaAsset) => void }) {
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('1:1');
  const [visualStyle, setVisualStyle] = useState<VisualStyle>('realistic');
  const [providerStatus, setProviderStatus] = useState<ProviderStatus | null>(null);
  const [runtimeState, setRuntimeState] = useState<MediaRuntimeState>('idle');
  const [currentAsset, setCurrentAsset] = useState<MediaAsset | null>(null);
  const [history, setHistory] = useState<MediaAsset[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [openMenuId, setOpenMenuId] = useState<number | null>(null);
  const [businessContext, setBusinessContext] = useState('');
  const [detailsAsset, setDetailsAsset] = useState<MediaAsset | null>(null);
  const [lifecycleError, setLifecycleError] = useState<string | null>(null);

  useEffect(() => {
    apiGetProviderStatus().then(setProviderStatus);
    apiGetAssets().then(setHistory);
  }, []);

  const handleLifecycle = useCallback(async (assetId: number, action: string) => {
    if (action === 'permanent_delete') {
      const ok = window.confirm(
        'Permanently delete this asset?\n\n' +
        'This action is IRREVERSIBLE. The asset will be removed and cannot be recovered.',
      );
      if (!ok) return;
    }
    setLifecycleError(null);
    setOpenMenuId(null);
    const result = await apiLifecycleAction(assetId, action);
    if (!result.ok) {
      setLifecycleError(result.error || `${action} failed`);
      return;
    }
    if (action === 'permanent_delete') {
      setHistory(prev => prev.filter(a => a.id !== assetId));
      if (currentAsset?.id === assetId) setCurrentAsset(null);
    } else {
      // Re-read from server so state matches persisted truth
      const refreshed = await apiGetAssets();
      if (refreshed) setHistory(refreshed);
    }
  }, [currentAsset]);

  const handleSelect = useCallback((asset: MediaAsset) => {
    setCurrentAsset(asset);
    setRuntimeState(asset.runtime_state);
    setPrompt(asset.raw_prompt);
    setOpenMenuId(null);
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!prompt.trim()) return;
    setRuntimeState('preparing_brief');
    setError(null);
    setCurrentAsset(null);
    let bc: Record<string, unknown> | undefined;
    if (businessContext.trim()) {
      bc = { raw_text: businessContext.trim() };
      const lines = businessContext.trim().split('\n');
      for (const line of lines) {
        const [key, ...vals] = line.split(':');
        if (vals.length > 0) bc[key.trim().toLowerCase().replace(/\s+/g, '_')] = vals.join(':').trim();
      }
    }
    try {
      const asset = await apiGenerateMedia({
        prompt: prompt.trim(), aspect_ratio: aspectRatio,
        visual_style: visualStyle, business_context: bc,
      });
      setCurrentAsset(asset);
      setRuntimeState(asset.runtime_state);
      setHistory(prev => [asset, ...prev]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      setRuntimeState('failed');
    }
  }, [prompt, aspectRatio, visualStyle, businessContext]);

  const isBusy = runtimeState === 'preparing_brief' || runtimeState === 'generating';
  const providerAvail = providerStatus?.huggingface?.available ?? false;

  // Close overflow menu when clicking outside
  useEffect(() => {
    const handler = () => setOpenMenuId(null);
    if (openMenuId !== null) {
      document.addEventListener('click', handler);
    }
    return () => document.removeEventListener('click', handler);
  }, [openMenuId]);

  function lifecycleActions(asset: MediaAsset): { action: string; label: string; icon: React.ReactNode }[] {
    const state = asset.lifecycle_status || 'active';
    switch (state) {
      case 'active':
        return [
          { action: 'download', label: 'Download', icon: <IconDownload size={14} /> },
          { action: 'details', label: 'Details', icon: <IconInfoCircle size={14} /> },
          { action: 'archive', label: 'Archive', icon: <IconArchive size={14} /> },
          { action: 'trash', label: 'Move to Trash', icon: <IconTrash size={14} /> },
        ];
      case 'archived':
        return [
          { action: 'download', label: 'Download', icon: <IconDownload size={14} /> },
          { action: 'details', label: 'Details', icon: <IconInfoCircle size={14} /> },
          { action: 'restore', label: 'Restore', icon: <IconRestore size={14} /> },
          { action: 'trash', label: 'Move to Trash', icon: <IconTrash size={14} /> },
        ];
      case 'trashed':
        return [
          { action: 'details', label: 'Details', icon: <IconInfoCircle size={14} /> },
          { action: 'restore', label: 'Restore', icon: <IconRestore size={14} /> },
          { action: 'permanent_delete', label: 'Delete Permanently', icon: <IconX size={14} /> },
        ];
      default:
        return [{ action: 'details', label: 'Details', icon: <IconInfoCircle size={14} /> }];
    }
  }

  // ── Render ──
  return (
    <div className="cs-media-gen">
      {/* ── Lifecycle error ── */}
      {lifecycleError && (
        <div className="cs-lifecycle-error" role="alert">
          <IconAlertTriangle size={13} />
          <span>{lifecycleError}</span>
          <button className="cs-lifecycle-error-dismiss" onClick={() => setLifecycleError(null)}
            aria-label="Dismiss error">×</button>
        </div>
      )}

      {/* ── Error display ── */}
      {error && (
        <div className="cs-media-error">
          <IconAlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* ── Result hero ── */}
      {(currentAsset && (runtimeState === 'generated' || runtimeState === 'description_only')) ? (
        <div className="cs-media-result-hero">
          {runtimeState === 'generated' && currentAsset.asset_url ? (
            <div className="cs-media-image-container" style={{ aspectRatio: currentAsset.aspect_ratio.replace(':', '/') }}>
              <img src={currentAsset.asset_url} alt={currentAsset.raw_prompt}
                className="cs-media-image" />
              <span className="cs-media-badge">{currentAsset.provider || 'generated'}</span>
            </div>
          ) : (
            <div className="cs-media-concept-container">
              <div className="cs-media-concept-card">
                <div className="cs-media-concept-icon">🎨</div>
                <h3 className="cs-media-concept-title">Visual Concept</h3>
                <p className="cs-media-concept-desc">{currentAsset.description || currentAsset.raw_prompt}</p>
                {currentAsset.failure_reason && (
                  <p className="cs-media-concept-desc" style={{ color: '#991b1b' }}>{currentAsset.failure_reason}</p>
                )}
              </div>
            </div>
          )}
          <div className="cs-media-meta-bar">
            <span>Prompt: {currentAsset.raw_prompt}</span>
            {currentAsset.aspect_ratio && <span>Ratio: {currentAsset.aspect_ratio}</span>}
            {currentAsset.visual_style && <span>Style: {currentAsset.visual_style}</span>}
            {currentAsset.provider && <span>Provider: {currentAsset.provider}</span>}
            <span>Lifecycle: {currentAsset.lifecycle_status || 'active'}</span>
          </div>
          <div className="cs-media-result-actions">
            {currentAsset.asset_url && (
              <a className="cs-btn cs-btn-secondary" href={currentAsset.asset_url} download target="_blank" rel="noopener">
                <IconDownload size={14} /> Download
              </a>
            )}
            {onAddToCampaign && (
              <button className="cs-btn cs-btn-secondary" onClick={() => onAddToCampaign(currentAsset)}>
                <IconSpeakerphone size={14} /> Add to Campaign
              </button>
            )}
          </div>
        </div>
      ) : null}

      {/* ── Provider unavailable / failed display ── */}
      {(runtimeState === 'provider_unavailable') && (
        <div className="cs-media-error-block">
          <IconAlertTriangle size={20} />
          <p className="cs-state-title">Provider unavailable</p>
          <p className="cs-state-desc">The media generation provider is not currently available. Try again later.</p>
        </div>
      )}

      {/* ── Provider unavailable / failed display ── */}
      {(runtimeState === 'failed' && !currentAsset) && (
        <div className="cs-media-error-block">
          <IconX size={20} />
          <p className="cs-state-title">Generation failed</p>
          <p className="cs-state-desc">{error || 'Media generation failed. Please try again.'}</p>
        </div>
      )}

      {/* ── Controls ── */}
      {runtimeState === 'generated' || runtimeState === 'description_only' ? (
        <details className="cs-media-controls-toggle" open={false}>
          <summary>Generation controls</summary>
          <div className="cs-media-controls-panel">{renderControls()}</div>
        </details>
      ) : runtimeState !== 'provider_unavailable' && runtimeState !== 'failed' ? (
        <div className="cs-media-controls-panel">{renderControls()}</div>
      ) : null}

      {/* ── History ── */}
      {history.length > 0 && (
        <div className="cs-media-history">
          <div className="cs-media-history-header">
            <h4 className="cs-media-history-title">Generated Assets</h4>
            {lifecycleError && (
              <span className="cs-media-history-error">{lifecycleError}</span>
            )}
          </div>
          <div className="cs-media-history-grid">
            {history.map(asset => {
              const lcState = asset.lifecycle_status || 'active';
              const isTrashed = lcState === 'trashed';
              return (
                <div key={asset.id}
                  className={`cs-media-history-card ${currentAsset?.id === asset.id ? 'cs-history-active' : ''} ${isTrashed ? 'cs-history-trashed' : ''}`}
                  onClick={() => handleSelect(asset)}>
                  {asset.asset_url ? (
                    <img src={asset.asset_url} alt="" className="cs-history-thumb" />
                  ) : (
                    <div className="cs-history-thumb cs-history-placeholder">
                      <span>{asset.result_kind === 'visual_concept' ? <IconClipboard size={24} /> : <IconPalette size={24} />}</span>
                    </div>
                  )}
                  <div className="cs-history-meta">
                    <span className="cs-history-label">{asset.raw_prompt.slice(0, 30)}</span>
                    <span className={`cs-history-state cs-state-${asset.runtime_state}`}>
                      {stateLabel(asset.runtime_state)}
                    </span>
                    {isTrashed && <span className="cs-history-trashed-badge">Trashed</span>}
                  </div>
                  {/* State-aware overflow menu */}
                  <div className="cs-history-overflow" onClick={e => { e.stopPropagation(); setOpenMenuId(openMenuId === asset.id ? null : asset.id); }}>
                    <button className="cs-history-overflow-btn" title="Actions" aria-label="Asset actions">
                      <IconDotsVertical size={14} />
                    </button>
                    {openMenuId === asset.id && (
                      <div className="cs-history-menu" onClick={e => e.stopPropagation()}>
                        {lifecycleActions(asset).map(item => (
                          item.action === 'trash' || item.action === 'permanent_delete' ? (
                            <button key={item.action} className="cs-history-menu-item cs-menu-item-danger"
                              onClick={() => handleLifecycle(asset.id, item.action)}>
                              {item.icon} {item.label}
                            </button>
                          ) : item.action === 'details' ? (
                            <button key={item.action} className="cs-history-menu-item"
                              onClick={() => setDetailsAsset(asset)}>
                              {item.icon} {item.label}
                            </button>
                          ) : item.action === 'download' ? (
                            <a key={item.action} className="cs-history-menu-item" href={asset.asset_url || '#'}
                              download target="_blank" rel="noopener"
                              onClick={() => setOpenMenuId(null)}
                              style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 6 }}>
                              {item.icon} {item.label}
                            </a>
                          ) : (
                            <button key={item.action} className="cs-history-menu-item"
                              onClick={() => handleLifecycle(asset.id, item.action)}>
                              {item.icon} {item.label}
                            </button>
                          )
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Details modal ── */}
      {detailsAsset && (
        <div className="cs-modal-overlay" onClick={() => setDetailsAsset(null)} role="dialog" aria-modal="true">
          <div className="cs-modal" onClick={e => e.stopPropagation()}>
            <div className="cs-modal-header">
              <h3 className="cs-modal-title">Asset Details</h3>
              <button className="cs-modal-close" onClick={() => setDetailsAsset(null)}>×</button>
            </div>
            <div className="cs-modal-body">
              {detailsAsset.asset_url && (
                <img src={detailsAsset.asset_url} alt="" className="cs-details-image" />
              )}
              <dl className="cs-details-list">
                <dt>Name</dt><dd>{detailsAsset.raw_prompt}</dd>
                <dt>Type</dt><dd>{detailsAsset.result_kind || 'N/A'}</dd>
                <dt>Runtime State</dt><dd>{detailsAsset.runtime_state}</dd>
                <dt>Lifecycle</dt><dd>{detailsAsset.lifecycle_status || 'active'}</dd>
                <dt>Aspect Ratio</dt><dd>{detailsAsset.aspect_ratio || 'N/A'}</dd>
                <dt>Visual Style</dt><dd>{detailsAsset.visual_style || 'N/A'}</dd>
                <dt>Provider</dt><dd>{detailsAsset.provider || 'N/A'}</dd>
                <dt>Created</dt><dd>{detailsAsset.created_at ? new Date(detailsAsset.created_at).toLocaleString() : 'N/A'}</dd>
                {detailsAsset.description && <><dt>Description</dt><dd>{detailsAsset.description}</dd></>}
                {detailsAsset.failure_reason && <><dt>Failure</dt><dd>{detailsAsset.failure_reason}</dd></>}
                {detailsAsset.archived_at && <><dt>Archived</dt><dd>{new Date(detailsAsset.archived_at).toLocaleString()}</dd></>}
                {detailsAsset.deleted_at && <><dt>Trashed</dt><dd>{new Date(detailsAsset.deleted_at).toLocaleString()}</dd></>}
                {detailsAsset.restored_at && <><dt>Restored</dt><dd>{new Date(detailsAsset.restored_at).toLocaleString()}</dd></>}
              </dl>
            </div>
          </div>
        </div>
      )}

      <style>{`
.cs-media-gen { display: flex; flex-direction: column; gap: 16px; }
.cs-media-result-hero { animation: csFadeIn 0.3s ease-out; }
.cs-media-image-container { width: 100%; max-height: 70vh; background: linear-gradient(135deg, #f0ede8 0%, #e8e4de 100%); border-radius: 12px; overflow: hidden; position: relative; display: flex; align-items: center; justify-content: center; }
.cs-media-image { width: 100%; height: 100%; object-fit: contain; display: block; }
.cs-media-badge { position: absolute; top: 12px; left: 12px; background: rgba(0,0,0,0.65); color: #fff; font-size: 11px; font-weight: 500; padding: 4px 10px; border-radius: 4px; letter-spacing: 0.3px; }
.cs-media-concept-container { width: 100%; }
.cs-media-concept-card { width: 100%; background: linear-gradient(135deg, #f8f6f1 0%, #f0ede8 100%); border: 2px dashed #d4d0c8; border-radius: 12px; display: flex; flex-direction: column; align-items: center; text-align: center; padding: 40px 24px; gap: 8px; }
.cs-media-meta-bar { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 12px; color: var(--shunya-text-secondary, rgba(26,28,29,0.45)); }
.cs-media-result-actions { display: flex; gap: 8px; }
.cs-media-error { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: rgba(185,28,28,0.08); border-radius: 8px; color: #991b1b; font-size: 13px; }
.cs-media-error-block { text-align: center; padding: 40px 24px; display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--shunya-text-secondary, rgba(26,28,29,0.55)); }

/* Lifecycle error */
.cs-lifecycle-error { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(185,28,28,0.08); border-radius: 6px; font-size: 12px; color: #991b1b; }
.cs-lifecycle-error-dismiss { margin-left: auto; background: none; border: none; cursor: pointer; font-size: 16px; color: #991b1b; padding: 0 4px; }

/* Controls */
.cs-media-controls-toggle summary { cursor: pointer; font-size: 12px; color: var(--shunya-color-accent, #6C4AE2); margin-top: 4px; }
.cs-media-controls-panel { display: flex; flex-direction: column; gap: 12px; padding: 16px; background: var(--shunya-surface-2, #f8f6f1); border-radius: 10px; }

.cs-field { display: flex; flex-direction: column; gap: 4px; }
.cs-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: var(--shunya-text-secondary, rgba(26,28,29,0.45)); }
.cs-textarea { width: 100%; min-height: 64px; padding: 10px 12px; border: 1px solid var(--shunya-surface-1, #e8e4de); border-radius: 6px; background: var(--shunya-surface, #fff); font-size: 13px; font-family: inherit; resize: vertical; box-sizing: border-box; }
.cs-textarea:focus { outline: none; border-color: var(--shunya-color-accent, #6C4AE2); }
.cs-input { width: 100%; padding: 8px 10px; border: 1px solid var(--shunya-surface-1, #e8e4de); border-radius: 6px; background: var(--shunya-surface, #fff); font-size: 12px; font-family: inherit; box-sizing: border-box; }
.cs-input:focus { outline: none; border-color: var(--shunya-color-accent, #6C4AE2); }
.cs-select-group { display: flex; gap: 8px; }
.cs-select-group .cs-field { flex: 1; }

/* Buttons */
.cs-btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; font-family: inherit; transition: background 0.1s ease; }
.cs-btn-primary { background: var(--shunya-color-accent, #6C4AE2); color: #fff; }
.cs-btn-primary:hover { background: #5a3bc9; }
.cs-btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.cs-btn-secondary { background: var(--shunya-surface-1, #e8e4de); color: var(--shunya-text, #1A1C1D); }
.cs-btn-secondary:hover { background: #d4d0c8; text-decoration: none; }

/* History */
.cs-media-history-header { display: flex; align-items: center; gap: 8px; }
.cs-media-history-title { font-size: 13px; font-weight: 600; margin: 0; color: var(--shunya-text, #1A1C1D); }
.cs-media-history-error { font-size: 11px; color: #991b1b; }
.cs-media-history-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }
.cs-media-history-card { background: var(--shunya-surface, #fff); border: 1px solid var(--shunya-surface-1, #e8e4de); border-radius: 8px; overflow: hidden; cursor: pointer; transition: border-color 0.15s ease; position: relative; }
.cs-media-history-card:hover { border-color: var(--shunya-color-accent, #6C4AE2); }
.cs-history-active { border-color: var(--shunya-color-accent, #6C4AE2); box-shadow: 0 0 0 2px rgba(108,74,226,0.15); }
.cs-history-trashed { opacity: 0.55; }
.cs-history-thumb { width: 100%; aspect-ratio: 1; object-fit: cover; display: block; }
.cs-history-placeholder { display: flex; align-items: center; justify-content: center; font-size: 24px; background: var(--shunya-surface-2, #f0ede8); }
.cs-history-meta { padding: 6px 8px; display: flex; flex-direction: column; gap: 2px; }
.cs-history-label { font-size: 10px; color: var(--shunya-text, #1A1C1D); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cs-history-state { font-size: 9px; text-transform: uppercase; letter-spacing: 0.3px; padding: 1px 6px; border-radius: 3px; display: inline-block; width: fit-content; }
.cs-history-trashed-badge { font-size: 9px; text-transform: uppercase; letter-spacing: 0.3px; padding: 1px 6px; border-radius: 3px; background: rgba(185,28,28,0.1); color: #991b1b; display: inline-block; width: fit-content; }
.cs-state-generated { background: rgba(34,197,94,0.12); color: #15803D; }
.cs-state-description_only { background: rgba(108,74,226,0.1); color: #5a3bc9; }
.cs-state-failed { background: rgba(185,28,28,0.1); color: #991b1b; }

/* Overflow menu */
.cs-history-overflow { position: absolute; top: 4px; right: 4px; z-index: 10; }
.cs-history-overflow-btn { display: flex; align-items: center; justify-content: center; width: 26px; height: 26px; border: none; border-radius: 6px; background: rgba(255,255,255,0.85); color: var(--shunya-text-secondary, rgba(26,28,29,0.55)); cursor: pointer; backdrop-filter: blur(4px); transition: background 0.1s ease, color 0.1s ease; }
.cs-history-overflow-btn:hover { background: rgba(255,255,255,0.95); color: var(--shunya-text, #1A1C1D); }
.cs-history-menu { position: absolute; top: 100%; right: 0; margin-top: 2px; background: #fff; border: 1px solid var(--shunya-surface-1, #e8e4de); border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); min-width: 160px; padding: 4px; z-index: 100; }
.cs-history-menu-item { display: flex; align-items: center; gap: 6px; width: 100%; padding: 7px 10px; border: none; background: none; font-size: 12px; color: var(--shunya-text, #1A1C1D); cursor: pointer; border-radius: 4px; font-family: inherit; white-space: nowrap; }
.cs-history-menu-item:hover { background: var(--shunya-surface-2, #f0ede8); }
.cs-menu-item-danger { color: #991b1b; }
.cs-menu-item-danger:hover { background: rgba(185,28,28,0.08); }

/* Details modal */
.cs-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.cs-modal { background: #fff; border-radius: 12px; max-width: 520px; width: 100%; max-height: 80vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.cs-modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--shunya-surface-1, #e8e4de); }
.cs-modal-title { font-size: 15px; font-weight: 600; margin: 0; color: var(--shunya-text, #1A1C1D); }
.cs-modal-close { background: none; border: none; font-size: 20px; cursor: pointer; color: var(--shunya-text-secondary, rgba(26,28,29,0.45)); padding: 0 4px; }
.cs-modal-body { padding: 20px; }
.cs-details-image { width: 100%; border-radius: 8px; margin-bottom: 16px; }
.cs-details-list { display: grid; grid-template-columns: auto 1fr; gap: 8px 16px; font-size: 13px; }
.cs-details-list dt { color: var(--shunya-text-secondary, rgba(26,28,29,0.55)); font-weight: 500; }
.cs-details-list dd { margin: 0; color: var(--shunya-text, #1A1C1D); word-break: break-all; }

@keyframes csFadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 600px) {
  .cs-media-image-container, .cs-media-concept-card { border-radius: 8px; }
  .cs-media-concept-card { padding: 24px 16px; }
  .cs-select-group { flex-direction: column; }
  .cs-media-history-grid { grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); }
}
      `}</style>
    </div>
  );

  function renderControls() {
    return (
      <>
        <div className="cs-field">
          <label className="cs-label">What do you want to create?</label>
          <textarea className="cs-textarea" value={prompt} onChange={e => setPrompt(e.target.value)}
            placeholder="e.g., A modern beach resort in Bali at sunset with infinity pool" rows={3} disabled={isBusy} />
        </div>
        <div className="cs-select-group">
          <div className="cs-field">
            <label className="cs-label">Aspect Ratio</label>
            <select className="cs-input" value={aspectRatio} onChange={e => setAspectRatio(e.target.value as AspectRatio)}>
              {ASPECT_RATIOS.map(ar => <option key={ar.value} value={ar.value}>{ar.label}</option>)}
            </select>
          </div>
          <div className="cs-field">
            <label className="cs-label">Visual Style</label>
            <select className="cs-input" value={visualStyle} onChange={e => setVisualStyle(e.target.value as VisualStyle)}>
              {VISUAL_STYLES.map(vs => <option key={vs.value} value={vs.value}>{vs.label}</option>)}
            </select>
          </div>
        </div>
        <div className="cs-field">
          <label className="cs-label">Business Context (optional)</label>
          <textarea className="cs-textarea" value={businessContext} onChange={e => setBusinessContext(e.target.value)}
            placeholder="Client: Bali Resort&#10;Location: Uluwatu&#10;Season: Summer&#10;Target audience: Luxury travelers" rows={2} disabled={isBusy} />
        </div>
        {!providerAvail && (
          <div className="cs-media-error" style={{ fontSize: 12 }}>
            <IconAlertTriangle size={13} />
            <span>Media generation provider unavailable. Generation may fail.</span>
          </div>
        )}
        <button className="cs-btn cs-btn-primary" onClick={handleGenerate} disabled={!prompt.trim()}>
          <IconSparkles size={14} /> {isBusy ? 'Generating…' : 'Generate'}
        </button>
      </>
    );
  }
}

const ASPECT_RATIOS: { value: AspectRatio; label: string }[] = [
  { value: '1:1', label: 'Square 1:1' }, { value: '4:5', label: 'Portrait 4:5' },
  { value: '9:16', label: 'Story 9:16' }, { value: '16:9', label: 'Landscape 16:9' },
  { value: '3:2', label: 'Photo 3:2' }, { value: '4:3', label: 'Display 4:3' },
];

const VISUAL_STYLES: { value: VisualStyle; label: string }[] = [
  { value: 'realistic', label: 'Realistic' }, { value: 'illustration', label: 'Illustration' },
  { value: 'cinematic', label: 'Cinematic' }, { value: 'minimalist', label: 'Minimalist' },
  { value: 'corporate', label: 'Corporate' }, { value: 'artistic', label: 'Artistic' },
];