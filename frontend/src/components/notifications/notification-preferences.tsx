/**
 * Notification Preferences — event_type × channel toggle matrix.
 *
 * Renders a table of toggle switches allowing the user to enable or
 * disable each notification channel per event type.
 *
 * GET  /api/v1/notifications/preferences → { grouped: { event_type: { channel: bool } } }
 * PUT  /api/v1/notifications/preferences → { preferences: [{ event_type, channel, enabled }] }
 */
import { useState, useEffect, useCallback } from 'react';
import { IconBell, IconMail, IconDeviceMobile, IconBrowser, IconBellOff } from '@tabler/icons-react';

const CHANNEL_LABELS: Record<string, { label: string; icon: React.ReactNode }> = {
  email:   { label: 'Email',   icon: <IconMail size={14} /> },
  push:    { label: 'Push',    icon: <IconDeviceMobile size={14} /> },
  'in-app': { label: 'In-App', icon: <IconBell size={14} /> },
  browser: { label: 'Browser', icon: <IconBrowser size={14} /> },
};

const CHANNEL_ORDER = ['in-app', 'push', 'email', 'browser'];

type PreferencesMap = Record<string, Record<string, boolean>>;

export function NotificationPreferences() {
  const [prefs, setPrefs] = useState<PreferencesMap>({});
  const [eventTypes, setEventTypes] = useState<string[]>([]);
  const [channels, setChannels] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const r = await fetch('/api/v1/notifications/preferences', { credentials: 'include' });
      const d = await r.json();
      if (d.success) {
        setPrefs(d.grouped || {});
        setEventTypes(d.event_types || []);
        setChannels(d.channels || []);
      } else {
        setError(d.error || 'Failed to load preferences');
      }
    } catch {
      setError('Network error loading preferences');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggle = useCallback(async (eventType: string, channel: string) => {
    const current = prefs[eventType]?.[channel] ?? true;
    const updated = { ...prefs };
    if (!updated[eventType]) updated[eventType] = {};
    updated[eventType][channel] = !current;
    setPrefs(updated);
    setSaving(true);
    try {
      await fetch('/api/v1/notifications/preferences', {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferences: [{ event_type: eventType, channel, enabled: !current }],
        }),
      });
    } catch {
      // revert on failure
      setPrefs(prefs);
    }
    setSaving(false);
  }, [prefs]);

  if (loading) {
    return (
      <div className="notif-prefs">
        <div className="notif-prefs-header"><h2>Notification Preferences</h2></div>
        <p className="notif-prefs-loading">Loading preferences…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="notif-prefs">
        <div className="notif-prefs-header"><h2>Notification Preferences</h2></div>
        <p className="notif-prefs-error" role="alert">{error}</p>
        <button className="notif-prefs-retry" onClick={load}>Retry</button>
      </div>
    );
  }

  const displayChannels = channels.length > 0
    ? CHANNEL_ORDER.filter(c => channels.includes(c))
    : CHANNEL_ORDER;

  return (
    <div className="notif-prefs">
      <div className="notif-prefs-header">
        <h2><IconBell size={18} /> Notification Preferences</h2>
        {saving && <span className="notif-prefs-saving">Saving…</span>}
      </div>
      <p className="notif-prefs-subtitle">
        Choose how SHUNYA notifies you for each type of event.
      </p>

      <div className="notif-prefs-table">
        <div className="notif-prefs-row notif-prefs-head">
          <span className="notif-prefs-cell notif-prefs-event">Event Type</span>
          {displayChannels.map(ch => (
            <span key={ch} className="notif-prefs-cell notif-prefs-channel" title={CHANNEL_LABELS[ch]?.label || ch}>
              {CHANNEL_LABELS[ch]?.icon || ch}
            </span>
          ))}
        </div>

        {eventTypes.map(et => (
          <div key={et} className="notif-prefs-row notif-prefs-body-row">
            <span className="notif-prefs-cell notif-prefs-event">{et.replace(/\./g, ' · ')}</span>
            {displayChannels.map(ch => {
              const enabled = prefs[et]?.[ch] ?? true;
              return (
                <span key={ch} className="notif-prefs-cell notif-prefs-toggle-cell">
                  <button
                    className={`notif-prefs-toggle ${enabled ? 'notif-prefs-on' : 'notif-prefs-off'}`}
                    onClick={() => toggle(et, ch)}
                    aria-label={`${et} via ${ch}: ${enabled ? 'enabled' : 'disabled'}`}
                    title={enabled ? 'Click to disable' : 'Click to enable'}
                  >
                    {enabled ? <IconBell size={14} /> : <IconBellOff size={14} />}
                  </button>
                </span>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}