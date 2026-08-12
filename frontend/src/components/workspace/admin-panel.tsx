/** FDA22 — Admin Panel: Roles, Permissions, Service Accounts, Delegations, Policies */

import { useState, useEffect, type FC } from 'react';

interface ApiResponse<T> { success: boolean; data?: T; error?: string }

async function api<T>(path: string, opts?: RequestInit): Promise<ApiResponse<T>> {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    return r.json();
  } catch { return { success: false, error: 'Network error' }; }
}

type Tab = 'roles' | 'permissions' | 'service-accounts' | 'delegations' | 'policies';

export const AdminPanel: FC = () => {
  const [tab, setTab] = useState<Tab>('roles');
  const [roles, setRoles] = useState<any[]>([]);
  const [permissions, setPermissions] = useState<any[]>([]);
  const [sas, setSas] = useState<any[]>([]);
  const [delegations, setDelegations] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saName, setSaName] = useState('');
  const [saPerms, setSaPerms] = useState('connector.view');
  const [creating, setCreating] = useState(false);
  const [token, setToken] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    const [r, p, s, d, pol] = await Promise.all([
      api<any[]>('/api/v1/admin/roles'),
      api<any[]>('/api/v1/admin/permissions'),
      api<any[]>('/api/v1/admin/service-accounts'),
      api<any[]>('/api/v1/admin/delegations'),
      api<any[]>('/api/v1/admin/policies'),
    ]);
    if (r.success) setRoles(r.data || []);
    if (p.success) setPermissions(p.data || []);
    if (s.success) setSas(s.data || []);
    if (d.success) setDelegations(d.data || []);
    if (pol.success) setPolicies(pol.data || []);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const createSA = async () => {
    setCreating(true); setToken('');
    const r = await api<any>('/api/v1/admin/service-accounts', {
      method: 'POST', body: JSON.stringify({ name: saName, permissions: saPerms.split(',').map(s => s.trim()) }),
    });
    if (r.success && r.data?.token) setToken(r.data.token);
    setCreating(false); load();
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'roles', label: 'Roles' },
    { key: 'permissions', label: 'Permissions' },
    { key: 'service-accounts', label: 'Service Accts' },
    { key: 'delegations', label: 'Delegations' },
    { key: 'policies', label: 'Policies' },
  ];

  return (
    <div className="wksp-admin">
      <div className="wksp-admin-tabs">
        {tabs.map(t => (
          <button key={t.key} className={`wksp-admin-tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>{t.label}</button>
        ))}
      </div>

      {loading && <div className="wksp-loading-text">Loading…</div>}
      {error && <div className="wksp-error-message">{error}</div>}

      {!loading && tab === 'roles' && (
        <div className="wksp-admin-section">
          <h3>Roles</h3>
          {roles.map(r => (
            <div key={r.id} className="wksp-admin-row"><strong>{r.display_name}</strong> <span className="wksp-muted">({r.name})</span> — {r.permissions?.length || 0} permissions</div>
          ))}
        </div>
      )}

      {!loading && tab === 'permissions' && (
        <div className="wksp-admin-section">
          <h3>All Permissions ({permissions.length})</h3>
          <div className="wksp-perm-grid">
            {permissions.map(p => (
              <div key={p.key} className="wksp-perm-item"><code>{p.key}</code><span className="wksp-muted">{p.description}</span></div>
            ))}
          </div>
        </div>
      )}

      {!loading && tab === 'service-accounts' && (
        <div className="wksp-admin-section">
          <h3>Service Accounts</h3>
          <div className="wksp-admin-form">
            <input value={saName} onChange={e => setSaName(e.target.value)} placeholder="Name" className="wksp-input" />
            <input value={saPerms} onChange={e => setSaPerms(e.target.value)} placeholder="permission1,permission2" className="wksp-input" />
            <button onClick={createSA} disabled={creating || !saName} className="wksp-btn">Create</button>
          </div>
          {token && <div className="wksp-token-display">Token: <code>{token}</code> <span className="wksp-muted">(copy now — will not be shown again)</span></div>}
          {sas.map(sa => (
            <div key={sa.id} className="wksp-admin-row"><strong>{sa.name}</strong> — {sa.is_active ? 'Active' : 'Inactive'} <span className="wksp-muted">({sa.permissions?.length || 0} perms)</span></div>
          ))}
        </div>
      )}

      {!loading && tab === 'delegations' && (
        <div className="wksp-admin-section">
          <h3>Delegations</h3>
          {delegations.map(d => (
            <div key={d.id} className="wksp-admin-row"><strong>#{d.id}</strong> — {d.status} <span className="wksp-muted">({d.permission_keys?.length || 0} permissions)</span></div>
          ))}
          {delegations.length === 0 && <p className="wksp-muted">No delegations found.</p>}
        </div>
      )}

      {!loading && tab === 'policies' && (
        <div className="wksp-admin-section">
          <h3>Tenant Policies</h3>
          {policies.map(p => (
            <div key={p.id} className="wksp-admin-row"><strong>{p.policy_key}</strong> = <code>{p.policy_value}</code> <span className="wksp-muted">({p.policy_type})</span></div>
          ))}
          {policies.length === 0 && <p className="wksp-muted">No policies configured.</p>}
        </div>
      )}

      <style>{`
.wksp-admin { padding: var(--shunya-spacing-md); }
.wksp-admin-tabs { display: flex; gap: 4px; margin-bottom: var(--shunya-spacing-md); flex-wrap: wrap; }
.wksp-admin-tab { padding: 6px 14px; background: var(--shunya-surface-2); border: 1px solid var(--shunya-surface-1); border-radius: 6px; color: var(--shunya-text-secondary); cursor: pointer; font-size: 13px; }
.wksp-admin-tab.active { background: var(--shunya-surface-3); color: var(--shunya-text); border-color: var(--shunya-color-primary); }
.wksp-admin-section h3 { font-size: 14px; font-weight: 600; margin-bottom: 8px; color: var(--shunya-text); }
.wksp-admin-row { padding: 6px 0; border-bottom: 1px solid var(--shunya-surface-1); font-size: 13px; color: var(--shunya-text); }
.wksp-muted { color: var(--shunya-text-secondary, #888); font-size: 12px; margin-left: 6px; }
.wksp-perm-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 6px; }
.wksp-perm-item { display: flex; flex-direction: column; gap: 2px; padding: 6px; background: var(--shunya-surface-2); border-radius: 4px; }
.wksp-perm-item code { font-size: 11px; color: var(--shunya-color-primary, #555); }
.wksp-admin-form { display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap; }
.wksp-input { padding: 6px 10px; background: var(--shunya-surface-3); border: 1px solid var(--shunya-surface-1); border-radius: 4px; color: var(--shunya-text); font-size: 13px; flex: 1; min-width: 150px; }
.wksp-btn { padding: 6px 14px; background: var(--shunya-color-primary, #555); border: none; border-radius: 4px; color: #fff; cursor: pointer; font-size: 13px; }
.wksp-btn:disabled { opacity: 0.5; }
.wksp-token-display { padding: 8px; background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); border-radius: 4px; margin-bottom: 8px; font-size: 12px; }
.wksp-loading-text { text-align: center; padding: 40px; color: var(--shunya-text-secondary); }
.wksp-error-message { color: #f88; padding: 10px; }
      `}</style>
    </div>
  );
};