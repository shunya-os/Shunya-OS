/**
 * Theme Settings — Workspace theme editor with color pickers and logo upload.
 *
 * Embedded in the workspace-bar profile dropdown as a settings modal.
 * Provides controls for:
 *   - Primary color, accent color, background color, sidebar background
 *   - Font family selection
 *   - Logo upload (POST /api/v1/orgs/{org_id}/logo)
 *   - Welcome message and company motto
 *   - Logo style (contain, cover, circle)
 */

import { useState, useEffect, useRef } from 'react';

// ── Types ───────────────────────────────────────────────────

interface ThemeData {
  primary_color: string;
  accent_color: string;
  bg_color: string;
  sidebar_bg: string;
  font_family: string;
  logo_path: string | null;
  logo_style: string;
  welcome_message: string;
  company_motto: string;
  custom_css: string;
}

interface ThemeSettingsProps {
  onClose: () => void;
}

// ── Org ID resolution ───────────────────────────────────────

function getCurrentOrgId(): number | null {
  // Try common patterns: current_org_id in session, or first org from API
  // For now, default to org_id=1 for single-tenant setups
  return 1;
}

// ── API helpers ──────────────────────────────────────────────

async function fetchTheme(orgId: number): Promise<ThemeData> {
  const r = await fetch(`/api/v1/orgs/${orgId}/theme`, { credentials: 'include' });
  if (!r.ok) throw new Error(`Failed to load theme (${r.status})`);
  const data = await r.json();
  return data.data;
}

async function saveTheme(orgId: number, theme: Partial<ThemeData>): Promise<ThemeData> {
  const r = await fetch(`/api/v1/orgs/${orgId}/theme`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(theme),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ error: `Server error (${r.status})` }));
    throw new Error(err.error || `Failed to save theme (${r.status})`);
  }
  const data = await r.json();
  return data.data;
}

async function uploadLogo(orgId: number, file: File): Promise<string> {
  const formData = new FormData();
  formData.append('logo', file);

  const r = await fetch(`/api/v1/orgs/${orgId}/logo`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ error: `Upload failed (${r.status})` }));
    throw new Error(err.error || `Logo upload failed (${r.status})`);
  }
  const data = await r.json();
  return data.data.logo_path;
}

// ── Color Picker Component ──────────────────────────────────

function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="ts-field">
      <label className="ts-label">{label}</label>
      <div className="ts-color-row">
        <input type="color" className="ts-color-picker" value={value} onChange={(e) => onChange(e.target.value)} />
        <input
          type="text"
          className="ts-color-text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#000000"
        />
      </div>
    </div>
  );
}

// ── Preset Color Themes ─────────────────────────────────────

const PRESET_THEMES: { name: string; primary: string; accent: string; bg: string; sidebar: string }[] = [
  { name: 'Default Blue', primary: '#2563eb', accent: '#7c3aed', bg: '#f8fafc', sidebar: '#0f172a' },
  { name: 'Midnight', primary: '#1e3a5f', accent: '#2563eb', bg: '#0f172a', sidebar: '#020617' },
  { name: 'Emerald', primary: '#059669', accent: '#34d399', bg: '#f0fdf4', sidebar: '#064e3b' },
  { name: 'Ruby Red', primary: '#dc2626', accent: '#f87171', bg: '#fef2f2', sidebar: '#450a0a' },
  { name: 'Amber Glow', primary: '#f59e0b', accent: '#fbbf24', bg: '#fffbeb', sidebar: '#451a03' },
  { name: 'Dark Purple', primary: '#7c3aed', accent: '#a78bfa', bg: '#0f172a', sidebar: '#1e1b4b' },
  { name: 'Teal Ocean', primary: '#0d9488', accent: '#2dd4bf', bg: '#f0fdfa', sidebar: '#042f2e' },
  { name: 'Petal Pink', primary: '#ec4899', accent: '#f472b6', bg: '#fdf2f8', sidebar: '#500724' },
];

// ── Font Options ────────────────────────────────────────────

const FONT_OPTIONS = ['Inter', 'System UI', 'serif', 'monospace', 'Poppins', 'Roboto', 'Plus Jakarta Sans'];

// ── Theme Settings Component ─────────────────────────────────

export function ThemeSettings({ onClose }: ThemeSettingsProps) {
  const [orgId] = useState(() => getCurrentOrgId());
  const [theme, setTheme] = useState<ThemeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'colors' | 'logo' | 'text'>('colors');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load theme on mount
  useEffect(() => {
    if (!orgId) {
      setError('No organization context available. Theme settings require an active org.');
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchTheme(orgId)
      .then((data) => {
        setTheme(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [orgId]);

  // Helpers
  const updateField = (field: keyof ThemeData, value: string) => {
    if (!theme) return;
    setTheme({ ...theme, [field]: value });
  };

  const handleSave = async () => {
    if (!theme || !orgId) return;
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await saveTheme(orgId, {
        primary_color: theme.primary_color,
        accent_color: theme.accent_color,
        bg_color: theme.bg_color,
        sidebar_bg: theme.sidebar_bg,
        font_family: theme.font_family,
        logo_style: theme.logo_style,
        welcome_message: theme.welcome_message,
        company_motto: theme.company_motto,
        custom_css: theme.custom_css,
      });
      setTheme(updated);
      setSuccessMsg('Theme saved successfully!');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !orgId) return;
    setSaving(true);
    setError(null);
    try {
      const logoPath = await uploadLogo(orgId, file);
      if (theme) {
        setTheme({ ...theme, logo_path: logoPath });
      }
      setSuccessMsg('Logo uploaded successfully!');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
      // Reset file input so the same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handlePreset = (preset: (typeof PRESET_THEMES)[0]) => {
    if (!theme) return;
    setTheme({
      ...theme,
      primary_color: preset.primary,
      accent_color: preset.accent,
      bg_color: preset.bg,
      sidebar_bg: preset.sidebar,
    });
  };

  // ── Render ──

  return (
    <div className="ts-overlay" onClick={onClose}>
      <div className="ts-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Theme settings">
        <div className="ts-header">
          <h2 className="ts-title">Theme Settings</h2>
          <button className="ts-close" onClick={onClose} aria-label="Close settings">
            &times;
          </button>
        </div>

        {loading ? (
          <div className="ts-loading">
            <div className="ts-spinner" />
            <span>Loading theme…</span>
          </div>
        ) : error && !theme ? (
          <div className="ts-error-state">
            <div className="ts-error-icon">⚠</div>
            <div className="ts-error-msg">{error}</div>
          </div>
        ) : theme ? (
          <>
            {/* Tab bar */}
            <div className="ts-tabs" role="tablist">
              <button
                className={`ts-tab ${activeTab === 'colors' ? 'ts-tab-active' : ''}`}
                onClick={() => setActiveTab('colors')}
                role="tab"
                aria-selected={activeTab === 'colors'}
              >
                Colors
              </button>
              <button
                className={`ts-tab ${activeTab === 'logo' ? 'ts-tab-active' : ''}`}
                onClick={() => setActiveTab('logo')}
                role="tab"
                aria-selected={activeTab === 'logo'}
              >
                Logo
              </button>
              <button
                className={`ts-tab ${activeTab === 'text' ? 'ts-tab-active' : ''}`}
                onClick={() => setActiveTab('text')}
                role="tab"
                aria-selected={activeTab === 'text'}
              >
                Text
              </button>
            </div>

            {/* Colors tab */}
            {activeTab === 'colors' && (
              <div className="ts-tab-content">
                <div className="ts-presets">
                  <div className="ts-section-label">Quick Themes</div>
                  <div className="ts-preset-grid">
                    {PRESET_THEMES.map((p) => (
                      <button key={p.name} className="ts-preset-btn" onClick={() => handlePreset(p)} title={p.name}>
                        <div className="ts-preset-swatches">
                          <span className="ts-swatch" style={{ background: p.primary }} />
                          <span className="ts-swatch" style={{ background: p.accent }} />
                          <span className="ts-swatch" style={{ background: p.bg }} />
                          <span className="ts-swatch" style={{ background: p.sidebar }} />
                        </div>
                        <span className="ts-preset-name">{p.name}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="ts-fields">
                  <ColorField
                    label="Primary Color"
                    value={theme.primary_color}
                    onChange={(v) => updateField('primary_color', v)}
                  />
                  <ColorField
                    label="Accent Color"
                    value={theme.accent_color}
                    onChange={(v) => updateField('accent_color', v)}
                  />
                  <ColorField
                    label="Background Color"
                    value={theme.bg_color}
                    onChange={(v) => updateField('bg_color', v)}
                  />
                  <ColorField
                    label="Sidebar Background"
                    value={theme.sidebar_bg}
                    onChange={(v) => updateField('sidebar_bg', v)}
                  />
                </div>
              </div>
            )}

            {/* Logo tab */}
            {activeTab === 'logo' && (
              <div className="ts-tab-content">
                <div className="ts-section-label">Logo</div>
                <div className="ts-logo-preview">
                  {theme.logo_path ? (
                    <img
                      src={theme.logo_path}
                      alt="Organization logo"
                      className={`ts-logo-img ts-logo-${theme.logo_style}`}
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="ts-logo-placeholder">
                      <span className="ts-logo-placeholder-icon">🖼</span>
                      <span>No logo uploaded</span>
                    </div>
                  )}
                </div>
                <div className="ts-upload-row">
                  <button className="ts-upload-btn" onClick={() => fileInputRef.current?.click()} disabled={saving}>
                    {saving ? 'Uploading…' : 'Choose Logo'}
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/gif,image/svg+xml,image/webp"
                    className="ts-file-input"
                    onChange={handleLogoUpload}
                  />
                  <span className="ts-upload-hint">PNG, JPG, GIF, SVG, WebP</span>
                </div>
                <div className="ts-field">
                  <label className="ts-label">Logo Style</label>
                  <div className="ts-style-options">
                    {['contain', 'cover', 'circle'].map((style) => (
                      <button
                        key={style}
                        className={`ts-style-btn ${theme.logo_style === style ? 'ts-style-active' : ''}`}
                        onClick={() => updateField('logo_style', style)}
                      >
                        {style}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Text tab */}
            {activeTab === 'text' && (
              <div className="ts-tab-content">
                <div className="ts-field">
                  <label className="ts-label">Font Family</label>
                  <select
                    className="ts-select"
                    value={theme.font_family}
                    onChange={(e) => updateField('font_family', e.target.value)}
                  >
                    {FONT_OPTIONS.map((f) => (
                      <option key={f} value={f === 'System UI' ? 'system-ui' : f}>
                        {f}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="ts-field">
                  <label className="ts-label">Welcome Message</label>
                  <input
                    type="text"
                    className="ts-input"
                    value={theme.welcome_message}
                    onChange={(e) => updateField('welcome_message', e.target.value)}
                    placeholder="Welcome to your workspace"
                  />
                </div>
                <div className="ts-field">
                  <label className="ts-label">Company Motto</label>
                  <input
                    type="text"
                    className="ts-input"
                    value={theme.company_motto}
                    onChange={(e) => updateField('company_motto', e.target.value)}
                    placeholder="Your company motto"
                  />
                </div>
                <div className="ts-field">
                  <label className="ts-label">Custom CSS</label>
                  <textarea
                    className="ts-textarea"
                    value={theme.custom_css}
                    onChange={(e) => updateField('custom_css', e.target.value)}
                    placeholder="/* Custom CSS overrides */"
                    rows={4}
                  />
                </div>
              </div>
            )}

            {/* Action bar */}
            <div className="ts-actions">
              {error && <div className="ts-error">{error}</div>}
              {successMsg && <div className="ts-success">{successMsg}</div>}
              <button className="ts-save-btn" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save Theme'}
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

// ── Styles ───────────────────────────────────────────────────

const styles = `
/* Overlay */
.ts-overlay { position: fixed; inset: 0; z-index: 500; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; backdrop-filter: blur(2px); }

/* Modal */
.ts-modal { background: var(--sh-surface, #1a1a26); border: 1px solid var(--sh-border, #333); border-radius: var(--sh-radius-lg, 12px); width: min(520px, 90vw); max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }

.ts-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--sh-border, #22222e); }
.ts-title { font-size: var(--sh-text-lg, 18px); font-weight: 600; color: var(--sh-text, #e0e0e0); margin: 0; }
.ts-close { background: transparent; border: none; font-size: 24px; color: var(--sh-text-secondary, #888); cursor: pointer; padding: 0 4px; line-height: 1; }
.ts-close:hover { color: var(--sh-text, #e0e0e0); }

/* Loading */
.ts-loading { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 48px 20px; color: var(--sh-text-secondary, #888); }
.ts-spinner { width: 20px; height: 20px; border: 2px solid var(--sh-border, #333); border-top-color: var(--sh-purple, #555); border-radius: 50%; animation: ts-spin 0.6s linear infinite; }
@keyframes ts-spin { to { transform: rotate(360deg); } }

/* Error state */
.ts-error-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 48px 20px; text-align: center; }
.ts-error-icon { font-size: 32px; }
.ts-error-msg { font-size: var(--sh-text-sm, 14px); color: var(--sh-danger, #f55); }

/* Tabs */
.ts-tabs { display: flex; border-bottom: 1px solid var(--sh-border, #22222e); padding: 0 20px; }
.ts-tab { padding: 10px 16px; background: transparent; border: none; border-bottom: 2px solid transparent; color: var(--sh-text-secondary, #888); font-size: var(--sh-text-sm, 14px); cursor: pointer; transition: color 0.15s, border-color 0.15s; }
.ts-tab:hover { color: var(--sh-text, #e0e0e0); }
.ts-tab-active { color: var(--sh-purple, #555); border-bottom-color: var(--sh-purple, #555); }

/* Tab content */
.ts-tab-content { padding: 20px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 16px; }

/* Fields */
.ts-field { display: flex; flex-direction: column; gap: 6px; }
.ts-label { font-size: var(--sh-text-xs, 12px); color: var(--sh-text-secondary, #888); text-transform: uppercase; letter-spacing: 0.04em; font-weight: 500; }
.ts-input, .ts-select, .ts-textarea { padding: 8px 12px; background: var(--sh-surface-subtle, #12121e); border: 1px solid var(--sh-border, #2a2a3a); border-radius: var(--sh-radius-sm, 6px); color: var(--sh-text, #e0e0e0); font-size: var(--sh-text-sm, 14px); font-family: inherit; }
.ts-input:focus, .ts-select:focus, .ts-textarea:focus { outline: none; border-color: var(--sh-purple, #555); }
.ts-textarea { resize: vertical; min-height: 80px; font-family: monospace; }
.ts-select { cursor: pointer; }
.ts-select option { background: #1a1a26; }

/* Color field */
.ts-color-row { display: flex; align-items: center; gap: 8px; }
.ts-color-picker { width: 40px; height: 36px; padding: 2px; border: 1px solid var(--sh-border, #2a2a3a); border-radius: var(--sh-radius-sm, 6px); cursor: pointer; background: transparent; }
.ts-color-text { flex: 1; padding: 8px 12px; background: var(--sh-surface-subtle, #12121e); border: 1px solid var(--sh-border, #2a2a3a); border-radius: var(--sh-radius-sm, 6px); color: var(--sh-text, #e0e0e0); font-size: var(--sh-text-sm, 14px); font-family: monospace; }
.ts-color-text:focus { outline: none; border-color: var(--sh-purple, #555); }

/* Presets */
.ts-section-label { font-size: var(--sh-text-xs, 12px); color: var(--sh-text-secondary, #888); text-transform: uppercase; letter-spacing: 0.04em; font-weight: 500; margin-bottom: 8px; }
.ts-preset-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.ts-preset-btn { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 4px; background: var(--sh-surface-subtle, #12121e); border: 1px solid var(--sh-border, #2a2a3a); border-radius: var(--sh-radius-sm, 6px); cursor: pointer; transition: border-color 0.15s; }
.ts-preset-btn:hover { border-color: var(--sh-purple, #555); }
.ts-preset-swatches { display: flex; gap: 2px; }
.ts-swatch { width: 16px; height: 12px; border-radius: 2px; border: 1px solid rgba(255,255,255,0.08); }
.ts-preset-name { font-size: 10px; color: var(--sh-text-secondary, #888); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }

/* Logo */
.ts-logo-preview { display: flex; align-items: center; justify-content: center; min-height: 120px; background: var(--sh-surface-subtle, #12121e); border: 1px dashed var(--sh-border, #2a2a3a); border-radius: var(--sh-radius-md, 8px); padding: 16px; }
.ts-logo-img { max-width: 200px; max-height: 100px; }
.ts-logo-contain { object-fit: contain; }
.ts-logo-cover { object-fit: cover; width: 100%; height: 100px; border-radius: var(--sh-radius-sm, 6px); }
.ts-logo-circle { object-fit: cover; width: 100px; height: 100px; border-radius: 50%; }
.ts-logo-placeholder { display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--sh-text-secondary, #666); font-size: var(--sh-text-sm, 14px); }
.ts-logo-placeholder-icon { font-size: 32px; }

.ts-upload-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.ts-upload-btn { padding: 8px 16px; background: var(--sh-purple, #555); color: #fff; border: none; border-radius: var(--sh-radius-sm, 6px); font-size: var(--sh-text-sm, 14px); cursor: pointer; }
.ts-upload-btn:hover { opacity: 0.85; }
.ts-upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ts-file-input { display: none; }
.ts-upload-hint { font-size: var(--sh-text-xs, 12px); color: var(--sh-text-secondary, #666); }

.ts-style-options { display: flex; gap: 6px; }
.ts-style-btn { padding: 6px 14px; background: var(--sh-surface-subtle, #12121e); border: 1px solid var(--sh-border, #2a2a3a); border-radius: var(--sh-radius-sm, 6px); color: var(--sh-text, #e0e0e0); font-size: var(--sh-text-xs, 12px); text-transform: capitalize; cursor: pointer; }
.ts-style-btn:hover { border-color: var(--sh-purple, #555); }
.ts-style-active { border-color: var(--sh-purple, #555); background: rgba(85,85,85,0.15); }

/* Actions */
.ts-actions { display: flex; align-items: center; gap: 12px; padding: 12px 20px; border-top: 1px solid var(--sh-border, #22222e); }
.ts-error { font-size: var(--sh-text-xs, 12px); color: var(--sh-danger, #f55); flex: 1; }
.ts-success { font-size: var(--sh-text-xs, 12px); color: var(--sh-success, #4caf50); flex: 1; }
.ts-save-btn { margin-left: auto; padding: 8px 20px; background: var(--sh-purple, #555); color: #fff; border: none; border-radius: var(--sh-radius-sm, 6px); font-size: var(--sh-text-sm, 14px); font-weight: 500; cursor: pointer; }
.ts-save-btn:hover { opacity: 0.85; }
.ts-save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ts-fields { display: flex; flex-direction: column; gap: 12px; }
`;

if (typeof document !== 'undefined') {
  const el = document.createElement('style');
  el.textContent = styles;
  el.id = 'shunya-theme-settings-styles';
  if (!document.getElementById('shunya-theme-settings-styles')) {
    document.head.appendChild(el);
  }
}
