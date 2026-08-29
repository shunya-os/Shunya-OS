/** PeoplePersonsPanel — Displays canonical Person records from /api/v1/people/persons */

import { useState, useEffect, type FC } from 'react';

interface PersonData {
  id: number;
  tenant_id: number | null;
  canonical_name: string;
  preferred_name: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  team_member: {
    id: number;
    email: string;
    role: string;
    is_active: boolean;
  } | null;
}

async function api<T>(path: string, opts?: RequestInit) {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    return r.json() as Promise<{ success: boolean; data?: T; error?: string }>;
  } catch { return { success: false, error: 'Network error' }; }
}

export const PeoplePersonsPanel: FC = () => {
  const [persons, setPersons] = useState<PersonData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    const res = await api<PersonData[]>('/api/v1/people/persons');
    if (res.success) {
      setPersons(res.data || []);
    } else {
      setError(res.error || 'Failed to load persons');
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="wksp-people-persons">
      <div className="wksp-people-header">
        <h2>People</h2>
        <span className="wksp-badge">{persons.length} persons</span>
      </div>

      {loading && <div className="wksp-loading-text">Loading…</div>}
      {error && <div className="wksp-error-message">{error}</div>}

      {!loading && !error && persons.length === 0 && (
        <p className="wksp-muted">No Person records found for this tenant.</p>
      )}

      {!loading && persons.length > 0 && (
        <div className="wksp-person-list">
          {persons.map(p => (
            <div key={p.id} className="wksp-person-card">
              <div className="wksp-person-avatar">
                {(p.preferred_name || p.canonical_name)[0].toUpperCase()}
              </div>
              <div className="wksp-person-info">
                <div className="wksp-person-name">
                  {p.preferred_name || p.canonical_name.split('@')[0]}
                </div>
                <div className="wksp-person-email">{p.canonical_name}</div>
                <div className="wksp-person-meta">
                  <span className="wksp-tag">status: {p.status}</span>
                  {p.team_member && (
                    <>
                      <span className="wksp-tag">role: {p.team_member.role}</span>
                      <span className={`wksp-tag ${p.team_member.is_active ? 'wksp-tag-active' : 'wksp-tag-inactive'}`}>
                        {p.team_member.is_active ? 'active' : 'inactive'}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
.wksp-people-persons { padding: var(--shunya-spacing-md); }
.wksp-people-header { display: flex; align-items: center; gap: var(--shunya-spacing-sm); margin-bottom: var(--shunya-spacing-md); }
.wksp-badge { background: var(--shunya-surface-2, #2a2a3a); color: var(--shunya-text-secondary, #888); padding: 2px 10px; border-radius: 10px; font-size: 12px; }
.wksp-person-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: var(--shunya-spacing-sm); }
.wksp-person-card { display: flex; gap: var(--shunya-spacing-sm); padding: var(--shunya-spacing-sm); background: var(--shunya-surface-1, #1e1e2e); border: 1px solid var(--shunya-surface-2, #2a2a3a); border-radius: var(--shunya-radius-md, 8px); }
.wksp-person-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--shunya-color-primary, #555); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 16px; flex-shrink: 0; }
.wksp-person-info { flex: 1; min-width: 0; }
.wksp-person-name { font-weight: 500; color: var(--shunya-text, #e0e0e0); }
.wksp-person-email { font-size: 12px; color: var(--shunya-text-secondary, #888); }
.wksp-person-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
.wksp-tag { font-size: 11px; background: var(--shunya-surface-2, #2a2a3a); color: var(--shunya-text-secondary, #888); padding: 1px 6px; border-radius: 3px; }
.wksp-tag-active { color: #4caf50; }
.wksp-tag-inactive { color: #f44336; }
.wksp-muted { color: var(--shunya-text-secondary, #888); font-style: italic; }
.wksp-loading-text, .wksp-error-message { color: var(--shunya-text-secondary, #888); padding: var(--shunya-spacing-md); }
      `}</style>
    </div>
  );
};