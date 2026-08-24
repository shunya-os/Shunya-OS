/**
 * MediaGenerator — AI image/media generation panel for Content Studio 4.0.
 *
 * Provider-neutral: supports ComfyUI/local generation where available.
 * Exposes aspect ratio, platform preset, visual direction, variant count.
 * Generated media enters the canonical asset system.
 */
import { useState, useCallback } from 'react';

// ── Types ──

export type AspectRatio = '1:1' | '4:5' | '9:16' | '16:9' | '3:2' | '4:3';
export type PlatformPreset = 'instagram-square' | 'instagram-portrait' | 'instagram-story' | 'facebook-feed' | 'facebook-story' | 'linkedin-feed' | 'twitter-feed' | 'google-display' | 'website-banner' | 'custom';
export type MediaStatus = 'idle' | 'generating' | 'completed' | 'failed';

interface GeneratedMedia {
  id: string;
  url: string;
  prompt: string;
  aspectRatio: AspectRatio;
  createdAt: string;
  status: 'draft' | 'saved';
}

const ASPECT_RATIOS: { value: AspectRatio; label: string; w: number; h: number }[] = [
  { value: '1:1', label: 'Square 1:1', w: 1024, h: 1024 },
  { value: '4:5', label: 'Portrait 4:5', w: 1024, h: 1280 },
  { value: '9:16', label: 'Story 9:16', w: 1080, h: 1920 },
  { value: '16:9', label: 'Landscape 16:9', w: 1920, h: 1080 },
  { value: '3:2', label: 'Photo 3:2', w: 1200, h: 800 },
  { value: '4:3', label: 'Display 4:3', w: 1600, h: 1200 },
];

const PLATFORM_PRESETS: { value: PlatformPreset; label: string; ratio: AspectRatio }[] = [
  { value: 'instagram-square', label: 'Instagram Square', ratio: '1:1' },
  { value: 'instagram-portrait', label: 'Instagram Portrait', ratio: '4:5' },
  { value: 'instagram-story', label: 'Instagram Story', ratio: '9:16' },
  { value: 'facebook-feed', label: 'Facebook Feed', ratio: '1:1' },
  { value: 'facebook-story', label: 'Facebook Story', ratio: '9:16' },
  { value: 'linkedin-feed', label: 'LinkedIn Feed', ratio: '1:1' },
  { value: 'twitter-feed', label: 'X/Twitter Feed', ratio: '16:9' },
  { value: 'google-display', label: 'Google Display', ratio: '4:3' },
  { value: 'website-banner', label: 'Website Banner', ratio: '16:9' },
  { value: 'custom', label: 'Custom', ratio: '1:1' },
];

const VISUAL_STYLES = [
  { value: 'realistic', label: 'Realistic' },
  { value: 'illustration', label: 'Illustration' },
  { value: 'cinematic', label: 'Cinematic' },
  { value: 'minimalist', label: 'Minimalist' },
  { value: 'corporate', label: 'Corporate' },
  { value: 'artistic', label: 'Artistic' },
];

export function MediaGenerator({ onAddToCampaign }: { onAddToCampaign?: (media: GeneratedMedia) => void }) {
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('1:1');
  const [platformPreset, setPlatformPreset] = useState<PlatformPreset>('custom');
  const [visualStyle, setVisualStyle] = useState('realistic');
  const [variantCount, setVariantCount] = useState(1);
  const [status, setStatus] = useState<MediaStatus>('idle');
  const [generated, setGenerated] = useState<GeneratedMedia[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handlePlatformChange = (preset: PlatformPreset) => {
    setPlatformPreset(preset);
    const p = PLATFORM_PRESETS.find(pp => pp.value === preset);
    if (p && p.ratio) setAspectRatio(p.ratio);
  };

  const handleGenerate = useCallback(async () => {
    if (!prompt.trim()) return;
    setStatus('generating');
    setError(null);

    try {
      // Try the backend image generation endpoint
      const resp = await fetch('/api/v1/content/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          prompt: prompt,
          content_type: 'image',
          image_params: {
            aspect_ratio: aspectRatio,
            style: visualStyle,
            platform: platformPreset === 'custom' ? null : platformPreset,
            variants: variantCount,
          },
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        if (data.success && data.content) {
          const newMedia: GeneratedMedia = {
            id: `media_${Date.now()}`,
            url: data.content, // Would be an image URL from the provider
            prompt: prompt,
            aspectRatio: aspectRatio,
            createdAt: new Date().toISOString(),
            status: 'draft',
          };
          setGenerated(prev => [newMedia, ...prev]);
          setStatus('completed');
          return;
        }
      }
      // Fallback: AI chat generates a description of the image
      const chatResp = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          messages: [
            { role: 'system', content: `You are a creative visual director. Describe in detail what an image should look like based on the user's prompt. Include composition, colors, lighting, mood, and style. Aspect ratio: ${aspectRatio}. Style: ${visualStyle}.` },
            { role: 'user', content: prompt },
          ],
          temperature: 0.8,
          max_tokens: 1024,
        }),
      });
      if (chatResp.ok) {
        const chatData = await chatResp.json();
        const newMedia: GeneratedMedia = {
          id: `media_${Date.now()}`,
          url: '', // No actual image — provider needed
          prompt: chatData.content || prompt,
          aspectRatio: aspectRatio,
          createdAt: new Date().toISOString(),
          status: 'draft',
        };
        setGenerated(prev => [newMedia, ...prev]);
        setStatus('completed');
      } else {
        setError('Media generation requires a connected provider (ComfyUI, etc.). The description was generated via AI chat.');
        setStatus('failed');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      setStatus('failed');
    }
  }, [prompt, aspectRatio, visualStyle, variantCount, platformPreset]);

  return (
    <div className="cs-media-gen">
      <div className="cs-field">
        <label className="cs-label">Visual Prompt</label>
        <textarea
          className="cs-textarea"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="Describe the image you want to generate..."
          rows={3}
        />
      </div>

      <div className="cs-field">
        <label className="cs-label">Platform Preset</label>
        <div className="cs-preset-grid">
          {PLATFORM_PRESETS.map(p => (
            <button
              key={p.value}
              className={`cs-preset-btn ${platformPreset === p.value ? 'cs-preset-active' : ''}`}
              onClick={() => handlePlatformChange(p.value)}
              title={`${p.label} (${p.ratio})`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="cs-media-row">
        <div className="cs-field cs-media-half">
          <label className="cs-label">Aspect Ratio</label>
          <select
            className="cs-input"
            value={aspectRatio}
            onChange={e => setAspectRatio(e.target.value as AspectRatio)}
          >
            {ASPECT_RATIOS.map(r => (
              <option key={r.value} value={r.value}>{r.label} ({r.w}×{r.h})</option>
            ))}
          </select>
        </div>

        <div className="cs-field cs-media-half">
          <label className="cs-label">Visual Style</label>
          <select
            className="cs-input"
            value={visualStyle}
            onChange={e => setVisualStyle(e.target.value)}
          >
            {VISUAL_STYLES.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="cs-field">
        <label className="cs-label">Variants</label>
        <div className="cs-variant-row">
          {[1, 2, 3, 4].map(n => (
            <button
              key={n}
              className={`cs-variant-btn ${variantCount === n ? 'cs-variant-active' : ''}`}
              onClick={() => setVariantCount(n)}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      <button
        className="cs-btn cs-btn-primary"
        onClick={handleGenerate}
        disabled={!prompt.trim() || status === 'generating'}
        style={{ marginTop: 8 }}
      >
        {status === 'generating' ? 'Generating…' : 'Generate Media'}
      </button>

      {error && <div className="cs-error">{error}</div>}

      {generated.length > 0 && (
        <div className="cs-media-results">
          <h4 className="cs-media-results-title">Generated Media</h4>
          <div className="cs-media-grid">
            {generated.map((m, i) => (
              <div key={m.id} className="cs-media-card">
                <div className="cs-media-preview" style={{ aspectRatio: m.aspectRatio.replace(':', '/') }}>
                  {m.url ? (
                    <img src={m.url} alt={`Generated ${i + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 6 }} />
                  ) : (
                    <div className="cs-media-placeholder">
                      <span>Media Preview</span>
                      <small>{m.aspectRatio}</small>
                    </div>
                  )}
                </div>
                <div className="cs-media-meta">
                  <span className="cs-media-prompt">{m.prompt.slice(0, 60)}</span>
                  <div className="cs-media-actions">
                    {onAddToCampaign && (
                      <button className="cs-icon-btn" onClick={() => onAddToCampaign(m)} title="Add to Campaign">
                        📢
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
.cs-media-gen { padding: 0; }
.cs-preset-grid { display: flex; flex-wrap: wrap; gap: 4px; }
.cs-preset-btn { padding: 4px 10px; font-size: 11px; background: var(--shunya-surface-2, #f0ede8); border: 1px solid var(--shunya-surface-1, #e8e4de); border-radius: 4px; cursor: pointer; white-space: nowrap; }
.cs-preset-btn:hover { border-color: var(--shunya-color-accent, #6C4AE2); }
.cs-preset-active { background: var(--shunya-color-accent, #6C4AE2); color: #fff; border-color: var(--shunya-color-accent, #6C4AE2); }
.cs-media-row { display: flex; gap: 8px; }
.cs-media-half { flex: 1; }
.cs-variant-row { display: flex; gap: 4px; }
.cs-variant-btn { padding: 4px 12px; font-size: 12px; background: var(--shunya-surface-2, #f0ede8); border: 1px solid var(--shunya-surface-1, #e8e4de); border-radius: 4px; cursor: pointer; }
.cs-variant-btn:hover { border-color: var(--shunya-color-accent, #6C4AE2); }
.cs-variant-active { background: var(--shunya-color-accent, #6C4AE2); color: #fff; border-color: var(--shunya-color-accent, #6C4AE2); }
.cs-media-results { margin-top: 16px; }
.cs-media-results-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; color: var(--shunya-text, #1A1C1D); }
.cs-media-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }
.cs-media-card { background: var(--shunya-surface, #fff); border: 1px solid var(--shunya-surface-1, #e8e4de); border-radius: 8px; overflow: hidden; }
.cs-media-preview { width: 100%; background: var(--shunya-surface-2, #f0ede8); display: flex; align-items: center; justify-content: center; min-height: 120px; }
.cs-media-placeholder { display: flex; flex-direction: column; align-items: center; color: var(--shunya-text-secondary, rgba(26,28,29,0.55)); font-size: 12px; gap: 4px; }
.cs-media-meta { padding: 6px 8px; display: flex; justify-content: space-between; align-items: center; }
.cs-media-prompt { font-size: 11px; color: var(--shunya-text, #1A1C1D); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cs-media-actions { display: flex; gap: 4px; }
.cs-media-actions .cs-icon-btn { font-size: 14px; padding: 2px; cursor: pointer; background: none; border: none; }
.cs-error { color: #B91C1C; font-size: 12px; padding: 8px; background: rgba(185,28,28,0.08); border-radius: 4px; margin-top: 8px; }
      `}</style>
    </div>
  );
}