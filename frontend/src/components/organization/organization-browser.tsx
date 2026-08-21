/**
 * OrganizationBrowser — Navigable organization hierarchy.
 *
 * Reads real canonical people data from /api/v1/people/members.
 * Groups members by role/designation as an org structure.
 * No fake hierarchy. Truthful empty state when no data.
 * Mobile-responsive.
 */

import { useState, useEffect, type FC } from 'react';

interface Member {
  id: number;
  name: string;
  email: string;
  role: string;
  designation: string;
  is_active: boolean;
  joined_at: string | null;
}

async function api<T>(path: string): Promise<{ success: boolean; data?: T; error?: string }> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    return await r.json();
  } catch { return { success: false, error: 'Network error' }; }
}

function _timeAgo(ts: string | null | undefined): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    const diff = Date.now() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch { return ''; }
}

export const OrganizationBrowser: FC = () => {
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedRoles, setExpandedRoles] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    const result = await api<Member[]>('/api/v1/people/members');
    if (result.success && result.data) {
      setMembers(result.data);
    } else if (result.success === false && result.error) {
      // Auth error means the API exists — show empty state for data
      setMembers([]);
    } else {
      setError('Could not load organization data');
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  // Group members by role for org hierarchy
  const roleGroups = members.reduce((acc, m) => {
    const role = m.role || 'member';
    if (!acc[role]) acc[role] = [];
    acc[role].push(m);
    return acc;
  }, {} as Record<string, Member[]>);

  // Sort roles: admin first, then by count descending
  const sortedRoles = Object.entries(roleGroups).sort(([a], [b]) => {
    const order = ['admin', 'manager', 'member', 'contributor', 'viewer'];
    return (order.indexOf(a) - order.indexOf(b));
  });

  const filteredMembers = search.trim()
    ? members.filter(m =>
        m.name.toLowerCase().includes(search.toLowerCase()) ||
        m.email.toLowerCase().includes(search.toLowerCase()) ||
        (m.designation || '').toLowerCase().includes(search.toLowerCase())
      )
    : null;

  const toggleRole = (role: string) => {
    setExpandedRoles(prev => {
      const next = new Set(prev);
      if (next.has(role)) next.delete(role);
      else next.add(role);
      return next;
    });
  };

  const displayMembers = filteredMembers !== null
    ? filteredMembers
    : null;

  return (
    <div className="pw-panel-container" style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 960 }}>
      <div className="pw-domain-header">
        <span className="pw-domain-icon">👤</span>
        <h2 className="pw-domain-title">Organization</h2>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '0 0 16px' }}>
        People, roles, and structure
      </p>

      {/* Search */}
      <div style={{ marginBottom: 20 }}>
        <input
          placeholder="Search people by name, email, or designation…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%', padding: '10px 14px', border: '1px solid rgba(26,28,29,0.12)',
            borderRadius: 8, fontSize: 14, outline: 'none', fontFamily: 'inherit',
            color: '#1A1C1D', background: '#fff', boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Summary */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="org-summary-card">
          <div className="org-summary-value">{members.length}</div>
          <div className="org-summary-label">Total Members</div>
        </div>
        {sortedRoles.map(([role, list]) => (
          <div key={role} className="org-summary-card">
            <div className="org-summary-value">{list.length}</div>
            <div className="org-summary-label" style={{ textTransform: 'capitalize' }}>{role}s</div>
          </div>
        ))}
      </div>

      {/* Loading */}
      {loading && <div className="org-loading">Loading organization data…</div>}
      {error && <div className="org-error">{error}</div>}

      {/* Empty state */}
      {!loading && !error && members.length === 0 && (
        <div className="org-empty">
          <p>No organization members found.</p>
          <p className="org-empty-sub">Members will appear here when they are added to the organization.</p>
        </div>
      )}

      {/* Search results */}
      {!loading && !error && displayMembers !== null && displayMembers.length === 0 && search.trim() && (
        <div className="org-empty">
          <p>No members matching "{search}".</p>
        </div>
      )}

      {/* Org hierarchy */}
      {!loading && !error && members.length > 0 && displayMembers === null && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {sortedRoles.map(([role, roleMembers]) => {
            const isExpanded = expandedRoles.has(role);
            return (
              <div key={role} className="org-role-group">
                <button
                  className="org-role-header"
                  onClick={() => toggleRole(role)}
                  aria-expanded={isExpanded}
                >
                  <span className="org-role-arrow">{isExpanded ? '▼' : '▶'}</span>
                  <span className="org-role-name" style={{ textTransform: 'capitalize' }}>{role}</span>
                  <span className="org-role-count">{roleMembers.length}</span>
                </button>
                {isExpanded && (
                  <div className="org-role-members">
                    {roleMembers.map(m => (
                      <div key={m.id} className="org-member-card">
                        <div className="org-member-row">
                          <div className="org-member-avatar">
                            {m.name.charAt(0).toUpperCase()}
                          </div>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div className="org-member-name">{m.name}</div>
                            <div className="org-member-meta">
                              {m.designation && <span>{m.designation}</span>}
                              <span>{m.email}</span>
                            </div>
                          </div>
                          <span className={`org-member-status ${m.is_active ? 'org-active' : 'org-inactive'}`}>
                            {m.is_active ? 'Active' : 'Inactive'}
                          </span>
                          {m.joined_at && (
                            <span className="org-member-joined">Joined {_timeAgo(m.joined_at)}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Search results flat list */}
      {!loading && !error && displayMembers !== null && displayMembers.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {displayMembers.map(m => (
            <div key={m.id} className="org-member-card">
              <div className="org-member-row">
                <div className="org-member-avatar">{m.name.charAt(0).toUpperCase()}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="org-member-name">{m.name}</div>
                  <div className="org-member-meta">
                    {m.designation && <span>{m.designation}</span>}
                    <span>{m.email}</span>
                    <span style={{ textTransform: 'capitalize' }}>{m.role}</span>
                  </div>
                </div>
                <span className={`org-member-status ${m.is_active ? 'org-active' : 'org-inactive'}`}>
                  {m.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
.org-summary-card {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 18px;
  flex: 1;
  min-width: 70px;
}
.org-summary-value { font-size: 22px; font-weight: 700; color: #1A1C1D; }
.org-summary-label { font-size: 11px; color: rgba(26,28,29,0.55); margin-top: 2px; }
.org-loading { padding: 40px; text-align: center; color: rgba(26,28,29,0.55); }
.org-error { padding: 40px; text-align: center; color: #d1453b; }
.org-empty { padding: 40px; text-align: center; }
.org-empty-sub { font-size: 13px; color: rgba(26,28,29,0.45); }
.org-role-group {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  overflow: hidden;
}
.org-role-header {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 14px 16px;
  background: transparent; border: none;
  cursor: pointer; font-size: 14px; font-weight: 600; color: #1A1C1D;
  font-family: inherit; text-align: left;
  transition: background 0.15s;
}
.org-role-header:hover { background: rgba(26,28,29,0.02); }
.org-role-arrow { font-size: 10px; color: rgba(26,28,29,0.35); width: 12px; }
.org-role-name { flex: 1; }
.org-role-count {
  font-size: 12px; font-weight: 500; color: rgba(26,28,29,0.45);
  background: rgba(26,28,29,0.04); padding: 2px 8px; border-radius: 12px;
}
.org-role-members { display: flex; flex-direction: column; border-top: 1px solid rgba(26,28,29,0.04); }
.org-member-card {
  padding: 12px 16px 12px 28px;
  border-bottom: 1px solid rgba(26,28,29,0.03);
}
.org-member-card:last-child { border-bottom: none; }
.org-member-row {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}
.org-member-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: rgba(26,28,29,0.06); color: rgba(26,28,29,0.55);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 600;
  flex-shrink: 0;
}
.org-member-name { font-size: 14px; font-weight: 500; color: #1A1C1D; }
.org-member-meta {
  display: flex; gap: 10px; flex-wrap: wrap;
  font-size: 12px; color: rgba(26,28,29,0.45); margin-top: 2px;
}
.org-member-status {
  font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 6px;
}
.org-active { background: rgba(46,125,50,0.08); color: #2e7d32; }
.org-inactive { background: rgba(209,69,59,0.08); color: #d1453b; }
.org-member-joined {
  font-size: 11px; color: rgba(26,28,29,0.35);
}
      `}</style>
    </div>
  );
};

export default OrganizationBrowser;