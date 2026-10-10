/**
 * Active Sessions — list active sessions with terminate buttons.
 *
 * GET  /api/v1/sessions              → list active sessions
 * DELETE /api/v1/sessions/:id        → terminate one session
 * DELETE /api/v1/sessions            → terminate all other sessions
 */
import { useState, useEffect, useCallback } from 'react';
import { IconDeviceLaptop, IconTrash, IconX, IconRefresh } from '@tabler/icons-react';

interface Session {
  id: string;
  identity_id: string;
  is_current: boolean;
  user_agent: string;
  ip_address: string;
  created_at: string;
  last_active_at: string;
}

export function ActiveSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const r = await fetch('/api/v1/sessions', { credentials: 'include' });
      const d = await r.json();
      if (d.success) {
        setSessions(d.sessions || []);
      } else {
        setError(d.error || 'Failed to load sessions');
      }
    } catch {
      setError('Network error loading sessions');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const terminate = useCallback(async (sessionId: string) => {
    setError('');
    setMessage('');
    try {
      const r = await fetch(`/api/v1/sessions/${sessionId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      const d = await r.json();
      if (d.success) {
        setMessage(d.message || 'Session terminated');
        setSessions(prev => prev.filter(s => s.id !== sessionId));
      } else {
        setError(d.error || 'Failed to terminate session');
      }
    } catch {
      setError('Network error');
    }
  }, []);

  const terminateAllOthers = useCallback(async () => {
    setError('');
    setMessage('');
    try {
      const r = await fetch('/api/v1/sessions', {
        method: 'DELETE',
        credentials: 'include',
      });
      const d = await r.json();
      if (d.success) {
        setMessage(d.message || 'Other sessions terminated');
        setSessions(prev => prev.filter(s => s.is_current));
      } else {
        setError(d.error || 'Failed to terminate sessions');
      }
    } catch {
      setError('Network error');
    }
  }, []);

  const formatAgent = (ua: string) => {
    if (!ua) return 'Unknown device';
    if (ua.includes('Chrome')) return 'Chrome';
    if (ua.includes('Firefox')) return 'Firefox';
    if (ua.includes('Safari') && !ua.includes('Chrome')) return 'Safari';
    if (ua.includes('Edge')) return 'Edge';
    return ua.slice(0, 40);
  };

  if (loading) {
    return (
      <div className="active-sessions">
        <div className="active-sessions-header"><h2><IconDeviceLaptop size={18} /> Active Sessions</h2></div>
        <p className="active-sessions-loading">Loading sessions…</p>
      </div>
    );
  }

  return (
    <div className="active-sessions">
      <div className="active-sessions-header">
        <h2><IconDeviceLaptop size={18} /> Active Sessions</h2>
        <button className="active-sessions-refresh" onClick={load} title="Refresh sessions">
          <IconRefresh size={16} />
        </button>
      </div>

      {error && <p className="active-sessions-error" role="alert">{error}</p>}
      {message && <p className="active-sessions-message" role="status">{message}</p>}

      {sessions.length > 1 && (
        <button className="active-sessions-terminate-all" onClick={terminateAllOthers}>
          <IconX size={14} /> Terminate all other sessions
        </button>
      )}

      <div className="active-sessions-list">
        {sessions.map(s => (
          <div key={s.id} className={`active-sessions-item ${s.is_current ? 'active-sessions-current' : ''}`}>
            <div className="active-sessions-item-icon">
              <IconDeviceLaptop size={20} />
            </div>
            <div className="active-sessions-item-info">
              <span className="active-sessions-item-agent">
                {formatAgent(s.user_agent)}
                {s.is_current && <span className="active-sessions-badge">Current</span>}
              </span>
              <span className="active-sessions-item-meta">
                IP: {s.ip_address || 'Unknown'} · Created {s.created_at ? new Date(s.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
            {!s.is_current && (
              <button
                className="active-sessions-item-terminate"
                onClick={() => terminate(s.id)}
                title="Terminate this session"
                aria-label="Terminate session"
              >
                <IconTrash size={16} />
              </button>
            )}
          </div>
        ))}
        {sessions.length === 0 && (
          <p className="active-sessions-empty">No active sessions found.</p>
        )}
      </div>
    </div>
  );
}