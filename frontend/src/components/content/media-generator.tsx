/**
 * MediaGenerator — Truthful media generation panel for Content Studio.
 *
 * Canonical runtime state model:
 *   IDLE | PREPARING_BRIEF | GENERATING | GENERATED | DESCRIPTION_ONLY | PROVIDER_UNAVAILABLE | FAILED
 *
 * No GENERATED state without a real image asset.
 * DESCRIPTION_ONLY is a fundamentally different result, presented as "Visual Concept."
 * No placeholder impersonates generated content.
 */
import { useState, useCallback, useEffect } from 'react';

// ── Canonical Types ──────────────────────────────────────────

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
  | 'error'
  | null;

export type AspectRatio = '1:1' | '4:5' | '9:16' | '16:9' | '3:2' | '4:3';
export type VisualStyle = 'realistic' | 'illustration' | 'cinematic' | 'minimalist' | 'corporate' | 'artistic';

interface MediaAsset {
  id: number;
  runtime_state: MediaRuntimeState;
  result_kind: MediaResultKind;
  raw_prompt: string;
  visual_brief: string | null;
  asset_url: string | null;
  description: string | null;
  platform: string | null;
  aspect_ratio: string;
  visual_style: string;
  provider: string | null;
  generation_job_id: string | null;
  failure_reason: string | null;
  campaign_id: number | null;
  created_at: string;
  updated_at: string;
}

interface ProviderStatus {
  huggingface: {
    available: boolean;
    model: string;
    cost: string;
    error?: string;
  };
}

const ASPECT_RATIOS: { value: AspectRatio; label: string }[] = [
  { value: '1:1', label: 'Square 1:1' },
  { value: '4:5', label: 'Portrait 4:5' },
  { value: '9:16', label: 'Story 9:16' },
  { value: '16:9', label: 'Landscape 16:9' },
  { value: '3:2', label: 'Photo 3:2' },
  { value: '4:3', label: 'Display 4:3' },
];

const VISUAL_STYLES: { value: VisualStyle; label: string }[] = [
  { value: 'realistic', label: 'Realistic' },
  { value: 'illustration', label: 'Illustration' },
  { value: 'cinematic', label: 'Cinematic' },
  { value: 'minimalist', label: 'Minimalist' },
  { value: 'corporate', label: 'Corporate' },
  { value: 'artistic', label: 'Artistic' },
];

// ── API call ──────────────────────────────────────────────────

async function apiGenerateMedia(params: {
  prompt: string;
  aspect_ratio: string;
  visual_style: string;
  business_context?: Record<string, unknown>;
}): Promise<MediaAsset> {
  const resp = await fetch('/api/v1/media/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(params),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }));
    throw new Error(err.error || 'Media generation failed');
  }
  const body = await resp.json();
  if (!body.success || !body.data) {
    throw new Error(body.error || 'Generation returned no data');
  }
  return body.data;
}

async function apiGetAssets(): Promise<MediaAsset[]> {
  try {
    const resp = await fetch('/api/v1/media/assets', {
      credentials: 'include',
    });
    if (!resp.ok) return [];
    const body = await resp.json();
    if (!body.success) return [];
    return body.data;
  } catch {
    return [];
  }
}

async function apiGetProviderStatus(): Promise<ProviderStatus | null> {
  try {
    const resp = await fetch('/api/v1/media/status', {
      credentials: 'include',
    });
    if (!resp.ok) return null;
    const body = await resp.json();
    return body.providers;
  } catch {
    return null;
  }
}

// ── Helpers ──────────────────────────────────────────────────

function stateLabel(state: MediaRuntimeState): string {
  const labels: Record<MediaRuntimeState, string> = {
    idle: 'Ready',
    preparing_brief: 'Preparing visual brief…',
    generating: 'Generating image…',
    generated: 'Generated',
    description_only: 'Visual concept ready',
    provider_unavailable: 'Provider unavailable',
    failed: 'Generation failed',
  };
  return labels[state];
}

function stateIcon(state: MediaRuntimeState): string {
  const icons: Record<MediaRuntimeState, string> = {
    idle: '🎨',
    preparing_brief: '📝',
    generating: '✨',
    generated: '✅',
    description_only: '📋',
    provider_unavailable: '⚠️',
    failed: '❌',
  };
  return icons[state];
}

// ── Main Component ────────────────────────────────────────────

export function MediaGenerator({ onAddToCampaign }: { onAddToCampaign?: (asset: MediaAsset) => void }) {
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('1:1');
  const [visualStyle, setVisualStyle] = useState<VisualStyle>('realistic');
  const [providerStatus, setProviderStatus] = useState<ProviderStatus | null>(null);

  // Canonical state
  const [runtimeState, setRuntimeState] = useState<MediaRuntimeState>('idle');
  const [currentAsset, setCurrentAsset] = useState<MediaAsset | null>(null);
  const [history, setHistory] = useState<MediaAsset[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Optional business context (from Content Studio parent)
  const [businessContext, setBusinessContext] = useState('');

  // Load provider status and history on mount
  useEffect(() => {
    apiGetProviderStatus().then(setProviderStatus);
    apiGetAssets().then(setHistory);
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!prompt.trim()) return;

    setRuntimeState('preparing_brief');
    setError(null);
    setCurrentAsset(null);

    // Parse business context from text input into structured object
    let bc: Record<string, unknown> | undefined;
    if (businessContext.trim()) {
      bc = { raw_text: businessContext.trim() };
      // Try to extract structured fields
      const lines = businessContext.trim().split('\n');
      for (const line of lines) {
        const [key, ...vals] = line.split(':');
        if (vals.length > 0) {
          bc[key.trim().toLowerCase().replace(/\s+/g, '_')] = vals.join(':').trim();
        }
      }
    }

    try {
      const asset = await apiGenerateMedia({
        prompt: prompt.trim(),
        aspect_ratio: aspectRatio,
        visual_style: visualStyle,
        business_context: bc,
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

  return (
    <div className="cs-media-gen">
      {/* ── Result is the hero ── */}
      {(currentAsset && (runtimeState === 'generated' || runtimeState === 'description_only')) ? (
        <div className="cs-media-result-hero">
          {runtimeState === 'generated' && currentAsset.asset_url ? (
            <div className="cs-media-image-container" style={{ aspectRatio: currentAsset.aspect_ratio.replace(':', '/') }}>
              <img
                src={currentAsset.asset_url}
                alt={currentAsset.raw_prompt}
                className="cs-media-image"
              />
              <div className="cs-media-badge">Generated Image</div>
            </div>
          ) : (
            <div className="cs-media-concept-container">
              <div className="cs-media-concept-card" style={{ aspectRatio: currentAsset.aspect_ratio.replace(':', '/') }}>
                <div className="cs-media-concept-icon">📋</div>
                <h3 className="cs-media-concept-title">Visual Concept</h3>
                <p className="cs-media-concept-desc">
                  {currentAsset.description || 'A creative concept was generated based on your input.'}
                </p>
              </div>
              <div className="cs-media-badge cs-badge-concept">Visual Concept</div>
            </div>
          )}

          {/* Asset metadata */}
          <div className="cs-media-meta-bar">
            <span className="cs-media-meta-item">{stateIcon(runtimeState)} {stateLabel(runtimeState)}</span>
            <span className="cs-media-meta-item">{currentAsset.aspect_ratio}</span>
            <span className="cs-media-meta-item">{currentAsset.visual_style}</span>
            {currentAsset.provider && (
              <span className="cs-media-meta-item">via {currentAsset.provider.split('/').pop()}</span>
            )}
            <span className="cs-media-meta-item">
              {new Date(currentAsset.created_at).toLocaleString()}
            </span>
          </div>

          {/* Visual brief */}
          {currentAsset.visual_brief && (
            <details className="cs-media-brief-toggle">
              <summary>View visual brief</summary>
              <pre className="cs-media-brief">{currentAsset.visual_brief}</pre>
            </details>
          )}

          {/* Campaign attachment */}
          {onAddToCampaign && (
            <button
              className="cs-btn cs-btn-secondary"
              onClick={() => onAddToCampaign(currentAsset)}
              style={{ marginTop: 12 }}
            >
              📢 Add to Campaign
            </button>
          )}
        </div>
      ) : null}

      {/* ── Provider unavailable state ── */}
      {runtimeState === 'provider_unavailable' && currentAsset && (
        <div className="cs-media-state-card cs-state-unavailable">
          <div className="cs-state-icon">⚠️</div>
          <h3 className="cs-state-title">Image generation is currently unavailable</h3>
          <p className="cs-state-desc">
            {currentAsset.failure_reason || 'The image generation service could not be reached.'}
          </p>
          {currentAsset.visual_brief && (
            <details className="cs-media-brief-toggle">
              <summary>Your visual brief was saved</summary>
              <pre className="cs-media-brief">{currentAsset.visual_brief}</pre>
            </details>
          )}
          <button className="cs-btn cs-btn-primary" onClick={handleGenerate} disabled={!prompt.trim()}>
            Retry
          </button>
        </div>
      )}

      {/* ── Failed state ── */}
      {runtimeState === 'failed' && (
        <div className="cs-media-state-card cs-state-failed">
          <div className="cs-state-icon">❌</div>
          <h3 className="cs-state-title">Generation failed</h3>
          <p className="cs-state-desc">{error || 'An error occurred during generation. Your settings have been preserved.'}</p>
          <button className="cs-btn cs-btn-primary" onClick={handleGenerate} disabled={!prompt.trim()}>
            Retry
          </button>
        </div>
      )}

      {/* ── Controls (always visible, visually secondary when result exists) ── */}
      {runtimeState === 'generated' || runtimeState === 'description_only' ? (
        <details className="cs-media-controls-toggle" open={false}>
          <summary>Generation controls</summary>
          <div className="cs-media-controls-panel">
            {renderControls()}
          </div>
        </details>
      ) : runtimeState !== 'provider_unavailable' && runtimeState !== 'failed' ? (
        <div className="cs-media-controls-panel">
          {renderControls()}
        </div>
      ) : null}

      {/* ── History ── */}
      {history.length > 0 && (
        <div className="cs-media-history">
          <h4 className="cs-media-history-title">Generated Assets</h4>
          <div className="cs-media-history-grid">
            {history.map(asset => (
              <div
                key={asset.id}
                className={`cs-media-history-card ${currentAsset?.id === asset.id ? 'cs-history-active' : ''}`}
                onClick={() => {
                  setCurrentAsset(asset);
                  setRuntimeState(asset.runtime_state);
                  setPrompt(asset.raw_prompt);
                }}
              >
                {asset.asset_url ? (
                  <img src={asset.asset_url} alt="" className="cs-history-thumb" />
                ) : (
                  <div className="cs-history-thumb cs-history-placeholder">
                    <span>{asset.result_kind === 'visual_concept' ? '📋' : '🎨'}</span>
                  </div>
                )}
                <div className="cs-history-meta">
                  <span className="cs-history-label">{asset.raw_prompt.slice(0, 30)}</span>
                  <span className={`cs-history-state cs-state-${asset.runtime_state}`}>
                    {stateLabel(asset.runtime_state)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
.cs-media-gen {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Result Hero ── */
.cs-media-result-hero {
  animation: csFadeIn 0.3s ease-out;
}
.cs-media-image-container {
  width: 100%;
  max-height: 70vh;
  background: linear-gradient(135deg, #f0ede8 0%, #e8e4de 100%);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cs-media-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
.cs-media-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(0,0,0,0.65);
  color: #fff;
  font-size: 11px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 4px;
  letter-spacing: 0.3px;
}
.cs-badge-concept {
  top: auto;
  bottom: 12px;
  background: rgba(108,74,226,0.85);
}

/* ── Visual Concept Card ── */
.cs-media-concept-container {
  width: 100%;
}
.cs-media-concept-card {
  width: 100%;
  background: linear-gradient(135deg, #f8f6f1 0%, #f0ede8 100%);
  border: 2px dashed #d4d0c8;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 24px;
  gap: 8px;
}
.cs-media-concept-icon {
  font-size: 40px;
  line-height: 1;
}
.cs-media-concept-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--shunya-text, #1A1C1D);
  margin: 0;
}
.cs-media-concept-desc {
  font-size: 13px;
  line-height: 1.6;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  max-width: 480px;
  margin: 0 auto;
  white-space: pre-wrap;
}

/* ── Meta bar ── */
.cs-media-meta-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 16px;
  font-size: 12px;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.45));
}

/* ── Visual Brief ── */
.cs-media-brief-toggle summary {
  cursor: pointer;
  font-size: 12px;
  color: var(--shunya-color-accent, #6C4AE2);
  font-weight: 500;
  margin-top: 8px;
}
.cs-media-brief {
  font-size: 12px;
  line-height: 1.5;
  color: var(--shunya-text, #1A1C1D);
  background: var(--shunya-surface-2, #f8f6f1);
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
  white-space: pre-wrap;
  overflow-x: auto;
}

/* ── State Cards ── */
.cs-media-state-card {
  padding: 32px 24px;
  border-radius: 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.cs-state-unavailable {
  background: rgba(217,119,6,0.08);
  border: 1px solid rgba(217,119,6,0.2);
}
.cs-state-failed {
  background: rgba(185,28,28,0.08);
  border: 1px solid rgba(185,28,28,0.15);
}
.cs-state-icon {
  font-size: 36px;
  line-height: 1;
}
.cs-state-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--shunya-text, #1A1C1D);
  margin: 0;
}
.cs-state-desc {
  font-size: 13px;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.55));
  max-width: 400px;
  margin: 0;
}

/* ── Controls ── */
.cs-media-controls-toggle summary {
  cursor: pointer;
  font-size: 12px;
  color: var(--shunya-color-accent, #6C4AE2);
  margin-top: 4px;
}
.cs-media-controls-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--shunya-surface-2, #f8f6f1);
  border-radius: 10px;
}
.cs-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.cs-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--shunya-text-secondary, rgba(26,28,29,0.45));
}
.cs-textarea {
  width: 100%;
  min-height: 64px;
  padding: 10px 12px;
  border: 1px solid var(--shunya-surface-1, #e8e4de);
  border-radius: 6px;
  background: var(--shunya-surface, #fff);
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
}
.cs-textarea:focus {
  outline: none;
  border-color: var(--shunya-color-accent, #6C4AE2);
}
.cs-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--shunya-surface-1, #e8e4de);
  border-radius: 6px;
  background: var(--shunya-surface, #fff);
  font-size: 12px;
  font-family: inherit;
  box-sizing: border-box;
}
.cs-input:focus {
  outline: none;
  border-color: var(--shunya-color-accent, #6C4AE2);
}
.cs-select-group {
  display: flex;
  gap: 8px;
}
.cs-select-group .cs-field {
  flex: 1;
}
.cs-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s ease;
}
.cs-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.cs-btn-primary {
  background: var(--shunya-color-accent, #6C4AE2);
  color: #fff;
}
.cs-btn-primary:hover:not(:disabled) {
  background: #5a3bc9;
}
.cs-btn-secondary {
  background: var(--shunya-surface-2, #f0ede8);
  color: var(--shunya-text, #1A1C1D);
  border: 1px solid var(--shunya-surface-1, #e8e4de);
}
.cs-btn-secondary:hover:not(:disabled) {
  border-color: var(--shunya-color-accent, #6C4AE2);
}

/* ── History ── */
.cs-media-history {
  margin-top: 8px;
}
.cs-media-history-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--shunya-text, #1A1C1D);
}
.cs-media-history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
}
.cs-media-history-card {
  background: var(--shunya-surface, #fff);
  border: 1px solid var(--shunya-surface-1, #e8e4de);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.15s ease;
}
.cs-media-history-card:hover {
  border-color: var(--shunya-color-accent, #6C4AE2);
}
.cs-history-active {
  border-color: var(--shunya-color-accent, #6C4AE2);
  box-shadow: 0 0 0 2px rgba(108,74,226,0.15);
}
.cs-history-thumb {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  display: block;
}
.cs-history-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: var(--shunya-surface-2, #f0ede8);
}
.cs-history-meta {
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.cs-history-label {
  font-size: 10px;
  color: var(--shunya-text, #1A1C1D);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cs-history-state {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  padding: 1px 6px;
  border-radius: 3px;
}
.cs-state-generated {
  background: rgba(34,197,94,0.12);
  color: #15803D;
}
.cs-state-description_only {
  background: rgba(108,74,226,0.1);
  color: #5a3bc9;
}
.cs-state-failed {
  background: rgba(185,28,28,0.1);
  color: #991b1b;
}

@keyframes csFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ── */
@media (max-width: 600px) {
  .cs-media-image-container, .cs-media-concept-card {
    border-radius: 8px;
  }
  .cs-media-concept-card {
    padding: 24px 16px;
  }
  .cs-select-group {
    flex-direction: column;
  }
  .cs-media-history-grid {
    grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  }
}
      `}</style>
    </div>
  );

  function renderControls() {
    return (
      <>
        <div className="cs-field">
          <label className="cs-label">What do you want to create?</label>
          <textarea
            className="cs-textarea"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Describe the image or scene you want to generate..."
            rows={3}
          />
        </div>

        <div className="cs-field">
          <label className="cs-label">Business context (optional)</label>
          <textarea
            className="cs-textarea"
            value={businessContext}
            onChange={e => setBusinessContext(e.target.value)}
            placeholder={"e.g. Destination: Bali\nDuration: 4 nights\nPrice: INR 30,000\nPositioning: accessible premium"}
            rows={2}
          />
        </div>

        <div className="cs-select-group">
          <div className="cs-field">
            <label className="cs-label">Aspect Ratio</label>
            <select
              className="cs-input"
              value={aspectRatio}
              onChange={e => setAspectRatio(e.target.value as AspectRatio)}
            >
              {ASPECT_RATIOS.map(r => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          <div className="cs-field">
            <label className="cs-label">Style</label>
            <select
              className="cs-input"
              value={visualStyle}
              onChange={e => setVisualStyle(e.target.value as VisualStyle)}
            >
              {VISUAL_STYLES.map(s => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Provider status indicator */}
        <div style={{ fontSize: 11, color: providerAvail ? 'var(--shunya-text-secondary, rgba(26,28,29,0.35))' : '#D97706' }}>
          {providerAvail
            ? '✓ Free image generation available (FLUX.1-schnell)'
            : '⚠ Free image generation may be unavailable — visual concept fallback will be used'
          }
        </div>

        <button
          className="cs-btn cs-btn-primary"
          onClick={handleGenerate}
          disabled={!prompt.trim() || isBusy}
          style={{ alignSelf: 'flex-start' }}
        >
          {isBusy ? (
            <>{stateIcon(runtimeState)} {stateLabel(runtimeState)}</>
          ) : (
            <>🎨 Generate Media</>
          )}
        </button>
      </>
    );
  }
}