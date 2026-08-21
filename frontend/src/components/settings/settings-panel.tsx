/**
 * Settings Panel — Profile, Appearance, Data
 * Warm glass-morphism, inline CSS, matching SHUNYA OS aesthetic.
 * Simplified: removed Notifications, Language, Account sections.
 */
import { useState, useEffect, useRef } from 'react';
import {
  Settings,
  User,
  Palette,
  Download,
  Sun,
  Moon,
  RefreshCw,
  FileDown,
  Shield,
  Sparkles,
  CreditCard,
  Zap,
} from 'lucide-react';
import { ColorPicker, Kbd, Group, Text, Select, ThemeIcon } from '@mantine/core';
import { SessionManager } from '../../api/session';
import { IntegrationHub } from './integration-hub';
import { MfaSetup } from '../auth/mfa-setup';

// ── Types ──

type SettingsTab = 'profile' | 'appearance' | 'ai' | 'security' | 'data' | 'payments' | 'integrations';
type ThemeColor = '#6C4AE2' | '#2D6A4F' | '#0891B2' | '#B91C1C' | '#A4865F';

interface ProfileInfo {
  name: string;
  email: string;
  avatarInitial: string;
}

const TABS: { id: SettingsTab; label: string; icon: any }[] = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'ai', label: 'AI Model', icon: Sparkles },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'data', label: 'Data', icon: Download },
  { id: 'payments', label: 'Payments', icon: CreditCard },
  { id: 'integrations', label: 'Integrations', icon: Zap },
];

const accentColor = '#6C4AE2';

// ── Profile Section ──

function ProfileSection({ profile, onNameChange }: { profile: ProfileInfo; onNameChange: (name: string) => void }) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(profile.name);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  const handleSave = () => {
    onNameChange(name.trim() || profile.name);
    setEditing(false);
  };

  return (
    <div className="sp-section">
      <div className="sp-section-header">
        <User size={14} style={{ color: accentColor }} />
        <span className="sp-section-title">Profile</span>
      </div>
      <div className="sp-card">
        <div className="sp-avatar-row">
          <div className="sp-avatar" style={{ background: accentColor }}>
            {profile.avatarInitial}
          </div>
          <div className="sp-avatar-info">
            <span className="sp-avatar-name">{profile.name || 'User'}</span>
            <span className="sp-avatar-email">{profile.email}</span>
          </div>
        </div>
        <div className="sp-field">
          <span className="sp-field-label">Display Name</span>
          <div className="sp-field-row">
            {editing ? (
              <>
                <input
                  ref={inputRef}
                  className="sp-input"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleSave(); if (e.key === 'Escape') { setName(profile.name); setEditing(false); } }}
                  placeholder="Your name"
                />
                <button className="sp-btn sp-btn-primary" onClick={handleSave}>Save</button>
                <button className="sp-btn" onClick={() => { setName(profile.name); setEditing(false); }}>Cancel</button>
              </>
            ) : (
              <>
                <span className="sp-value">{profile.name || 'Not set'}</span>
                <button className="sp-btn" onClick={() => { setName(profile.name); setEditing(true); }}>Edit</button>
              </>
            )}
          </div>
        </div>
        <div className="sp-field">
          <span className="sp-field-label">Email</span>
          <span className="sp-value sp-value-readonly">{profile.email}</span>
        </div>
      </div>
    </div>
  );
}

// ── Appearance Section ──

function AppearanceSection({ isDark, setIsDark, themeColor, setThemeColor }: {
  isDark: boolean;
  setIsDark: (v: boolean) => void;
  themeColor: string;
  setThemeColor: (c: string) => void;
}) {
  return (
    <div className="sp-section">
      <div className="sp-section-header">
        <Palette size={14} style={{ color: accentColor }} />
        <span className="sp-section-title">Appearance</span>
      </div>
      <div className="sp-card">
        <div className="sp-field">
          <span className="sp-field-label">Theme</span>
          <div className="sp-toggle-row">
            <button
              className={`sp-toggle-btn ${!isDark ? 'sp-toggle-active' : ''}`}
              onClick={() => setIsDark(false)}
            >
              <Sun size={14} /> Light
            </button>
            <button
              className={`sp-toggle-btn ${isDark ? 'sp-toggle-active' : ''}`}
              onClick={() => setIsDark(true)}
            >
              <Moon size={14} /> Dark
            </button>
          </div>
        </div>
        <div className="sp-field">
          <span className="sp-field-label">Accent Color</span>
          <ColorPicker
            format="hex"
            value={themeColor}
            onChange={setThemeColor}
            swatches={['#6C4AE2', '#2D6A4F', '#0891B2', '#B91C1C', '#A4865F', '#2563EB', '#D97706', '#DC2626']}
            swatchesPerRow={8}
            size="sm"
          />
        </div>
        <div className="sp-field">
          <span className="sp-field-label">Keyboard Shortcuts</span>
          <div className="sp-shortcut-hints" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 4 }}>
            <Group gap={4}>
              <Kbd>⌘</Kbd><Text span size="xs" c="dimmed">+</Text><Kbd>K</Kbd>
              <Text span size="xs" c="dimmed" ml={2}>Command palette</Text>
            </Group>
            <Group gap={4}>
              <Kbd>⌘</Kbd><Text span size="xs" c="dimmed">+</Text><Kbd>/</Kbd>
              <Text span size="xs" c="dimmed" ml={2}>Shortcuts</Text>
            </Group>
            <Group gap={4}>
              <Kbd>⌘</Kbd><Text span size="xs" c="dimmed">+</Text><Kbd>Z</Kbd>
              <Text span size="xs" c="dimmed" ml={2}>Undo</Text>
            </Group>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Data Section ──

function DataSection() {
  const [exporting, setExporting] = useState<'json' | 'csv' | null>(null);
  const [exportMsg, setExportMsg] = useState('');

  const handleExport = async (format: 'json' | 'csv') => {
    setExporting(format);
    setExportMsg('');
    try {
      const resp = await fetch('/api/v1/objects?limit=1000', { credentials: 'include' });
      const data = await resp.json();
      const objects: any[] = (data?.data?.objects || data?.objects || []) as any[];

      if (format === 'json') {
        const blob = new Blob([JSON.stringify(objects, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `shunya-export-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        const allKeys = [...new Set(objects.flatMap((o: any) => Object.keys(o)))];
        const csvRows = [allKeys.join(',')];
        objects.forEach((o: any) => {
          csvRows.push(allKeys.map(k => {
            const val = o[k];
            if (val === null || val === undefined) return '';
            const str = String(val).replace(/"/g, '""');
            return `"${str}"`;
          }).join(','));
        });
        const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `shunya-export-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      }
      setExportMsg(`Data exported successfully as ${format.toUpperCase()}.`);
    } catch {
      setExportMsg('Export failed — could not fetch data.');
    } finally {
      setExporting(null);
      setTimeout(() => setExportMsg(''), 4000);
    }
  };

  return (
    <div className="sp-section">
      <div className="sp-section-header">
        <Download size={14} style={{ color: accentColor }} />
        <span className="sp-section-title">Data</span>
      </div>
      <div className="sp-card">
        <p className="sp-card-desc">Export all your SHUNYA data. This includes objects, settings, and workspace information.</p>
        <div className="sp-export-actions">
          <button
            className="sp-btn sp-btn-primary"
            onClick={() => handleExport('json')}
            disabled={exporting !== null}
          >
            {exporting === 'json' ? <RefreshCw size={13} className="sp-spin" /> : <FileDown size={13} />}
            {exporting === 'json' ? 'Exporting...' : 'Export as JSON'}
          </button>
          <button
            className="sp-btn sp-btn-primary"
            onClick={() => handleExport('csv')}
            disabled={exporting !== null}
          >
            {exporting === 'csv' ? <RefreshCw size={13} className="sp-spin" /> : <FileDown size={13} />}
            {exporting === 'csv' ? 'Exporting...' : 'Export as CSV'}
          </button>
        </div>
        {exportMsg && (
          <div className="sp-export-msg">{exportMsg}</div>
        )}
      </div>
    </div>
  );
}

// ── Security Section (MFA via real API) ──

function SecuritySection() {
  return <MfaSetup />;
}

// ── Payment Section (Razorpay Integration) ──

function PaymentSection() {
  const [loading, setLoading] = useState(true);
  const [configured, setConfigured] = useState(false);
  const [keyId, setKeyId] = useState('');
  const [keySecret, setKeySecret] = useState('');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/v1/razorpay/status', { credentials: 'include' });
      const data = await resp.json();
      setConfigured(data.configured === true);
    } catch {
      setConfigured(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveKeys = async () => {
    if (!keyId.trim() || !keySecret.trim()) {
      setMsg({ type: 'error', text: 'Please enter both Key ID and Key Secret.' });
      return;
    }
    setSaving(true);
    setMsg(null);
    try {
      const resp = await fetch('/api/v1/razorpay/save-keys', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key_id: keyId.trim(), key_secret: keySecret.trim() }),
      });
      const data = await resp.json();
      if (data.success) {
        setMsg({ type: 'success', text: 'Razorpay keys saved successfully!' });
        setConfigured(true);
        setKeyId('');
        setKeySecret('');
      } else {
        setMsg({ type: 'error', text: data.error || 'Failed to save keys.' });
      }
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message || 'Network error.' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setMsg(null);
    try {
      const resp = await fetch('/api/v1/razorpay/test-connection', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await resp.json();
      if (data.success) {
        setMsg({ type: 'success', text: 'Connection successful! Razorpay API keys are valid.' });
      } else {
        setMsg({ type: 'error', text: data.error || 'Connection test failed.' });
      }
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message || 'Network error.' });
    } finally {
      setTesting(false);
    }
  };

  const handleDisconnect = async () => {
    // Clear keys by saving empty strings
    setSaving(true);
    try {
      const resp = await fetch('/api/v1/razorpay/save-keys', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key_id: '', key_secret: '' }),
      });
      const data = await resp.json();
      if (data.success) {
        setConfigured(false);
        setMsg({ type: 'success', text: 'Razorpay disconnected.' });
      } else {
        setMsg({ type: 'error', text: data.error || 'Failed to disconnect.' });
      }
    } catch (err: any) {
      setMsg({ type: 'error', text: err.message || 'Network error.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="sp-section">
        <div className="sp-section-header">
          <CreditCard size={14} style={{ color: accentColor }} />
          <span className="sp-section-title">Payments</span>
        </div>
        <div className="sp-card">
          <RefreshCw size={13} className="sp-spin" />
          <span className="sp-card-desc">Checking payment configuration...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="sp-section">
      <div className="sp-section-header">
        <CreditCard size={14} style={{ color: accentColor }} />
        <span className="sp-section-title">Payments</span>
      </div>
      <div className="sp-card">
        <p className="sp-card-desc">
          Configure Razorpay to accept payments via UPI, cards, and net banking.
          {configured
            ? ' Your payment gateway is active.'
            : ' No payment gateway configured yet.'}
        </p>

        {configured ? (
          <>
            <div className="sp-field" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <span className="sp-export-msg" style={{ color: '#2D6A4F' }}>
                ✓ Razorpay Connected
              </span>
            </div>
            <div className="sp-export-actions" style={{ gap: 6 }}>
              <button
                className="sp-btn sp-btn-primary"
                onClick={handleTestConnection}
                disabled={testing}
              >
                {testing ? <RefreshCw size={13} className="sp-spin" /> : null}
                {testing ? 'Testing...' : 'Test Connection'}
              </button>
              <button
                className="sp-btn"
                onClick={handleDisconnect}
                disabled={saving}
              >
                Disconnect
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="sp-field">
              <span className="sp-field-label">Razorpay Key ID</span>
              <input
                className="sp-input"
                type="text"
                value={keyId}
                onChange={e => setKeyId(e.target.value)}
                placeholder="rzp_live_..."
              />
            </div>
            <div className="sp-field">
              <span className="sp-field-label">Razorpay Key Secret</span>
              <input
                className="sp-input"
                type="password"
                value={keySecret}
                onChange={e => setKeySecret(e.target.value)}
                placeholder="Enter your secret key"
              />
            </div>
            <div className="sp-export-actions" style={{ gap: 6 }}>
              <button
                className="sp-btn sp-btn-primary"
                onClick={handleSaveKeys}
                disabled={saving}
              >
                {saving ? <RefreshCw size={13} className="sp-spin" /> : null}
                {saving ? 'Saving...' : 'Save Keys'}
              </button>
            </div>
            <p className="sp-card-desc" style={{ marginTop: 6 }}>
              Don't have a Razorpay account?{' '}
              <a
                href="https://razorpay.com"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: accentColor, fontWeight: 600 }}
              >
                Sign up for free
              </a>
            </p>
          </>
        )}

        {msg && (
          <div
            className="sp-export-msg"
            style={{
              color: msg.type === 'success' ? '#2D6A4F' : '#C62828',
              marginTop: 6,
            }}
          >
            {msg.text}
          </div>
        )}
      </div>
    </div>
  );
}

// ── AI Model Section ──

const AI_MODELS = [
  'Groq (default)',
  'Gemini',
  'OpenRouter',
  'Cloudflare',
  'HuggingFace',
  'Together',
  'Anthropic',
];

function AiModelSection() {
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    try { return localStorage.getItem('shunya_ai_model') || 'Groq (default)'; } catch { return 'Groq (default)'; }
  });

  const handleModelChange = (value: string | null) => {
    const model = value || 'Groq (default)';
    setSelectedModel(model);
    try { localStorage.setItem('shunya_ai_model', model); } catch { /* localStorage unavailable */ }
  };

  return (
    <div className="sp-section">
      <div className="sp-section-header">
        <Sparkles size={14} style={{ color: accentColor }} />
        <span className="sp-section-title">AI Model</span>
      </div>
      <div className="sp-card">
        <p className="sp-card-desc">
          Select the AI provider to use for assistant queries and generation tasks.
        </p>
        <div className="sp-field">
          <span className="sp-field-label">Provider</span>
          <Select
            data={AI_MODELS}
            value={selectedModel}
            onChange={handleModelChange}
            allowDeselect={false}
            comboboxProps={{ withinPortal: true }}
            styles={{
              input: {
                background: 'rgba(255,255,255,0.8)',
                border: '1px solid rgba(26,28,29,0.08)',
                fontSize: 13,
                color: '#1A1C1D',
                '&:focus': {
                  borderColor: accentColor,
                  boxShadow: `0 0 0 2px ${accentColor}1A`,
                },
              },
              dropdown: {
                background: 'rgba(255,255,255,0.95)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(26,28,29,0.08)',
              },
              option: {
                fontSize: 13,
                color: '#1A1C1D',
                '&[data-selected]': {
                  background: `${accentColor}12`,
                  color: accentColor,
                },
                '&[data-hovered]': {
                  background: 'rgba(108,74,226,0.06)',
                },
              },
            }}
          />
        </div>
        <div className="sp-ai-info">
          <ThemeIcon size={20} radius="xl" color="violet" variant="light">
            <Sparkles size={12} />
          </ThemeIcon>
          <span className="sp-ai-info-text">
            {selectedModel === 'Groq (default)'
              ? 'Fast AI with Groq LPUs. Change to use a different provider.'
              : `Using ${selectedModel} for AI operations.`}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Main Settings Panel ──

export function SettingsPanel() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [isDark, setIsDark] = useState<boolean>(() => {
    try { return localStorage.getItem('shunya-theme') === 'dark'; } catch { return false; }
  });
  const [themeColor, setThemeColor] = useState<string>(() => {
    try { return (localStorage.getItem('shunya-accent-color') as ThemeColor) || '#6C4AE2'; } catch { return '#6C4AE2'; }
  });
  const [profile, setProfile] = useState<ProfileInfo>(() => {
    try {
      const session = SessionManager.load();
      const name = session?.name || '';
      const email = session?.email || '';
      return {
        name,
        email,
        avatarInitial: (name || email || 'U').charAt(0).toUpperCase(),
      };
    } catch {
      return { name: '', email: '', avatarInitial: 'U' };
    }
  });

  // Persist dark mode
  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.setAttribute('data-theme', 'dark');
      root.style.colorScheme = 'dark';
    } else {
      root.removeAttribute('data-theme');
      root.style.colorScheme = 'light';
    }
    localStorage.setItem('shunya-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // Persist accent color
  useEffect(() => {
    localStorage.setItem('shunya-accent-color', themeColor);
    document.documentElement.style.setProperty('--sh-accent', themeColor);
  }, [themeColor]);

  const handleNameChange = (name: string) => {
    setProfile(p => ({ ...p, name, avatarInitial: name.charAt(0).toUpperCase() }));
    try {
      const session = SessionManager.load();
      if (session) {
        SessionManager.save({ ...session, name });
      }
    } catch { /* ignore */ }
  };

  return (
    <div className="sp-container">
      {/* Header */}
      <div className="sp-header">
        <div className="sp-header-left">
          <div className="sp-header-icon" style={{ background: 'rgba(108,74,226,0.08)', color: accentColor }}>
            <Settings size={18} />
          </div>
          <div>
            <div className="sp-header-title">Settings</div>
            <div className="sp-header-sub">Manage your profile, appearance, and data</div>
          </div>
        </div>
      </div>

      {/* Sub-tabs */}
      <div className="sp-tabs">
        {TABS.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              className={`sp-tab ${isActive ? 'sp-tab-active' : ''}`}
              style={isActive ? { borderBottomColor: accentColor, color: accentColor } : {}}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={12} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="sp-content">
        {activeTab === 'profile' && <ProfileSection profile={profile} onNameChange={handleNameChange} />}
        {activeTab === 'appearance' && <AppearanceSection isDark={isDark} setIsDark={setIsDark} themeColor={themeColor} setThemeColor={setThemeColor} />}
        {activeTab === 'ai' && <AiModelSection />}
        {activeTab === 'security' && <SecuritySection />}
        {activeTab === 'data' && <DataSection />}
        {activeTab === 'payments' && <PaymentSection />}
        {activeTab === 'integrations' && <IntegrationHub />}
      </div>

      <style>{spCss}</style>
    </div>
  );
}

// ── Styles ──

const spCss = `
.sp-container { display: flex; flex-direction: column; gap: 14px; padding: 18px; width: 100%; }
.sp-header { display: flex; align-items: center; justify-content: space-between; }
.sp-header-left { display: flex; align-items: center; gap: 10px; }
.sp-header-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.sp-header-title { font-size: 15px; font-weight: 600; color: #1A1C1D; }
.sp-header-sub { font-size: 11px; color: rgba(26,28,29,0.45); margin-top: 1px; }

/* Tabs */
.sp-tabs { display: flex; gap: 0; border-bottom: 1px solid rgba(26,28,29,0.06); flex-wrap: wrap; overflow-x: auto; }
.sp-tab { display: flex; align-items: center; gap: 5px; padding: 8px 12px; border: none; background: transparent; cursor: pointer; font-size: 11px; font-weight: 500; color: rgba(26,28,29,0.35); font-family: inherit; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: all 0.15s; white-space: nowrap; }
.sp-tab:hover { color: rgba(26,28,29,0.55); }
.sp-tab-active { color: #6C4AE2 !important; }

/* Content */
.sp-content { display: flex; flex-direction: column; gap: 14px; width: 100%; }
.sp-section { display: flex; flex-direction: column; gap: 6px; }
.sp-section-header { display: flex; align-items: center; gap: 6px; padding: 8px 10px; background: rgba(255,255,255,0.5); border-radius: 8px; border-left: 3px solid #6C4AE2; font-size: 10px; font-weight: 600; color: rgba(26,28,29,0.5); text-transform: uppercase; letter-spacing: 0.06em; }

/* Card */
.sp-card { background: rgba(255,255,255,0.5); backdrop-filter: blur(4px); border: 1px solid rgba(26,28,29,0.04); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.sp-card-desc { font-size: 11px; color: rgba(26,28,29,0.45); margin: 0; line-height: 1.4; }

/* Avatar */
.sp-avatar-row { display: flex; align-items: center; gap: 12px; }
.sp-avatar { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 700; color: #fff; flex-shrink: 0; }
.sp-avatar-info { display: flex; flex-direction: column; gap: 1px; }
.sp-avatar-name { font-size: 14px; font-weight: 600; color: #1A1C1D; }
.sp-avatar-email { font-size: 11px; color: rgba(26,28,29,0.45); }

/* Fields */
.sp-field { display: flex; flex-direction: column; gap: 4px; }
.sp-field-label { font-size: 10px; font-weight: 600; color: rgba(26,28,29,0.45); text-transform: uppercase; letter-spacing: 0.06em; }
.sp-field-row { display: flex; align-items: center; gap: 6px; }
.sp-value { font-size: 13px; color: #1A1C1D; flex: 1; }
.sp-value-readonly { opacity: 0.6; }
.sp-input { flex: 1; padding: 6px 10px; border: 1px solid rgba(26,28,29,0.08); border-radius: 6px; background: rgba(255,255,255,0.8); font-size: 12px; color: #1A1C1D; font-family: inherit; outline: none; }
.sp-input:focus { border-color: #6C4AE2; box-shadow: 0 0 0 2px rgba(108,74,226,0.1); }

/* Buttons */
.sp-btn { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border: 1px solid rgba(26,28,29,0.08); border-radius: 6px; background: rgba(255,255,255,0.6); font-size: 11px; font-weight: 500; color: rgba(26,28,29,0.6); cursor: pointer; font-family: inherit; transition: all 0.15s; }
.sp-btn:hover { border-color: rgba(26,28,29,0.15); color: #1A1C1D; }
.sp-btn:disabled { opacity: 0.5; cursor: default; }
.sp-btn-primary { border-color: rgba(108,74,226,0.2); background: rgba(108,74,226,0.06); color: #6C4AE2; }
.sp-btn-primary:hover:not(:disabled) { background: rgba(108,74,226,0.12); border-color: #6C4AE2; }

/* Toggle */
.sp-toggle-row { display: flex; gap: 4px; }
.sp-toggle-btn { display: inline-flex; align-items: center; gap: 5px; padding: 5px 14px; border: 1px solid rgba(26,28,29,0.06); border-radius: 8px; background: transparent; font-size: 11px; font-weight: 500; color: rgba(26,28,29,0.45); cursor: pointer; font-family: inherit; transition: all 0.15s; }
.sp-toggle-btn:hover { border-color: rgba(26,28,29,0.12); color: #1A1C1D; }
.sp-toggle-active { background: rgba(108,74,226,0.06) !important; border-color: rgba(108,74,226,0.2) !important; color: #6C4AE2 !important; }

/* Color picker */
.sp-color-row { display: flex; gap: 8px; flex-wrap: wrap; }
.sp-color-swatch { width: 28px; height: 28px; border-radius: 50%; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.15s; }
.sp-color-swatch:hover { transform: scale(1.15); }

/* Export */
.sp-export-actions { display: flex; gap: 6px; }
.sp-export-msg { font-size: 11px; color: #2D6A4F; font-weight: 500; }

/* Spin */
.sp-spin { animation: sp-rotate 0.8s linear infinite; }
@keyframes sp-rotate { to { transform: rotate(360deg); } }

/* AI Model section */
.sp-ai-info { display: flex; align-items: center; gap: 8px; padding: 6px 8px; background: rgba(108,74,226,0.04); border-radius: 8px; margin-top: 2px; }
.sp-ai-info-text { font-size: 10px; color: rgba(26,28,29,0.45); line-height: 1.4; }

@media (max-width: 768px) {
  .sp-container { padding: 14px; }
  .sp-header-title { font-size: 14px; }
}
@media (max-width: 480px) {
  .sp-tab { padding: 8px 10px; font-size: 10px; }
}
`;