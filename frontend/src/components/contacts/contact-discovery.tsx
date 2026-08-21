/** D-05 — Contact Discovery View
 *
 * Business contact / referral discovery.
 * Connects to the people API at /api/v1/people/.
 * Provides searchable member browsing with role/status filtering.
 */

import { useState, useEffect, type FC } from 'react';

interface ContactMember {
  id: number;
  name: string;
  email: string;
  role: string;
  designation: string;
  is_active: boolean;
  joined_at: string | null;
}

interface ApiData {
  total: number;
  members: ContactMember[];
}

async function api<T>(path: string, opts?: RequestInit) {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    return r.json() as Promise<{ success: boolean; data?: T; error?: string }>;
  } catch { return { success: false, error: 'Network error' }; }
}

export const ContactDiscovery: FC = () => {
  const [members, setMembers] = useState<ContactMember[]>([]);
  const [filtered, setFiltered] = useState<ContactMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');

  const loadMembers = async () => {
    setLoading(true); setError('');
    const r = await api<ApiData>('/api/v1/people/members');
    if (r.success) {
      const list = r.data?.members ?? [];
      setMembers(list);
      setFiltered(list);
    } else {
      setError(r.error || 'Failed to load contacts');
    }
    setLoading(false);
  };

  useEffect(() => { loadMembers(); }, []);

  // Apply filters whenever filter criteria change
  useEffect(() => {
    let result = [...members];
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(m =>
        m.name.toLowerCase().includes(q) ||
        m.email.toLowerCase().includes(q) ||
        (m.designation || '').toLowerCase().includes(q)
      );
    }
    if (roleFilter !== 'all') {
      result = result.filter(m => m.role === roleFilter);
    }
    if (statusFilter === 'active') {
      result = result.filter(m => m.is_active);
    } else if (statusFilter === 'inactive') {
      result = result.filter(m => !m.is_active);
    }
    setFiltered(result);
  }, [search, roleFilter, statusFilter, members]);

  const uniqueRoles = [...new Set(members.map(m => m.role))].sort();

  return (
    <div className="wksp-contact-discovery">
      <div className="wksp-cd-header">
        <h3>Contact Discovery</h3>
        <span className="wksp-muted">{filtered.length} of {members.length} contacts</span>
      </div>

      {error && <div className="wksp-cd-error">{error}</div>}

      <div className="wksp-cd-filters">
        <input
          type="text"
          placeholder="Search name, email, designation…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="wksp-input wksp-cd-search"
        />
        <div className="wksp-cd-filter-group">
          <label className="wksp-cd-filter-label">
            Role:
            <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)} className="wksp-input-sm">
              <option value="all">All Roles</option>
              {uniqueRoles.map(r => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </label>
          <label className="wksp-cd-filter-label">
            Status:
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value as typeof statusFilter)} className="wksp-input-sm">
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </label>
        </div>
      </div>

      {loading && <div className="wksp-loading-text">Loading contacts…</div>}

      {!loading && !error && filtered.length === 0 && (
        <div className="wksp-cd-empty">
          <p>No contacts match your filters.</p>
          {search && <p className="wksp-muted">Try a different search term.</p>}
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="wksp-cd-grid">
          {filtered.slice(0, 100).map(m => (
            <div key={m.id} className={`wksp-cd-card ${!m.is_active ? 'wksp-cd-inactive' : ''}`}>
              <div className="wksp-cd-card-name">{m.name}</div>
              <div className="wksp-cd-card-email">{m.email}</div>
              <div className="wksp-cd-card-meta">
                <span className="wksp-cd-role">{m.role}</span>
                {m.designation && <span className="wksp-muted">{m.designation}</span>}
                <span className={`wksp-cd-status ${m.is_active ? 'wksp-cd-active' : 'wksp-cd-inactive-tag'}`}>
                  {m.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
.wksp-contact-discovery { padding: var(--shunya-spacing-md); }
.wksp-cd-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.wksp-cd-header h3 { font-size: 14px; font-weight: 600; color: var(--shunya-text); margin: 0; }
.wksp-cd-filters { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.wksp-cd-search { flex: 1; min-width: 200px; padding: 6px 8px; background: var(--shunya-surface-3); border: 1px solid var(--shunya-surface-1); border-radius: 4px; color: var(--shunya-text); font-size: 12px; }
.wksp-cd-filter-group { display: flex; gap: 8px; align-items: center; }
.wksp-cd-filter-label { font-size: 12px; color: var(--shunya-text-secondary); display: flex; align-items: center; gap: 4px; }
.wksp-cd-filter-label select { padding: 4px; background: var(--shunya-surface-3); border: 1px solid var(--shunya-surface-1); border-radius: 3px; color: var(--shunya-text); font-size: 12px; }
.wksp-cd-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 8px; }
.wksp-cd-card { background: var(--shunya-surface-2); border: 1px solid var(--shunya-surface-1); border-radius: 6px; padding: 10px; transition: border-color 0.15s; }
.wksp-cd-card:hover { border-color: var(--shunya-color-primary, #555); }
.wksp-cd-card.wksp-cd-inactive { opacity: 0.5; }
.wksp-cd-card-name { font-weight: 600; font-size: 13px; color: var(--shunya-text); margin-bottom: 2px; }
.wksp-cd-card-email { font-size: 11px; color: var(--shunya-text-secondary); margin-bottom: 6px; }
.wksp-cd-card-meta { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; font-size: 11px; }
.wksp-cd-role { background: var(--shunya-surface-3); padding: 1px 6px; border-radius: 3px; color: var(--shunya-text); }
.wksp-cd-status { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 500; }
.wksp-cd-active { background: rgba(34,197,94,0.15); color: #22c55e; }
.wksp-cd-inactive-tag { background: rgba(239,68,68,0.1); color: #f88; }
.wksp-cd-empty { text-align: center; padding: 40px 20px; color: var(--shunya-text-secondary); }
.wksp-cd-error { color: #f88; padding: 8px; background: rgba(239,68,68,0.1); border-radius: 4px; margin-bottom: 8px; }
.wksp-cd-error { color: #f88; padding: 8px; background: rgba(239,68,68,0.1); border-radius: 4px; margin-bottom: 8px; }
.wksp-loading-text { text-align: center; padding: 20px; color: var(--shunya-text-secondary); }
.wksp-input { padding: 6px 8px; background: var(--shunya-surface-3); border: 1px solid var(--shunya-surface-1); border-radius: 4px; color: var(--shunya-text); font-size: 12px; }
      `}</style>
    </div>
  );
};