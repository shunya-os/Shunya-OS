/**
 * Profile Page — General, Preferences, Password, Avatar management.
 * Warm-light design, Tabler icons, inline <style> CSS.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  IconUser, IconSettings, IconLock, IconCamera,
  IconMail, IconPhone, IconWorld, IconCalendar,
  IconSun, IconMoon, IconDeviceDesktop, IconFileDescription,
} from '@tabler/icons-react';

// ── Types ──

interface UserProfile {
  identity_id: string;
  display_name: string;
  email: string;
  phone: string;
  avatar_url: string;
  timezone: string;
  locale: string;
  date_format: string;
  bio: string;
  theme_preference: 'light' | 'dark' | 'system';
  created_at: string | null;
  updated_at: string | null;
}

type ProfileTab = 'general' | 'preferences' | 'password' | 'avatar';

const accentColor = '#D4A030'; // warm gold

const TABS: { id: ProfileTab; label: string; icon: any }[] = [
  { id: 'general', label: 'General', icon: IconUser },
  { id: 'preferences', label: 'Preferences', icon: IconSettings },
  { id: 'password', label: 'Password', icon: IconLock },
  { id: 'avatar', label: 'Avatar', icon: IconCamera },
];

// ── Helpers ──

async function fetchProfile(): Promise<UserProfile | null> {
  try {
    const res = await fetch('/api/v1/profile');
    const body = await res.json();
    if (body.success && body.data) return body.data;
    return null;
  } catch { return null; }
}

async function updateProfile(data: Partial<UserProfile>): Promise<boolean> {
  try {
    const res = await fetch('/api/v1/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const body = await res.json();
    return body.success === true;
  } catch { return false; }
}

async function updatePreferences(prefs: Record<string, string>): Promise<boolean> {
  try {
    const res = await fetch('/api/v1/profile/preferences', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(prefs),
    });
    const body = await res.json();
    return body.success === true;
  } catch { return false; }
}

async function changePassword(oldPassword: string, newPassword: string): Promise<{ success: boolean; error?: string }> {
  try {
    const res = await fetch('/api/v1/profile/password', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });
    const body = await res.json();
    return { success: body.success === true, error: body.error };
  } catch { return { success: false, error: 'Network error' }; }
}

async function uploadAvatar(file: File): Promise<string | null> {
  try {
    const fd = new FormData();
    fd.append('avatar', file);
    const res = await fetch('/api/v1/profile/avatar', { method: 'POST', body: fd });
    const body = await res.json();
    if (body.success && body.data?.avatar_url) return body.data.avatar_url;
    return null;
  } catch { return null; }
}

// ── General Section ──

function GeneralSection({ profile, onUpdated }: { profile: UserProfile; onUpdated: (p: UserProfile) => void }) {
  const [name, setName] = useState(profile.display_name);
  const [email, setEmail] = useState(profile.email);
  const [phone, setPhone] = useState(profile.phone);
  const [bio, setBio] = useState(profile.bio);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const handleSave = useCallback(async () => {
    setSaving(true);
    setMsg('');
    const ok = await updateProfile({ display_name: name, email, phone, bio });
    if (ok) {
      setMsg('Saved');
      onUpdated({ ...profile, display_name: name, email, phone, bio });
    } else {
      setMsg('Failed to save');
    }
    setSaving(false);
    setTimeout(() => setMsg(''), 2500);
  }, [name, email, phone, bio, profile, onUpdated]);

  return (
    <div className="pp-section">
      <div className="pp-section-header">
        <IconUser size={14} style={{ color: accentColor }} />
        <span className="pp-section-title">General Information</span>
      </div>
      <div className="pp-card">
        <div className="pp-field">
          <span className="pp-field-label">Display Name</span>
          <input className="pp-input" value={name} onChange={e => setName(e.target.value)} placeholder="Your name" />
        </div>
        <div className="pp-field">
          <span className="pp-field-label">Email</span>
          <div className="pp-field-row">
            <IconMail size={12} className="pp-field-icon" />
            <input className="pp-input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="email@example.com" />
          </div>
        </div>
        <div className="pp-field">
          <span className="pp-field-label">Phone</span>
          <div className="pp-field-row">
            <IconPhone size={12} className="pp-field-icon" />
            <input className="pp-input" type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="+1 555 000 0000" />
          </div>
        </div>
        <div className="pp-field">
          <span className="pp-field-label">Bio</span>
          <div className="pp-field-row">
            <IconFileDescription size={12} className="pp-field-icon" />
            <textarea className="pp-textarea" value={bio} onChange={e => setBio(e.target.value)} placeholder="A short bio…" rows={3} />
          </div>
        </div>
        <div className="pp-actions">
          <button className="pp-btn pp-btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
          {msg && <span className="pp-msg">{msg}</span>}
        </div>
      </div>
    </div>
  );
}

// ── Preferences Section ──

const TIMEZONES = [
  'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Moscow',
  'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata', 'Asia/Dubai',
  'Australia/Sydney', 'Pacific/Auckland',
];

const LOCALES = [
  { value: 'en-US', label: 'English (US)' },
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'fr-FR', label: 'Français' },
  { value: 'de-DE', label: 'Deutsch' },
  { value: 'es-ES', label: 'Español' },
  { value: 'ja-JP', label: '日本語' },
  { value: 'zh-CN', label: '中文' },
];

const DATE_FORMATS = [
  { value: 'YYYY-MM-DD', label: '2025-05-15' },
  { value: 'DD/MM/YYYY', label: '15/05/2025' },
  { value: 'MM/DD/YYYY', label: '05/15/2025' },
  { value: 'DD.MM.YYYY', label: '15.05.2025' },
];

function PreferencesSection({ profile, onUpdated }: { profile: UserProfile; onUpdated: (p: UserProfile) => void }) {
  const [timezone, setTimezone] = useState(profile.timezone);
  const [locale, setLocale] = useState(profile.locale);
  const [dateFormat, setDateFormat] = useState(profile.date_format);
  const [theme, setTheme] = useState(profile.theme_preference);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const handleSave = useCallback(async () => {
    setSaving(true);
    setMsg('');
    const ok = await updatePreferences({ timezone, locale, date_format: dateFormat, theme_preference: theme });
    if (ok) {
      setMsg('Saved');
      onUpdated({ ...profile, timezone, locale, date_format: dateFormat, theme_preference: theme as any });
    } else {
      setMsg('Failed to save');
    }
    setSaving(false);
    setTimeout(() => setMsg(''), 2500);
  }, [timezone, locale, dateFormat, theme, profile, onUpdated]);

  return (
    <div className="pp-section">
      <div className="pp-section-header">
        <IconSettings size={14} style={{ color: accentColor }} />
        <span className="pp-section-title">Preferences</span>
      </div>
      <div className="pp-card">
        <div className="pp-field">
          <span className="pp-field-label">Timezone</span>
          <div className="pp-field-row">
            <IconWorld size={12} className="pp-field-icon" />
            <select className="pp-select" value={timezone} onChange={e => setTimezone(e.target.value)}>
              {TIMEZONES.map(tz => <option key={tz} value={tz}>{tz}</option>)}
            </select>
          </div>
        </div>
        <div className="pp-field">
          <span className="pp-field-label">Locale</span>
          <div className="pp-field-row">
            <IconWorld size={12} className="pp-field-icon" />
            <select className="pp-select" value={locale} onChange={e => setLocale(e.target.value)}>
              {LOCALES.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
        </div>
        <div className="pp-field">
          <span className="pp-field-label">Date Format</span>
          <div className="pp-field-row">
            <IconCalendar size={12} className="pp-field-icon" />
            <select className="pp-select" value={dateFormat} onChange={e => setDateFormat(e.target.value)}>
              {DATE_FORMATS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
            </select>
          </div>
        </div>
        <div className="pp-field">
          <span className="pp-field-label">Theme</span>
          <div className="pp-toggle-row">
            <button
              className={`pp-toggle-btn ${theme === 'light' ? 'pp-toggle-active' : ''}`}
              onClick={() => setTheme('light')}
            >
              <IconSun size={12} /> Light
            </button>
            <button
              className={`pp-toggle-btn ${theme === 'dark' ? 'pp-toggle-active' : ''}`}
              onClick={() => setTheme('dark')}
            >
              <IconMoon size={12} /> Dark
            </button>
            <button
              className={`pp-toggle-btn ${theme === 'system' ? 'pp-toggle-active' : ''}`}
              onClick={() => setTheme('system')}
            >
              <IconDeviceDesktop size={12} /> System
            </button>
          </div>
        </div>
        <div className="pp-actions">
          <button className="pp-btn pp-btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save Preferences'}
          </button>
          {msg && <span className="pp-msg">{msg}</span>}
        </div>
      </div>
    </div>
  );
}

// ── Password Section ──

function PasswordSection() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  const handleChange = useCallback(async () => {
    setMsg('');
    setError('');

    if (!oldPassword || !newPassword) {
      setError('Both fields are required');
      return;
    }
    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setSaving(true);
    const result = await changePassword(oldPassword, newPassword);
    if (result.success) {
      setMsg('Password updated successfully');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } else {
      setError(result.error || 'Failed to update password');
    }
    setSaving(false);
    setTimeout(() => { setMsg(''); setError(''); }, 3000);
  }, [oldPassword, newPassword, confirmPassword]);

  return (
    <div className="pp-section">
      <div className="pp-section-header">
        <IconLock size={14} style={{ color: accentColor }} />
        <span className="pp-section-title">Change Password</span>
      </div>
      <div className="pp-card">
        <p className="pp-card-desc">Your password must be at least 8 characters.</p>
        <div className="pp-field">
          <span className="pp-field-label">Current Password</span>
          <input className="pp-input" type="password" value={oldPassword} onChange={e => setOldPassword(e.target.value)} placeholder="Enter current password" />
        </div>
        <div className="pp-field">
          <span className="pp-field-label">New Password</span>
          <input className="pp-input" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="Enter new password" />
        </div>
        <div className="pp-field">
          <span className="pp-field-label">Confirm New Password</span>
          <input className="pp-input" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="Confirm new password" />
        </div>
        <div className="pp-actions">
          <button className="pp-btn pp-btn-primary" onClick={handleChange} disabled={saving}>
            {saving ? 'Updating…' : 'Update Password'}
          </button>
          {msg && <span className="pp-msg">{msg}</span>}
          {error && <span className="pp-msg pp-msg-error">{error}</span>}
        </div>
      </div>
    </div>
  );
}

// ── Avatar Section ──

function AvatarSection({ profile, onUpdated }: { profile: UserProfile; onUpdated: (p: UserProfile) => void }) {
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState('');
  const [preview, setPreview] = useState<string | null>(null);
  const fileRef = useState<HTMLInputElement | null>(null);

  const handleFile = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (ev) => setPreview(ev.target?.result as string);
    reader.readAsDataURL(file);

    setUploading(true);
    setMsg('');
    const url = await uploadAvatar(file);
    if (url) {
      setMsg('Avatar updated');
      onUpdated({ ...profile, avatar_url: url });
    } else {
      setMsg('Upload failed');
      setPreview(null);
    }
    setUploading(false);
    setTimeout(() => setMsg(''), 2500);
  }, [profile, onUpdated]);

  const currentAvatar = preview || profile.avatar_url;

  return (
    <div className="pp-section">
      <div className="pp-section-header">
        <IconCamera size={14} style={{ color: accentColor }} />
        <span className="pp-section-title">Avatar</span>
      </div>
      <div className="pp-card">
        <p className="pp-card-desc">Upload a profile picture. Supports JPEG, PNG, WebP, and GIF.</p>
        <div className="pp-avatar-area">
          <div className="pp-avatar-preview" style={{ background: currentAvatar ? `url(${currentAvatar}) center/cover no-repeat` : 'rgba(26,28,29,0.04)' }}>
            {!currentAvatar && <IconUser size={32} style={{ color: 'rgba(26,28,29,0.2)' }} />}
          </div>
          <label className="pp-btn pp-btn-primary" style={{ cursor: 'pointer' }}>
            {uploading ? 'Uploading…' : 'Choose Image'}
            <input
              ref={el => { /* attach ref */ fileRef[1](el); }}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              style={{ display: 'none' }}
              onChange={handleFile}
              disabled={uploading}
            />
          </label>
          {msg && <span className="pp-msg">{msg}</span>}
        </div>
      </div>
    </div>
  );
}

// ── Main Export ──

export function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<ProfileTab>('general');

  useEffect(() => {
    fetchProfile().then(p => {
      setProfile(p);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="pp-container">
        <div className="pp-loading">Loading profile…</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="pp-container">
        <div className="pp-error" role="alert">Could not load profile. Please try again.</div>
      </div>
    );
  }

  return (
    <div className="pp-container">
      {/* Header */}
      <div className="pp-header">
        <div className="pp-header-left">
          <div className="pp-header-icon" style={{ background: 'rgba(212,160,48,0.08)', color: accentColor }}>
            <IconUser size={18} />
          </div>
          <div>
            <div className="pp-header-title">Profile</div>
            <div className="pp-header-sub">Manage your profile, preferences, and security</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="pp-tabs">
        {TABS.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              className={`pp-tab ${isActive ? 'pp-tab-active' : ''}`}
              style={isActive ? { borderBottomColor: accentColor, color: accentColor } : {}}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={12} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="pp-content">
        {activeTab === 'general' && <GeneralSection profile={profile} onUpdated={setProfile} />}
        {activeTab === 'preferences' && <PreferencesSection profile={profile} onUpdated={setProfile} />}
        {activeTab === 'password' && <PasswordSection />}
        {activeTab === 'avatar' && <AvatarSection profile={profile} onUpdated={setProfile} />}
      </div>

      <style>{ppCss}</style>
    </div>
  );
}

// ── Styles ──

const ppCss = `
.pp-container { display: flex; flex-direction: column; gap: 14px; padding: 18px; width: 100%; max-width: 600px; }
.pp-header { display: flex; align-items: center; justify-content: space-between; }
.pp-header-left { display: flex; align-items: center; gap: 10px; }
.pp-header-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.pp-header-title { font-size: 15px; font-weight: 600; color: #1A1C1D; }
.pp-header-sub { font-size: 11px; color: rgba(26,28,29,0.45); margin-top: 1px; }

/* Tabs */
.pp-tabs { display: flex; gap: 0; border-bottom: 1px solid rgba(26,28,29,0.06); flex-wrap: wrap; overflow-x: auto; }
.pp-tab { display: flex; align-items: center; gap: 5px; padding: 8px 12px; border: none; background: transparent; cursor: pointer; font-size: 11px; font-weight: 500; color: rgba(26,28,29,0.35); font-family: inherit; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: all 0.15s; white-space: nowrap; }
.pp-tab:hover { color: rgba(26,28,29,0.55); }
.pp-tab-active { color: ${accentColor} !important; }

/* Content */
.pp-content { display: flex; flex-direction: column; gap: 14px; width: 100%; }
.pp-section { display: flex; flex-direction: column; gap: 6px; }
.pp-section-header { display: flex; align-items: center; gap: 6px; padding: 8px 10px; background: rgba(255,255,255,0.5); border-radius: 8px; border-left: 3px solid ${accentColor}; font-size: 10px; font-weight: 600; color: rgba(26,28,29,0.5); text-transform: uppercase; letter-spacing: 0.06em; }

/* Card */
.pp-card { background: rgba(255,255,255,0.5); backdrop-filter: blur(4px); border: 1px solid rgba(26,28,29,0.04); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.pp-card-desc { font-size: 11px; color: rgba(26,28,29,0.45); margin: 0; line-height: 1.4; }

/* Fields */
.pp-field { display: flex; flex-direction: column; gap: 4px; }
.pp-field-label { font-size: 10px; font-weight: 600; color: rgba(26,28,29,0.45); text-transform: uppercase; letter-spacing: 0.06em; }
.pp-field-row { display: flex; align-items: center; gap: 6px; }
.pp-field-icon { color: rgba(26,28,29,0.25); flex-shrink: 0; }

.pp-input { flex: 1; padding: 6px 10px; border: 1px solid rgba(26,28,29,0.08); border-radius: 6px; background: rgba(255,255,255,0.8); font-size: 12px; color: #1A1C1D; font-family: inherit; outline: none; }
.pp-input:focus { border-color: ${accentColor}; box-shadow: 0 0 0 2px rgba(212,160,48,0.1); }

.pp-textarea { flex: 1; padding: 6px 10px; border: 1px solid rgba(26,28,29,0.08); border-radius: 6px; background: rgba(255,255,255,0.8); font-size: 12px; color: #1A1C1D; font-family: inherit; outline: none; resize: vertical; min-height: 52px; }
.pp-textarea:focus { border-color: ${accentColor}; box-shadow: 0 0 0 2px rgba(212,160,48,0.1); }

.pp-select { flex: 1; padding: 6px 10px; border: 1px solid rgba(26,28,29,0.08); border-radius: 6px; background: rgba(255,255,255,0.8); font-size: 12px; color: #1A1C1D; font-family: inherit; outline: none; cursor: pointer; }
.pp-select:focus { border-color: ${accentColor}; box-shadow: 0 0 0 2px rgba(212,160,48,0.1); }

/* Buttons */
.pp-btn { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border: 1px solid rgba(26,28,29,0.08); border-radius: 6px; background: rgba(255,255,255,0.6); font-size: 11px; font-weight: 500; color: rgba(26,28,29,0.6); cursor: pointer; font-family: inherit; transition: all 0.15s; }
.pp-btn:hover { border-color: rgba(26,28,29,0.15); color: #1A1C1D; }
.pp-btn:disabled { opacity: 0.5; cursor: default; }
.pp-btn-primary { border-color: rgba(212,160,48,0.2); background: rgba(212,160,48,0.06); color: ${accentColor}; }
.pp-btn-primary:hover:not(:disabled) { background: rgba(212,160,48,0.12); border-color: ${accentColor}; }

/* Toggle */
.pp-toggle-row { display: flex; gap: 4px; }
.pp-toggle-btn { display: inline-flex; align-items: center; gap: 5px; padding: 5px 14px; border: 1px solid rgba(26,28,29,0.06); border-radius: 8px; background: transparent; font-size: 11px; font-weight: 500; color: rgba(26,28,29,0.45); cursor: pointer; font-family: inherit; transition: all 0.15s; }
.pp-toggle-btn:hover { border-color: rgba(26,28,29,0.12); color: #1A1C1D; }
.pp-toggle-active { background: rgba(212,160,48,0.06) !important; border-color: rgba(212,160,48,0.2) !important; color: ${accentColor} !important; }

/* Messages */
.pp-actions { display: flex; align-items: center; gap: 8px; margin-top: 2px; }
.pp-msg { font-size: 11px; color: #2D6A4F; font-weight: 500; }
.pp-msg-error { color: #B91C1C; }

/* Avatar */
.pp-avatar-area { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 16px; }
.pp-avatar-preview { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid rgba(26,28,29,0.06); overflow: hidden; }

/* Loading / Error */
.pp-loading, .pp-error { font-size: 13px; color: rgba(26,28,29,0.45); padding: 24px; text-align: center; }
.pp-error { color: #B91C1C; }

@media (max-width: 768px) {
  .pp-container { padding: 14px; max-width: 100%; }
  .pp-header-title { font-size: 14px; }
}
@media (max-width: 480px) {
  .pp-tab { padding: 8px 10px; font-size: 10px; }
}
`;